# Payment System Setup & Verification Guide

## Overview
This guide helps you verify that the Stripe payment integration is working correctly and set up the automated subscription management system.

## Current Implementation Status

### ✅ What's Already Working
- **Stripe Integration**: Fully configured with live API keys
- **Payment Models**: Complete database schema for subscriptions, payments, and usage tracking
- **Subscription Service**: Comprehensive service layer for plan management
- **Admin Access**: Admin users automatically get Pro plan access to everything
- **Usage Limits**: Free users have daily/weekly limits, Premium/Pro users unlimited
- **Payment Processing**: Complete checkout flow with Stripe

### 🆕 What's Been Added
- **Daily Subscription Check**: Automated job to expire subscriptions exactly 30 days after payment
- **Admin Privilege Protection**: Admins always have Pro access regardless of subscription status
- **Proper Expiration Handling**: Subscriptions expire exactly one month after payment
- **Comprehensive Logging**: Detailed logging for subscription maintenance

## Setup Instructions

### 1. Test Current System
```bash
cd /Users/viktorigesund/Documents/teoritest
python3 verify_payment.py
```

This comprehensive script will verify:
- Stripe API connectivity and configuration
- Database models and connectivity
- Payment service functionality
- Admin user protection
- Payment intent creation
- Subscription statistics
- Daily job files existence
- Cron job installation status
- All core payment system functionality

### 2. Set Up Daily Subscription Check
```bash
chmod +x scripts/jobs/setup_cron.sh
./scripts/jobs/setup_cron.sh
```

This installs a cron job that runs daily at 00:05 (5 minutes after midnight) to:
- Expire subscriptions that are exactly 30 days old
- Ensure admin users always have Pro access
- Generate daily subscription reports
- Log all activities

### 3. Manual Testing
```bash
# Run the subscription check manually
python3 scripts/jobs/daily_subscription_check.py

# Check cron job is installed
crontab -l
```

## Subscription Flow

### Free Users
- 10 quiz per day
- 2 practice exams per week
- See ads
- No video access
- Basic stats only

### Premium Users (149 NOK/month)
- Unlimited quiz and exams
- No ads
- Full video access
- Detailed statistics
- AI-adaptive learning

### Pro Users (249 NOK/month)
- Everything from Premium
- Offline mode
- Personal AI tutor
- Advanced analytics

### Admin Users
- **Always have Pro access** regardless of subscription status
- Never see ads
- Unlimited access to all features
- Automatic Pro plan assignment

## Payment Expiration Logic

### How It Works
1. **Payment Processing**: When payment is completed, subscription expires_at is set to exactly 30 days from payment date
2. **Daily Check**: Every night at 00:05, the system checks for expired subscriptions
3. **Automatic Downgrade**: Expired users are automatically moved to Free plan
4. **Admin Protection**: Admin users are never downgraded and always maintain Pro access

### Example Timeline
- **Day 0**: User pays for Premium plan (expires_at = Day 30)
- **Day 1-29**: User has Premium access
- **Day 30 00:05**: Subscription expires, user downgraded to Free
- **Day 30+**: User has Free access until they pay again

## Testing Payment Flow

### Test Cards (Stripe Test Mode)
```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
```

### Live Testing
1. Start the application: `python run.py`
2. Navigate to `/subscription/plans`
3. Try upgrading to Premium
4. Complete payment with test card
5. Verify user gets Premium access immediately

## Monitoring & Logs

### Log Files
- `/var/log/sertifikatet/subscription_check.log` - Daily subscription maintenance
- `/var/log/sertifikatet/cron.log` - Cron job execution logs

### Manual Commands
```bash
# Comprehensive verification (replaces all other test scripts)
python3 verify_payment.py

# Manual daily job run
python3 scripts/jobs/daily_subscription_check.py

# Check cron job status
crontab -l | grep subscription

## Troubleshooting

### Common Issues

1. **Stripe API Error**: Check that STRIPE_SECRET_KEY is set correctly in .env
2. **Webhook Not Working**: Make sure STRIPE_WEBHOOK_SECRET is configured
3. **Subscriptions Not Expiring**: Check that cron job is running with `crontab -l`
4. **Admin Users Losing Access**: Run the daily check manually to restore Pro access

### Reset User Plan
```python
from app import create_app, db
from app.models import User
from app.services.payment_service import SubscriptionService

app = create_app()
with app.app_context():
    # Reset user to Premium
    SubscriptionService.update_user_plan(user_id, 'premium', 'active')
```

## Security Notes

- **Live Stripe Keys**: Currently using live API keys (pk_live_... and sk_live_...)
- **Admin Protection**: Admin users cannot be downgraded by automated systems
- **Payment Verification**: All payments are verified through Stripe webhooks
- **Audit Logging**: All subscription changes are logged for security

## Next Steps

1. **Set up webhook endpoint** in Stripe dashboard pointing to `/subscription/webhook/stripe`
2. **Test the full payment flow** with real cards in live mode
3. **Monitor logs** for the first few days to ensure system is working correctly
4. **Consider adding email notifications** for subscription expiry warnings

## Support

If you encounter any issues:
1. Check the logs in `/var/log/sertifikatet/`
2. Run the test script: `python3 verify_payment.py`
3. Verify Stripe dashboard for payment status
4. Contact system administrator
