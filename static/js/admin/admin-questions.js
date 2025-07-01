/**
 * Admin Questions & Content Management JavaScript
 * Enhanced questions management functionality
 */

(function() {
    'use strict';

    // Check if we're on a page with the questions section
    if (!document.getElementById('questionsSection')) {
        console.log('[Questions] Section not found, skipping initialization');
        return; // Exit early if not on questions page
    }

    console.log('[Questions] Initializing questions section JavaScript');

    // Questions management state
    let questionsCurrentPage = 1;
    let questionsPerPage = 20;
    let questionsSortBy = 'created_at';
    let questionsSortOrder = 'desc';
    let questionsSearchTimeout;

    // Initialize Questions Section
    document.addEventListener('DOMContentLoaded', function() {
        if (document.getElementById('questionsSection')) {
            initializeQuestionsSection();
        }
    });

    function initializeQuestionsSection() {
        // Initialize question management
        initializeQuestionFilters();
        initializeQuestionSorting();
        
        console.log('[Questions] Section initialized');
    }

    function initializeQuestionFilters() {
        // Add question filter functionality here if needed
        console.log('[Questions] Filters initialized');
    }

    function initializeQuestionSorting() {
        // Add question sorting functionality here if needed
        console.log('[Questions] Sorting initialized');
    }

    // Make functions available globally for onclick handlers
    window.QuestionsManager = {
        // Add question management functions here
    };

    console.log('[Questions] JavaScript loaded successfully');

})(); // End of IIFE
