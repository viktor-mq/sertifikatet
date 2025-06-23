# Debug Scripts

This folder contains diagnostic and debugging scripts for the Sertifikatet project. These are **not** unit tests - they are utility scripts for testing specific functionality and debugging issues.

## Email Testing
- `test_all_emails.py` - Comprehensive email system testing (sends test emails)
- `test_error_email.py` - Test error notification emails
- `check_email_config.py` - Email configuration diagnostic

## Database & Model Testing  
- `test_complete_fix.py` - Game scenario database fix verification
- `test_game_fix.py` - Game model fixes verification
- `test_imports.py` - Import verification and basic setup
- `test_subscription_fix.py` - Subscription service testing

## Feature-Specific Testing
- `test_cancellation_behavior.py` - Subscription cancellation behavior testing
- `test_specific_error.py` - Specific error scenario testing
- `debug_user_access.py` - Subscription access debugging

## Demo Scripts
- `demo_script.sh` - Mobile demo and testing guide

## Usage

Run these scripts from the project root directory:

```bash
# Email testing (will send actual emails)
python debug_scripts/test_all_emails.py

# Database fix verification
python debug_scripts/test_complete_fix.py

# Subscription testing
python debug_scripts/test_subscription_fix.py
```

⚠️ **Warning**: Some scripts send real emails or interact with the production database. Always check the script before running.

## Proper Unit Tests

For proper unit tests, use the `tests/` folder:

```bash
# Run all unit tests
pytest

# Run specific test files  
pytest tests/test_auth.py
pytest tests/test_models.py
```
