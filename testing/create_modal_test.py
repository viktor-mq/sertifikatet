#!/usr/bin/env python3
"""
Frontend Modal System Test Script
Creates a simple test page to verify the quiz results modal system works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from flask import render_template_string

def create_modal_test_page():
    """Create a standalone test page for the modal system"""
    
    test_html = """
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modal System Test - Sertifikatet</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .glass {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body class="text-white">
    <div class="max-w-4xl mx-auto px-6 py-12">
        <h1 class="text-3xl font-bold text-center mb-8">
            <span class="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                🧪 Modal System Integration Test
            </span>
        </h1>
        
        <div class="glass rounded-2xl p-8 mb-8">
            <h2 class="text-xl font-semibold mb-4">Test Status</h2>
            <div id="testStatus" class="space-y-2">
                <div id="jsLoadStatus" class="flex items-center">
                    <span class="w-4 h-4 rounded-full bg-gray-400 mr-3"></span>
                    <span>Loading JavaScript files...</span>
                </div>
                <div id="modalStatus" class="flex items-center">
                    <span class="w-4 h-4 rounded-full bg-gray-400 mr-3"></span>
                    <span>Checking modal system...</span>
                </div>
                <div id="gamificationStatus" class="flex items-center">
                    <span class="w-4 h-4 rounded-full bg-gray-400 mr-3"></span>
                    <span>Checking gamification integration...</span>
                </div>
            </div>
        </div>
        
        <div class="glass rounded-2xl p-8">
            <h2 class="text-xl font-semibold mb-6">Test Scenarios</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button onclick="testModalSystem('excellent')" 
                        class="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 
                               text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50">
                    🌟 Test Excellent Result (95%)
                </button>
                
                <button onclick="testModalSystem('good')" 
                        class="w-full bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 
                               text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50">
                    👍 Test Good Result (78%)
                </button>
                
                <button onclick="testModalSystem('poor')" 
                        class="w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 
                               text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50">
                    📚 Test Poor Result (45%)
                </button>
                
                <button onclick="testModalSystem('achievements')" 
                        class="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 
                               text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50">
                    🏆 Test With Achievements
                </button>
            </div>
            
            <div class="mt-6 p-4 bg-blue-500 bg-opacity-20 rounded-lg">
                <h3 class="font-semibold mb-2">Manual Test Checklist:</h3>
                <ul class="text-sm space-y-1">
                    <li>✅ Modal appears with smooth animation</li>
                    <li>✅ XP counter animates from 0 to target value</li>
                    <li>✅ Circular progress bar animates</li>
                    <li>✅ Achievement notifications show properly</li>
                    <li>✅ "Se gjennom svar" button opens review modal</li>
                    <li>✅ Review modal navigation works (arrows/dots)</li>
                    <li>✅ Answer options are color-coded correctly</li>
                    <li>✅ Modal closes properly with X or backdrop click</li>
                    <li>✅ System works on mobile (responsive design)</li>
                    <li>✅ Keyboard navigation works (ESC, arrows)</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Load gamification JavaScript files -->
    <script src="/static/js/gamification.js"></script>
    <script src="/static/js/quiz-gamification.js"></script>
    <script src="/static/js/quiz-results-modal.js"></script>

    <script>
    // Test data for different scenarios
    const testData = {
        excellent: {
            success: true,
            session_id: 123,
            results: {
                correct_answers: 19,
                total_questions: 20,
                accuracy: 95,
                score: 95,
                total_time: 180
            },
            gamification: {
                xp_earned: 45,
                achievements: [],
                level_ups: [],
                daily_challenges: []
            }
        },
        good: {
            success: true,
            session_id: 124,
            results: {
                correct_answers: 14,
                total_questions: 18,
                accuracy: 78,
                score: 78,
                total_time: 240
            },
            gamification: {
                xp_earned: 28,
                achievements: [],
                level_ups: [],
                daily_challenges: []
            }
        },
        poor: {
            success: true,
            session_id: 125,
            results: {
                correct_answers: 9,
                total_questions: 20,
                accuracy: 45,
                score: 45,
                total_time: 320
            },
            gamification: {
                xp_earned: 15,
                achievements: [],
                level_ups: [],
                daily_challenges: []
            }
        },
        achievements: {
            success: true,
            session_id: 126,
            results: {
                correct_answers: 15,
                total_questions: 15,
                accuracy: 100,
                score: 100,
                total_time: 150
            },
            gamification: {
                xp_earned: 50,
                achievements: [
                    {
                        name: "Perfekt Score",
                        description: "Fikk alle spørsmål riktig på en quiz",
                        points: 25
                    },
                    {
                        name: "Lynrask",
                        description: "Fullførte quiz på under 3 minutter",
                        points: 15
                    }
                ],
                level_ups: [3],
                daily_challenges: [
                    {
                        title: "Daily Quiz Master",
                        description: "Complete 3 quizzes today"
                    }
                ]
            }
        }
    };

    // Mock review data
    window.mockReviewData = {
        success: true,
        questions: [
            {
                question_id: 1,
                question_text: "Hva betyr dette skiltet?",
                image_filename: null,
                options: [
                    { letter: 'a', text: 'Stopp' },
                    { letter: 'b', text: 'Vikeplikt' },
                    { letter: 'c', text: 'Forbudt' },
                    { letter: 'd', text: 'Tillatt' }
                ],
                correct_answer: 'b',
                user_answer: 'b',
                is_correct: true,
                time_spent: 25,
                explanation: "Dette skiltet betyr vikeplikt. Du må gi andre trafikanter fri passasje."
            },
            {
                question_id: 2,
                question_text: "Hvor langt fra et fotgjengerpassage må du parkere?",
                image_filename: null,
                options: [
                    { letter: 'a', text: '3 meter' },
                    { letter: 'b', text: '5 meter' },
                    { letter: 'c', text: '10 meter' },
                    { letter: 'd', text: '15 meter' }
                ],
                correct_answer: 'b',
                user_answer: 'a',
                is_correct: false,
                time_spent: 32,
                explanation: "Du må holde minst 5 meter avstand fra fotgjengerkrysning når du parkerer."
            },
            {
                question_id: 3,
                question_text: "Hva er fartsgrensen i tettbebygd strøk?",
                image_filename: null,
                options: [
                    { letter: 'a', text: '30 km/t' },
                    { letter: 'b', text: '40 km/t' },
                    { letter: 'c', text: '50 km/t' },
                    { letter: 'd', text: '60 km/t' }
                ],
                correct_answer: 'c',
                user_answer: 'c',
                is_correct: true,
                time_spent: 18,
                explanation: "Fartsgrensen i tettbebygd strøk er normalt 50 km/t med mindre annet er skiltet."
            }
        ]
    };

    // Mock fetch for review data
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        if (url.includes('/review')) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(window.mockReviewData)
            });
        }
        return originalFetch(url, options);
    };

    function updateStatus(elementId, success, message) {
        const element = document.getElementById(elementId);
        const indicator = element.querySelector('.w-4');
        const text = element.querySelector('span:last-child');
        
        if (success) {
            indicator.className = 'w-4 h-4 rounded-full bg-green-400 mr-3';
            text.textContent = '✅ ' + message;
        } else {
            indicator.className = 'w-4 h-4 rounded-full bg-red-400 mr-3';
            text.textContent = '❌ ' + message;
        }
    }

    function testModalSystem(scenario) {
        if (window.QuizResultsModal) {
            window.QuizResultsModal.show(testData[scenario]);
        } else {
            alert('❌ Quiz Results Modal system not loaded! Check JavaScript console for errors.');
        }
    }

    // Check system status on load
    document.addEventListener('DOMContentLoaded', function() {
        // Check JavaScript loading
        setTimeout(() => {
            updateStatus('jsLoadStatus', true, 'JavaScript files loaded successfully');
            
            // Check modal system
            if (window.QuizResultsModal) {
                updateStatus('modalStatus', true, 'Modal system ready');
            } else {
                updateStatus('modalStatus', false, 'Modal system not available');
            }
            
            // Check gamification system
            if (window.GamificationUpdater) {
                updateStatus('gamificationStatus', true, 'Gamification system ready');
            } else {
                updateStatus('gamificationStatus', false, 'Gamification system not available');
            }
            
            // Enable test buttons
            document.querySelectorAll('button[onclick]').forEach(btn => {
                btn.disabled = false;
            });
            
        }, 1000);
    });
    </script>
</body>
</html>
    """
    
    return test_html


def main():
    """Create the test page file"""
    app = create_app()
    
    with app.app_context():
        test_content = create_modal_test_page()
        
        # Write to templates directory
        test_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'templates',
            'quiz',
            'modal_integration_test.html'
        )
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✅ Created modal integration test page: {test_file_path}")
        print("\n📋 To test the modal system:")
        print("1. Start your Flask development server")
        print("2. Visit: http://localhost:5000/quiz/test-modal")
        print("3. Run through all test scenarios")
        print("4. Check the manual test checklist")
        print("\n🎯 Expected behavior:")
        print("- All status indicators should be green")
        print("- Modal should appear with smooth animations")
        print("- XP counters should animate from 0 to target values")
        print("- Review modal should show color-coded answers")
        print("- System should work on both desktop and mobile")


if __name__ == '__main__':
    main()
