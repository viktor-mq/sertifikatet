# Achievement Icons System

This directory contains custom SVG icons for the Sertifikatet achievement system.

## 🎨 Icon Design Guidelines

### Visual Style
- **Size**: 64x64px SVG format
- **Background**: Colored circle with white border
- **Icon**: White foreground elements
- **Style**: Simple, clean, easily recognizable at small sizes

### Color Scheme
Each achievement has a unique color that reflects its category and difficulty:

- 🟢 **Green** (#22c55e, #059669, #16a34a) - Beginner/Success achievements
- 🔵 **Blue** (#3b82f6, #06b6d4) - Learning/Knowledge achievements  
- 🟡 **Orange/Amber** (#f97316, #f59e0b) - Consistency achievements
- 🔴 **Red** (#ef4444, #dc2626, #7c2d12) - Challenge/Mastery achievements
- 🟣 **Purple** (#8b5cf6, #7c3aed) - Advanced/Expert achievements

## 📋 Current Achievement Icons

| Icon File | Achievement Name | Description | Color |
|-----------|------------------|-------------|-------|
| `first-quiz.svg` | Første Quiz | Checkered flag for first quiz completion | Green |
| `quiz-enthusiast.svg` | Quiz Entusiast | Brain symbol for 10 quizzes | Blue |
| `quiz-master.svg` | Quiz Mester | Crown for 50 quizzes mastery | Purple |
| `sharpshooter.svg` | Skarpskytter | Bullseye target for 90% accuracy | Red |
| `perfect-consistent.svg` | Konsistent Perfekt | Diamond for 5 perfect scores | Amber |
| `knowledge-seeker.svg` | Kunnskapssøker | Magnifying glass for 100 questions | Cyan |
| `master-learner.svg` | Læremester | Teacher figure for 1000 questions | Violet |
| `consistent.svg` | Konsistent | Lightning bolt for 3-day streak | Orange |
| `week-streak.svg` | Uke Streak | Fire for 7-day streak | Red |
| `dedicated.svg` | Dedikert | Flexed bicep for dedication | Red |
| `unstoppable.svg` | Ustoppelig | Rocket for 30-day streak | Dark Red |
| `exam-ready.svg` | Eksamensklar | Graduation cap for exam success | Emerald |
| `danger-signs-expert.svg` | Fareskilt Ekspert | Warning triangle for danger signs mastery | Red |
| `traffic-rules-guru.svg` | Trafikkregler Guru | Traffic light for traffic rules mastery | Green |

## 🔧 Technical Implementation

### Template Usage
The achievement template automatically detects icon types:

```html
{% if item.achievement.icon_filename and not item.achievement.icon_filename.startswith('fa-') %}
    <!-- Custom SVG/PNG icon -->
    <img src="{{ url_for('static', filename='achievements/' + item.achievement.icon_filename) }}" 
         alt="{{ item.achievement.name }}" 
         class="w-10 h-10 {{ 'filter brightness-0 invert' if not item.earned else '' }}">
{% elif item.achievement.icon_filename and item.achievement.icon_filename.startswith('fa-') %}
    <!-- FontAwesome fallback -->
    <i class="fas {{ item.achievement.icon_filename }} text-2xl"></i>
{% else %}
    <!-- Default icon -->
    <i class="fas fa-trophy text-2xl"></i>
{% endif %}
```

### Visual States
- **Earned**: Full color icon with colored background
- **Unearned**: Grayscale filter applied (`filter brightness-0 invert`)

### File Naming Convention
- Use kebab-case: `achievement-name.svg`
- Be descriptive but concise
- Match the achievement's purpose

## 🎯 Adding New Icons

### Step 1: Design the Icon
1. Create a 64x64px SVG
2. Use the color scheme guidelines
3. Keep the design simple and recognizable
4. Test at small sizes (16px, 24px)

### Step 2: Update Achievement Service
Add the icon filename to the achievement definition in `app/services/achievement_service.py`:

```python
{'id': X, 'rule': AchievementRule, 'params': {
    'name': 'Achievement Name',
    'description': 'Achievement description',
    'points': XX,
    'icon': 'new-achievement.svg',  # Your new icon file
    'requirement_type': 'type',
    'requirement_value': X
}}
```

### Step 3: Test the Implementation
1. Place the SVG file in `static/achievements/`
2. Restart the application
3. Check the achievements page to verify the icon displays correctly
4. Test both earned and unearned states

## 🚀 Future Enhancements

### Planned Features
- **Animated icons** for special achievements
- **Rarity indicators** (bronze, silver, gold borders)
- **Seasonal themes** for holiday achievements
- **User customization** options

### Icon Categories to Add
- **Driving-specific**: Steering wheel, road signs, car icons
- **Norwegian elements**: Flag, fjord, traditional symbols
- **Gamification**: Levels, badges, trophies
- **Social**: Friends, leaderboards, competitions

## 📝 Notes

- Icons are optimized for both light and dark themes
- SVG format ensures crisp display on all devices
- Fallback to FontAwesome icons for backwards compatibility
- All icons are accessible with proper alt text
- Color choices follow WCAG contrast guidelines

---

**Last Updated**: July 11, 2025
**Total Icons**: 14 custom achievement icons
**Status**: ✅ Ready for production
