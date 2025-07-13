# Database-Driven XP Rewards System

## Overview
The XP rewards system has been updated to use database configuration instead of hardcoded values, with support for dynamic scaling based on quiz length and other factors.

## Setup Instructions

### 1. Run the Database Migration
Make sure your database includes the new `xp_rewards` table:

```sql
CREATE TABLE xp_rewards (
    id INT PRIMARY KEY,
    reward_type VARCHAR(50) UNIQUE,
    base_value INT,
    scaling_factor DECIMAL(3,2) DEFAULT 1.0,
    max_value INT,
    description TEXT
);
```

### 2. Initialize XP Rewards Data
Run the initialization script to populate the table with recommended values:

```bash
python scripts/init_xp_rewards.py
```

This will create all the reward types with optimal scaling factors.

## How It Works

### Scaling Formulas

**Quiz Completion XP:**
- Formula: `base_value + (question_count × scaling_factor)`
- Default: `5 + (questions × 0.5)`
- Examples:
  - 5 questions: 5 + 2.5 = 8 XP
  - 20 questions: 5 + 10 = 15 XP
  - 40 questions: 5 + 20 = 25 XP

**Perfect Score Bonus:**
- Formula: `question_count × scaling_factor`
- Default: `questions × 1.5`
- Examples:
  - 5 questions: 8 XP bonus
  - 20 questions: 30 XP bonus
  - 40 questions: 60 XP bonus

**Total XP Example (5-question perfect quiz):**
- Correct answers: 5 × 2 = 10 XP
- Completion: 5 + (5 × 0.5) = 8 XP
- Perfect bonus: 5 × 1.5 = 8 XP
- **Total: 26 XP**

## API Endpoints

### Test XP Calculations
```
GET /gamification/api/calculate-xp?correct=5&total=5&score=100
```

Response:
```json
{
  "total_xp": 26,
  "breakdown": {
    "correct_answers": 10,
    "completion": 8,
    "perfect_bonus": 8
  }
}
```

### Get User Level Info
```
GET /gamification/api/level-info
```

## Updating Reward Values

You can modify XP rewards directly in the database:

```sql
-- Increase quiz completion base reward
UPDATE xp_rewards 
SET base_value = 8 
WHERE reward_type = 'quiz_complete';

-- Adjust perfect score scaling
UPDATE xp_rewards 
SET scaling_factor = 2.0 
WHERE reward_type = 'quiz_perfect';
```

## Fallback System

If the database is unavailable, the system automatically falls back to hardcoded values in `GamificationService.FALLBACK_XP_REWARDS`.

## Testing

1. **Complete a 5-question quiz with 100% score** - should get 26 XP
2. **Complete a 20-question quiz with 100% score** - should get 85 XP  
3. **Visit gamification dashboard** - XP should display correctly (35/100 XP → actual total/100 XP)
4. **Check API endpoint** - test calculations match expected values

## Migration Notes

- Existing XP totals are preserved
- New scaling only applies to future quiz completions
- All existing functions maintain the same interface
- Fallback ensures system continues working even if database migration fails
