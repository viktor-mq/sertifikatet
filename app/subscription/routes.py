"""
Subscription and Payment Routes
Phase 11: Payment & Subscriptions
"""

from flask import render_template, request, redirect, url_for, jsonify, flash, session
from flask_login import login_required, current_user
from datetime import datetime
from . import subscription_bp
from .. import db
from ..payment_models import SubscriptionPlan, Payment, UserSubscription
from ..services.payment_service import SubscriptionService, UsageLimitService, PaymentService
from ..services.stripe_service import StripeService


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
    """Upgrade to a specific plan"""
    plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan:
        flash('Plan ikke funnet', 'error')
        return redirect(url_for('subscription.plans'))
    
    # Check if user already has this plan
    current_plan = SubscriptionService.get_user_plan(current_user.id)
    if current_plan == plan_name:
        flash('Du har allerede denne planen', 'info')
        return redirect(url_for('subscription.manage'))
    
    return render_template('subscription/upgrade.html', plan=plan)


@subscription_bp.route('/checkout/<plan_name>', methods=['GET', 'POST'])
@login_required
def checkout(plan_name):
    """Checkout page for plan upgrade"""
    plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan:
        flash('Plan ikke funnet', 'error')
        return redirect(url_for('subscription.plans'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'stripe')
        
        try:
            if payment_method == 'stripe':
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
    
    return render_template('subscription/checkout.html', plan=plan)


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
    
    return render_template('subscription/manage.html',
                         subscription_stats=subscription_stats,
                         usage_stats=usage_stats,
                         payment_history=payment_history)


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
    """Public pricing page"""
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_nok).all()
    return render_template('subscription/pricing.html', plans=plans)


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
