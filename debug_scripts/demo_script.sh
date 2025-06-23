#!/bin/bash

echo "🚀 Sertifikatet Mobile Demo Script"
echo "=================================="
echo ""

echo "1. 📱 Starting development server..."
echo "   Run: python run.py"
echo "   Then open: http://localhost:5000"
echo ""

echo "2. 🔧 Testing Mobile in Chrome:"
echo "   - Press F12 → Click mobile icon 📱"
echo "   - Choose iPhone/Android device"
echo "   - Test hamburger menu ☰"
echo ""

echo "3. 🎯 Testing Quiz Swipe Gestures:"
echo "   - Go to /quiz/categories"
echo "   - Start any quiz"
echo "   - Swipe left/right on questions"
echo "   - Or use arrow keys on desktop"
echo ""

echo "4. 📲 Testing PWA Install:"
echo "   - Wait 2 seconds for install banner"
echo "   - Or: Chrome menu → 'Install Sertifikatet...'"
echo "   - Check if app appears in applications"
echo ""

echo "5. 🔄 Testing Offline Mode:"
echo "   - Start a quiz"
echo "   - Chrome DevTools → Network → Offline"
echo "   - Continue quiz, answers saved locally"
echo "   - Go back online → data syncs"
echo ""

echo "6. 📊 PWA Audit:"
echo "   - Chrome DevTools → Lighthouse tab"
echo "   - Select 'Progressive Web App'"
echo "   - Run audit for PWA score"
echo ""

echo "7. 📱 Real Device Testing:"
echo "   - Find your IP: ifconfig | grep inet"
echo "   - Run: python run.py --host=0.0.0.0"
echo "   - Mobile: http://YOUR_IP:5000"
echo ""

echo "✅ Features to demonstrate:"
echo "   • Responsive navigation"
echo "   • Quiz swipe gestures"  
echo "   • PWA install"
echo "   • Offline functionality"
echo "   • Pull-to-refresh"
echo "   • Haptic feedback (mobile)"
echo ""

echo "Happy testing! 🎉"
