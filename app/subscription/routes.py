"""
Subscription and Payment Routes
Phase 11: Payment & Subscriptions
"""

from flask import render_template, request, redirect, url_for, jsonify, flash, session
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
from . import subscription_bp
from .. import db
from ..payment_models import SubscriptionPlan, Payment, UserSubscription
from ..services.payment_service import SubscriptionService, UsageLimitService, PaymentService
from ..services.stripe_service import StripeService
from ..services.upgrade_service import UpgradeService


@subscription_bp.route('/plans')
def plans():
    """Subscription plans page"""
    # Get all active plans
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_nok).all()
    
    # Get user's current plan and usage stats
    current_plan = 'free'
    usage_stats = None
    subscription_stats = None
    
    if current_user.is_authenticated:
        current_plan = SubscriptionService.get_user_plan(current_user.id)
        usage_stats = UsageLimitService.get_usage_stats(current_user.id)
        subscription_stats = SubscriptionService.get_subscription_stats(current_user.id)
    
    return render_template('subscription/plans.html',
                         plans=plans,
                         current_plan=current_plan,
                         usage_stats=usage_stats,
                         subscription_stats=subscription_stats)


@subscription_bp.route('/upgrade/<plan_name>')
@login_required
def upgrade(plan_name):
    """Upgrade to a specific plan with smart upgrade logic"""
    plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan:
        flash('Plan ikke funnet', 'error')
        return redirect(url_for('subscription.plans'))
    
    # Check if user can upgrade to this plan
    can_upgrade, message = UpgradeService.can_upgrade_to(current_user.id, plan_name)
    if not can_upgrade:
        flash(message, 'info')
        return redirect(url_for('subscription.manage'))
    
    # Calculate upgrade cost with proration
    try:
        upgrade_info = UpgradeService.calculate_upgrade_cost(current_user.id, plan_name)
        return render_template('subscription/upgrade.html', 
                             plan=plan, 
                             upgrade_info=upgrade_info)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('subscription.plans'))


@subscription_bp.route('/checkout/<plan_name>', methods=['GET', 'POST'])
@login_required
def checkout(plan_name):
    """Checkout page for plan upgrade with proration support"""
    plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan:
        flash('Plan ikke funnet', 'error')
        return redirect(url_for('subscription.plans'))
    
    # Check if this is an upgrade and calculate cost
    try:
        upgrade_info = UpgradeService.calculate_upgrade_cost(current_user.id, plan_name)
        is_upgrade = True
    except ValueError:
        # Not an upgrade, use regular pricing
        is_upgrade = False
        upgrade_info = {
            'upgrade_cost': float(plan.price_nok),
            'target_plan': plan_name,
            'target_plan_display': plan.display_name,
            'proration_applied': False
        }
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'stripe')
        
        try:
            if payment_method == 'stripe':
                # Create payment intent with correct amount
                if is_upgrade:
                    # Use upgrade cost for upgrades
                    payment_data = PaymentService.create_payment_intent(
                        current_user.id, plan_name
                    )
                    # Update payment amount to upgrade cost
                    payment = Payment.query.get(payment_data['payment_id'])
                    payment.amount_nok = Decimal(str(upgrade_info['upgrade_cost']))
                    payment.description = f"Upgrade to {upgrade_info['target_plan_display']}"
                    if upgrade_info['proration_applied']:
                        payment.description += f" (prorated for {upgrade_info['remaining_days']} days remaining)"
                    db.session.commit()
                else:
                    # Regular new subscription
                    payment_data = PaymentService.create_payment_intent(
                        current_user.id, plan_name
                    )
                
                # Create Stripe Checkout session
                stripe_service = StripeService()
                success_url = url_for('subscription.payment_success', _external=True)
                cancel_url = url_for('subscription.checkout', plan_name=plan_name, _external=True)
                
                checkout_data = stripe_service.create_checkout_session(
                    current_user.id,
                    plan_name,
                    success_url,
                    cancel_url
                )
                
                # Redirect to Stripe Checkout
                return redirect(checkout_data['checkout_url'])
                
            else:
                # Handle other payment methods (Vipps, etc.)
                flash('Denne betalingsmetoden er ikke tilgjengelig ennå', 'info')
                
        except Exception as e:
            flash(f'Feil ved opprettelse av betaling: {str(e)}', 'error')
    
    return render_template('subscription/checkout.html', 
                         plan=plan, 
                         upgrade_info=upgrade_info, 
                         is_upgrade=is_upgrade)


@subscription_bp.route('/payment/success')
@login_required
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    payment_id = request.args.get('payment_id')
    
    if session_id:
        try:
            # Confirm Stripe payment
            stripe_service = StripeService()
            success = stripe_service.confirm_payment(session_id=session_id)
            
            if success:
                flash('Gratulerer! Betalingen din er bekreftet og abonnementet er aktivert!', 'success')
                return redirect(url_for('subscription.manage'))
            else:
                flash('Det oppstod en feil ved bekreftelse av betalingen', 'error')
                return redirect(url_for('subscription.plans'))
                
        except Exception as e:
            flash(f'Feil ved behandling av betaling: {str(e)}', 'error')
            return redirect(url_for('subscription.plans'))
    
    # Fallback for other payment methods or missing session_id
    flash('Ingen betalingsinformasjon funnet', 'error')
    return redirect(url_for('subscription.plans'))


@subscription_bp.route('/manage')
@login_required
def manage():
    """Subscription management page"""
    subscription_stats = SubscriptionService.get_subscription_stats(current_user.id)
    usage_stats = UsageLimitService.get_usage_stats(current_user.id)
    payment_history = PaymentService.get_user_payment_history(current_user.id)
    
    # Get available upgrade options
    upgrade_options = UpgradeService.get_upgrade_options(current_user.id)
    
    return render_template('subscription/manage.html',
                         subscription_stats=subscription_stats,
                         usage_stats=usage_stats,
                         payment_history=payment_history,
                         upgrade_options=upgrade_options)


@subscription_bp.route('/cancel', methods=['POST'])
@login_required
def cancel():
    """Cancel subscription"""
    reason = request.form.get('reason', 'User requested cancellation')
    
    if SubscriptionService.cancel_subscription(current_user.id, reason):
        flash('Abonnementet ditt har blitt kansellert', 'success')
    else:
        flash('Kunne ikke kansellere abonnement', 'error')
    
    return redirect(url_for('subscription.manage'))


@subscription_bp.route('/api/check-limits')
@login_required
def api_check_limits():
    """API endpoint to check user limits"""
    quiz_type = request.args.get('type', 'practice')
    
    can_take, message = SubscriptionService.can_user_take_quiz(current_user.id, quiz_type)
    usage_stats = UsageLimitService.get_usage_stats(current_user.id)
    
    return jsonify({
        'can_take': can_take,
        'message': message,
        'usage_stats': usage_stats,
        'current_plan': SubscriptionService.get_user_plan(current_user.id)
    })


@subscription_bp.route('/api/plan-options')
@login_required
def api_get_plan_options():
    """API endpoint to get plan options with upgrade pricing"""
    try:
        current_plan = SubscriptionService.get_user_plan(current_user.id)
        subscription_stats = SubscriptionService.get_subscription_stats(current_user.id)
        all_plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_nok).all()
        
        plan_options = []
        
        for plan in all_plans:
            plan_data = {
                'name': plan.name,
                'display_name': plan.display_name,
                'price': int(plan.price_nok),
                'description': plan.description,
                'features': [],
                'can_upgrade': False,
                'is_downgrade': False,
                'upgrade_info': None
            }
            
            # Add plan-specific features
            if plan.name == 'free':
                plan_data['features'] = [
                    '10 quiz per dag',
                    '2 prøveeksamener per uke', 
                    'Grunnleggende statistikk',
                    'Annonser inkludert'
                ]
                # For free plan when user has paid subscription, show it as cancellation option
                if current_plan != 'free':
                    plan_data['description'] = 'Tilbake til gratis plan ved å kansellere abonnementet'
            elif plan.name == 'premium':
                plan_data['features'] = [
                    'Ubegrenset quiz og prøveeksamener',
                    'Alle videoer og læringsmateriell',
                    'Detaljert statistikk og fremgang',
                    'AI-tilpasset læring',
                    'Ingen annonser',
                    'Prioritert kundesupport'
                ]
            elif plan.name == 'pro':
                plan_data['features'] = [
                    'Alt fra Premium Plan',
                    'Offline modus for læring',
                    'Personlig AI-veileder',
                    'Avansert læringsanalyse',
                    'Raskere kundesupport',
                    'Tidlig tilgang til nye funksjoner'
                ]
            
            # Check upgrade eligibility
            can_upgrade, message = UpgradeService.can_upgrade_to(current_user.id, plan.name)
            plan_data['can_upgrade'] = can_upgrade
            
            if can_upgrade:
                try:
                    upgrade_info = UpgradeService.calculate_upgrade_cost(current_user.id, plan.name)
                    plan_data['upgrade_info'] = upgrade_info
                except ValueError:
                    plan_data['can_upgrade'] = False
            
            # Check if this would be a downgrade
            current_plan_obj = SubscriptionService.get_plan_by_name(current_plan)
            if current_plan_obj and plan.price_nok < current_plan_obj.price_nok:
                plan_data['is_downgrade'] = True
            
            plan_options.append(plan_data)
        
        return jsonify({
            'current_plan': current_plan,
            'subscription_stats': subscription_stats,
            'plans': plan_options
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/api/features')
@login_required
def api_features():
    """API endpoint to get user's plan features"""
    plan_name = SubscriptionService.get_user_plan(current_user.id)
    features = SubscriptionService.get_plan_features(plan_name)
    
    return jsonify({
        'plan': plan_name,
        'features': features,
        'should_show_ads': SubscriptionService.should_show_ads(current_user.id)
    })


# Guest routes (no login required)
@subscription_bp.route('/pricing')
def pricing():
    """Redirect to homepage pricing section"""
    return redirect(url_for('main.index') + '#pricing')


@subscription_bp.route('/features')
def features():
    """Feature comparison page"""
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_nok).all()
    
    # Feature comparison matrix
    feature_matrix = {
        'Quiz per dag': {
            'free': '10',
            'premium': 'Ubegrenset',
            'pro': 'Ubegrenset'
        },
        'Prøveeksamener per uke': {
            'free': '2',
            'premium': 'Ubegrenset', 
            'pro': 'Ubegrenset'
        },
        'Videoer': {
            'free': '❌',
            'premium': '✅',
            'pro': '✅'
        },
        'Detaljert statistikk': {
            'free': '❌',
            'premium': '✅',
            'pro': '✅'
        },
        'AI-tilpasset læring': {
            'free': '❌',
            'premium': '✅',
            'pro': '✅'
        },
        'Offline modus': {
            'free': '❌',
            'premium': '❌',
            'pro': '✅'
        },
        'Personlig veileder': {
            'free': '❌',
            'premium': '❌',
            'pro': '✅'
        },
        'Annonser': {
            'free': '✅',
            'premium': '❌',
            'pro': '❌'
        },
        'Prioritert støtte': {
            'free': '❌',
            'premium': '✅',
            'pro': '✅'
        }
    }
    
    return render_template('subscription/features.html', 
                         plans=plans, 
                         feature_matrix=feature_matrix)


@subscription_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        stripe_service = StripeService()
        success = stripe_service.handle_webhook(payload, sig_header)
        
        if success:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'error': 'Webhook handling failed'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400
