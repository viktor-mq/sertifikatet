# Payment and Subscription Models for Phase 11
from datetime import datetime
from . import db

class SubscriptionPlan(db.Model):
    """Subscription plans (Free, Premium, Pro)"""
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 'free', 'premium', 'pro'
    display_name = db.Column(db.String(100), nullable=False)  # 'Premium Plan'
    price_nok = db.Column(db.Numeric(10, 2), nullable=False)  # Price in NOK
    billing_cycle = db.Column(db.String(20), default='monthly')  # 'monthly', 'yearly'
    description = db.Column(db.Text)
    features_json = db.Column(db.Text)  # JSON list of features
    max_daily_quizzes = db.Column(db.Integer)  # null = unlimited
    max_weekly_exams = db.Column(db.Integer)  # null = unlimited
    has_ads = db.Column(db.Boolean, default=True)
    has_detailed_stats = db.Column(db.Boolean, default=False)
    has_ai_adaptive = db.Column(db.Boolean, default=False)
    has_offline_mode = db.Column(db.Boolean, default=False)
    has_personal_tutor = db.Column(db.Boolean, default=False)
    has_video_access = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('UserSubscription', backref='plan')
    payments = db.relationship('Payment', backref='plan')


class UserSubscription(db.Model):
    """User's current and historical subscriptions"""
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'cancelled', 'expired', 'pending'
    
    # Billing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    auto_renew = db.Column(db.Boolean, default=True)
    next_billing_date = db.Column(db.DateTime)
    
    # Payment integration
    stripe_subscription_id = db.Column(db.String(255))  # Stripe subscription ID
    payment_method_id = db.Column(db.String(255))  # Stripe payment method ID
    
    # Trial
    is_trial = db.Column(db.Boolean, default=False)
    trial_ends_at = db.Column(db.DateTime)
    
    # Metadata
    cancelled_reason = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='subscriptions')
    payments = db.relationship('Payment', backref='subscription')
    
    __table_args__ = (
        db.Index('idx_user_subscription_status', 'user_id', 'status'),
        db.Index('idx_subscription_expires', 'expires_at'),
    )


class Payment(db.Model):
    """Payment transactions and history"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    
    # Payment details
    amount_nok = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='NOK')
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed', 'refunded', 'cancelled'
    payment_method = db.Column(db.String(50))  # 'card', 'vipps', 'bank_transfer', 'paypal'
    
    # Stripe integration
    stripe_payment_intent_id = db.Column(db.String(255))
    stripe_charge_id = db.Column(db.String(255))
    stripe_customer_id = db.Column(db.String(255))
    
    # Norwegian payment methods
    vipps_transaction_id = db.Column(db.String(255))
    bank_reference = db.Column(db.String(100))
    
    # Invoice details
    invoice_number = db.Column(db.String(50), unique=True)
    invoice_pdf_path = db.Column(db.String(255))
    
    # Billing address (for invoices)
    billing_name = db.Column(db.String(255))
    billing_email = db.Column(db.String(255))
    billing_address = db.Column(db.Text)
    billing_city = db.Column(db.String(100))
    billing_postal_code = db.Column(db.String(20))
    billing_country = db.Column(db.String(2), default='NO')
    
    # Transaction details
    payment_date = db.Column(db.DateTime)
    failure_reason = db.Column(db.Text)
    refund_amount = db.Column(db.Numeric(10, 2))
    refund_reason = db.Column(db.Text)
    refunded_at = db.Column(db.DateTime)
    
    # Metadata
    description = db.Column(db.String(255))
    metadata_json = db.Column(db.Text)  # JSON for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='payments')
    
    __table_args__ = (
        db.Index('idx_payment_user_status', 'user_id', 'status'),
        db.Index('idx_payment_date', 'payment_date'),
        db.Index('idx_stripe_payment_intent', 'stripe_payment_intent_id'),
    )


class UsageLimit(db.Model):
    """Track daily/weekly usage limits for free users"""
    __tablename__ = 'usage_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Daily limits
    daily_quizzes_taken = db.Column(db.Integer, default=0)
    daily_limit_date = db.Column(db.Date, default=datetime.utcnow().date)
    
    # Weekly limits  
    weekly_exams_taken = db.Column(db.Integer, default=0)
    weekly_limit_start = db.Column(db.Date)  # Start of the week
    
    # Monthly limits (future use)
    monthly_videos_watched = db.Column(db.Integer, default=0)
    monthly_limit_start = db.Column(db.Date)
    
    # Reset tracking
    last_daily_reset = db.Column(db.DateTime)
    last_weekly_reset = db.Column(db.DateTime)
    last_monthly_reset = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='usage_limit', uselist=False)
    
    __table_args__ = (
        db.Index('idx_usage_user_date', 'user_id', 'daily_limit_date'),
    )


class DiscountCode(db.Model):
    """Discount codes and promotions"""
    __tablename__ = 'discount_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Discount details
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage', 'fixed_amount', 'free_trial'
    discount_value = db.Column(db.Numeric(10, 2))  # Percentage (e.g., 20.00) or amount in NOK
    free_trial_days = db.Column(db.Integer)  # For free trial codes
    
    # Validity
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer)  # null = unlimited
    current_uses = db.Column(db.Integer, default=0)
    
    # Restrictions
    min_purchase_amount = db.Column(db.Numeric(10, 2))
    applicable_plans = db.Column(db.String(255))  # JSON list of plan names
    first_time_users_only = db.Column(db.Boolean, default=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='created_discount_codes')
    usages = db.relationship('DiscountUsage', backref='code')


class DiscountUsage(db.Model):
    """Track discount code usage"""
    __tablename__ = 'discount_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    code_id = db.Column(db.Integer, db.ForeignKey('discount_codes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'))
    
    # Usage details
    discount_amount = db.Column(db.Numeric(10, 2))
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='discount_usages')
    payment = db.relationship('Payment', backref='discount_usage', uselist=False)
    
    __table_args__ = (
        db.UniqueConstraint('code_id', 'user_id', 'payment_id', name='_code_user_payment_uc'),
    )


class RefundRequest(db.Model):
    """Customer refund requests"""
    __tablename__ = 'refund_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Request details
    reason = db.Column(db.String(100))  # 'not_satisfied', 'technical_issues', 'accidental_purchase', 'other'
    description = db.Column(db.Text)
    requested_amount = db.Column(db.Numeric(10, 2))
    
    # Processing
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected', 'processed'
    admin_notes = db.Column(db.Text)
    processed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_at = db.Column(db.DateTime)
    
    # Stripe refund
    stripe_refund_id = db.Column(db.String(255))
    actual_refund_amount = db.Column(db.Numeric(10, 2))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payment = db.relationship('Payment', backref='refund_requests')
    user = db.relationship('User', foreign_keys=[user_id], backref='refund_requests')
    processed_by = db.relationship('User', foreign_keys=[processed_by_user_id], backref='processed_refunds')


class BillingAddress(db.Model):
    """User billing addresses"""
    __tablename__ = 'billing_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Address details
    company_name = db.Column(db.String(255))
    full_name = db.Column(db.String(255), nullable=False)
    address_line_1 = db.Column(db.String(255), nullable=False)
    address_line_2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(2), default='NO')
    
    # Norwegian specific
    organization_number = db.Column(db.String(20))  # For businesses
    
    # Status
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='billing_addresses')
    
    __table_args__ = (
        db.Index('idx_billing_user', 'user_id'),
    )
