"""
Stripe Payment Integration Service
Handles Stripe API calls for payment processing and subscription management
"""

import stripe
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from flask import current_app, url_for
from ..models import User
from ..payment_models import (
    SubscriptionPlan, UserSubscription, Payment, BillingAddress
)
from .. import db
from .payment_service import PaymentService, SubscriptionService

logger = logging.getLogger(__name__)


class StripeService:
    """Service for Stripe payment processing"""
    
    def __init__(self):
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        self.publishable_key = current_app.config['STRIPE_PUBLISHABLE_KEY']
    
    def create_customer(self, user: User) -> Optional[str]:
        """Create a Stripe customer for the user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={
                    'user_id': user.id,
                    'platform': 'sertifikatet'
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer for user {user.id}: {str(e)}")
            return None
    
    def get_or_create_customer(self, user: User) -> Optional[str]:
        """Get existing Stripe customer ID or create new one"""
        # Check if user already has a Stripe customer ID stored
        # You might want to add stripe_customer_id field to User model
        # For now, we'll create a new customer each time
        return self.create_customer(user)
    
    def create_payment_intent(self, user_id: int, plan_name: str, 
                            success_url: str = None, cancel_url: str = None) -> Dict:
        """Create a Stripe Payment Intent for subscription"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
            if not plan:
                raise ValueError(f"Plan '{plan_name}' not found")
            
            # Create customer in Stripe
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                raise ValueError("Failed to create Stripe customer")
            
            # Create payment record in our database
            payment_data = PaymentService.create_payment_intent(user_id, plan_name)
            payment = Payment.query.get(payment_data['payment_id'])
            
            # Convert NOK to øre (smallest currency unit)
            amount_in_ore = int(plan.price_nok * 100)
            
            # Create Payment Intent in Stripe
            intent = stripe.PaymentIntent.create(
                amount=amount_in_ore,
                currency='nok',
                customer=customer_id,
                description=f"Sertifikatet {plan.display_name} Subscription",
                metadata={
                    'user_id': user_id,
                    'plan_name': plan_name,
                    'payment_id': payment.id,
                    'invoice_number': payment.invoice_number
                },
                automatic_payment_methods={
                    'enabled': True,
                },
                setup_future_usage='off_session'  # For future subscription renewals
            )
            
            # Update payment with Stripe intent ID
            payment.stripe_payment_intent_id = intent.id
            payment.stripe_customer_id = customer_id
            db.session.commit()
            
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'payment_id': payment.id,
                'amount': float(plan.price_nok),
                'currency': 'NOK',
                'description': payment.description,
                'publishable_key': self.publishable_key
            }
            
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise
    
    def create_checkout_session(self, user_id: int, plan_name: str, 
                              success_url: str, cancel_url: str) -> Dict:
        """Create a Stripe Checkout session for subscription"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
            if not plan:
                raise ValueError(f"Plan '{plan_name}' not found")
            
            # Create customer in Stripe
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                raise ValueError("Failed to create Stripe customer")
            
            # Create payment record in our database
            payment_data = PaymentService.create_payment_intent(user_id, plan_name)
            payment = Payment.query.get(payment_data['payment_id'])
            
            # Convert NOK to øre (smallest currency unit)
            amount_in_ore = int(plan.price_nok * 100)
            
            # Create Checkout Session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'nok',
                        'product_data': {
                            'name': f'Sertifikatet {plan.display_name}',
                            'description': f'Monthly subscription to {plan.display_name}',
                        },
                        'unit_amount': amount_in_ore,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url + f'?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment.id}',
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'plan_name': plan_name,
                    'payment_id': payment.id,
                    'invoice_number': payment.invoice_number
                },
                billing_address_collection='required',
                customer_update={
                    'address': 'auto',
                    'name': 'auto'
                }
            )
            
            # Update payment with Stripe session ID
            payment.stripe_payment_intent_id = session.id
            payment.stripe_customer_id = customer_id
            db.session.commit()
            
            return {
                'checkout_url': session.url,
                'session_id': session.id,
                'payment_id': payment.id,
                'amount': float(plan.price_nok),
                'currency': 'NOK',
                'publishable_key': self.publishable_key
            }
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise
    
    def confirm_payment(self, session_id: str = None, payment_intent_id: str = None) -> bool:
        """Confirm payment and activate subscription"""
        try:
            if session_id:
                # Handle Checkout Session completion
                session = stripe.checkout.Session.retrieve(session_id)
                payment_intent_id = session.payment_intent
                metadata = session.metadata
            elif payment_intent_id:
                # Handle Payment Intent confirmation
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                metadata = intent.metadata
            else:
                raise ValueError("Either session_id or payment_intent_id must be provided")
            
            # Find our payment record
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=session_id or payment_intent_id
            ).first()
            
            if not payment:
                logger.error(f"Payment not found for Stripe session/intent: {session_id or payment_intent_id}")
                return False
            
            # Complete the payment
            success = PaymentService.complete_payment(
                payment.id, 
                session_id or payment_intent_id,
                'stripe_card'
            )
            
            if success:
                logger.info(f"Payment {payment.id} completed successfully for user {payment.user_id}")
                
                # Update billing address if available (from Checkout)
                if session_id:
                    self._update_billing_address_from_session(session_id, payment.user_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return False
    
    def _update_billing_address_from_session(self, session_id: str, user_id: int):
        """Update user billing address from Checkout session"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer = stripe.Customer.retrieve(session.customer)
            
            if customer.address:
                address = customer.address
                billing_address = BillingAddress(
                    user_id=user_id,
                    full_name=customer.name or "",
                    address_line_1=address.line1 or "",
                    address_line_2=address.line2 or "",
                    city=address.city or "",
                    postal_code=address.postal_code or "",
                    country=address.country or "NO",
                    is_default=True,
                    created_at=datetime.utcnow()
                )
                
                # Set existing addresses as non-default
                BillingAddress.query.filter_by(user_id=user_id, is_default=True)\
                                  .update({'is_default': False})
                
                db.session.add(billing_address)
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error updating billing address from session {session_id}: {str(e)}")
    
    def create_subscription(self, user_id: int, plan_name: str, payment_method_id: str) -> Dict:
        """Create a recurring Stripe subscription"""
        try:
            user = User.query.get(user_id)
            plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
            
            if not user or not plan:
                raise ValueError("User or plan not found")
            
            # Create or get customer
            customer_id = self.get_or_create_customer(user)
            
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id
                }
            )
            
            # Create price in Stripe
            price = stripe.Price.create(
                unit_amount=int(plan.price_nok * 100),  # Convert to øre
                currency='nok',
                recurring={'interval': 'month'},
                product_data={'name': f'Sertifikatet {plan.display_name}'},
            )
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price.id}],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'user_id': user_id,
                    'plan_name': plan_name
                }
            )
            
            return {
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status
            }
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    def cancel_subscription(self, user_id: int) -> bool:
        """Cancel user's Stripe subscription"""
        try:
            subscription = UserSubscription.query.filter_by(
                user_id=user_id,
                status='active'
            ).first()
            
            if not subscription or not subscription.stripe_subscription_id:
                return False
            
            # Cancel in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update in our database
            return SubscriptionService.cancel_subscription(user_id, "Cancelled via Stripe")
            
        except Exception as e:
            logger.error(f"Error cancelling subscription for user {user_id}: {str(e)}")
            return False
    
    def handle_webhook(self, payload: str, sig_header: str) -> bool:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
            )
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                self._handle_payment_succeeded(payment_intent)
                
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                self._handle_payment_failed(payment_intent)
                
            elif event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                self._handle_checkout_completed(session)
                
            elif event['type'] == 'invoice.payment_succeeded':
                invoice = event['data']['object']
                self._handle_invoice_payment_succeeded(invoice)
                
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                self._handle_subscription_cancelled(subscription)
            
            return True
            
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            return False
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return False
    
    def _handle_payment_succeeded(self, payment_intent):
        """Handle successful payment"""
        metadata = payment_intent.get('metadata', {})
        payment_id = metadata.get('payment_id')
        
        if payment_id:
            PaymentService.complete_payment(
                int(payment_id),
                payment_intent['id'],
                'stripe_card'
            )
    
    def _handle_payment_failed(self, payment_intent):
        """Handle failed payment"""
        payment = Payment.query.filter_by(
            stripe_payment_intent_id=payment_intent['id']
        ).first()
        
        if payment:
            payment.status = 'failed'
            payment.failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
            db.session.commit()
    
    def _handle_checkout_completed(self, session):
        """Handle completed checkout session"""
        self.confirm_payment(session_id=session['id'])
    
    def _handle_invoice_payment_succeeded(self, invoice):
        """Handle successful subscription invoice payment"""
        # Handle recurring subscription payments
        subscription_id = invoice['subscription']
        if subscription_id:
            # Update subscription status and next billing date
            subscription = UserSubscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription:
                subscription.status = 'active'
                subscription.next_billing_date = datetime.fromtimestamp(
                    invoice['next_payment_attempt']
                ) if invoice.get('next_payment_attempt') else None
                db.session.commit()
    
    def _handle_subscription_cancelled(self, stripe_subscription):
        """Handle cancelled subscription"""
        subscription = UserSubscription.query.filter_by(
            stripe_subscription_id=stripe_subscription['id']
        ).first()
        
        if subscription:
            SubscriptionService.cancel_subscription(
                subscription.user_id,
                "Subscription cancelled in Stripe"
            )
    
    def get_payment_methods(self, user_id: int) -> List[Dict]:
        """Get user's saved payment methods"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []
            
            # You would need to store customer_id in User model
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting payment methods for user {user_id}: {str(e)}")
            return []
