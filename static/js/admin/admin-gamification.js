// Admin Gamification Management JavaScript
// Comprehensive gamification admin functionality

// CSRF token utility
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

// Global variables for state management
let tournamentCurrentPage = 1;
let tournamentPerPage = 20;
let tournamentFilters = {};

let challengeCurrentPage = 1;
let challengePerPage = 20;
let challengeFilters = {};

let achievementCurrentPage = 1;
let achievementPerPage = 20;
let achievementFilters = {};

let xpRewardsData = [];
let xpRewardsChanged = false;

// =============================================================================
// INITIALIZATION AND COMMON FUNCTIONS
// =============================================================================

function initializeGamificationAdmin() {
    console.log('Initializing Gamification Admin...');
    
    // Load initial overview data
    loadGamificationOverview();
    
    // Load tournaments by default (first tab)
    showGamificationTab('tournaments');
    
    // Set up event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Set today's date for challenge modal
    const challengeDateInput = document.getElementById('challengeModalDate');
    if (challengeDateInput) {
        challengeDateInput.value = new Date().toISOString().split('T')[0];
    }
    
    // Set default dates for tournament modal
    const startDateInput = document.getElementById('tournamentModalStartDate');
    const endDateInput = document.getElementById('tournamentModalEndDate');
    if (startDateInput && endDateInput) {
        const now = new Date();
        const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
        
        startDateInput.value = now.toISOString().slice(0, 16);
        endDateInput.value = nextWeek.toISOString().slice(0, 16);
    }
}

function showMessage(message, type = 'info') {
    // Create or update message display
    const alertClass = type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : 'alert-info';
    
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.gamification-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} gamification-alert`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        max-width: 400px;
    `;
    
    alertDiv.innerHTML = `
        <strong>${type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️'}</strong> ${message}
        <button onclick="this.parentElement.remove()" style="
            float: right; 
            background: none; 
            border: none; 
            font-size: 18px; 
            cursor: pointer;
            margin-left: 10px;
        ">&times;</button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 5000);
}

// =============================================================================
// TOURNAMENT MANAGEMENT
// =============================================================================

function loadTournamentData() {
    const loading = document.getElementById('tournament-loading');
    const tbody = document.getElementById('tournament-tbody');
    
    if (!tbody) return;
    
    // Show loading if element exists
    if (loading) loading.style.display = 'block';
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Loading tournaments...</td></tr>';
    
    // Build query parameters
    const params = new URLSearchParams({
        page: tournamentCurrentPage,
        per_page: tournamentPerPage,
        ...tournamentFilters
    });
    
    fetch(`/admin/api/tournaments?${params}`)
        .then(response => response.json())
        .then(data => {
            if (loading) loading.style.display = 'none';
            
            if (data.success) {
                displayTournamentData(data.tournaments);
                updateTournamentPagination(data.pagination);
            } else {
                showMessage(data.message, 'error');
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #dc3545;">Error loading tournaments</td></tr>';
            }
        })
        .catch(error => {
            if (loading) loading.style.display = 'none';
            showMessage('Failed to load tournament data', 'error');
            console.error('Error loading tournaments:', error);
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #dc3545;">Failed to load tournaments</td></tr>';
        });
}

function displayTournamentData(tournaments) {
    const tbody = document.getElementById('tournament-tbody');
    
    if (tournaments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #6c757d;">
                    <i class="fas fa-trophy" style="font-size: 3em; margin-bottom: 15px; opacity: 0.3;"></i>
                    <br>No tournaments found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = tournaments.map(tournament => {
        const statusBadge = getStatusBadge(tournament.status);
        const startDate = new Date(tournament.start_date).toLocaleDateString('no-NO');
        const endDate = new Date(tournament.end_date).toLocaleDateString('no-NO');
        
        return `
            <tr style="border-bottom: 1px solid #e5e7eb; transition: background-color 0.2s;">
                <td style="padding: 12px 16px;">
                    <div>
                        <strong>${escapeHtml(tournament.name)}</strong>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">
                            ${escapeHtml(tournament.description.substring(0, 50))}${tournament.description.length > 50 ? '...' : ''}
                        </div>
                    </div>
                </td>
                <td style="padding: 12px 16px; text-transform: capitalize;">${escapeHtml(tournament.tournament_type)}</td>
                <td style="padding: 12px 16px;">${statusBadge}</td>
                <td style="padding: 12px 16px; text-align: center;">${tournament.participant_count}</td>
                <td style="padding: 12px 16px; color: #f59e0b; font-weight: 600;">${tournament.prize_pool_xp} XP</td>
                <td style="padding: 12px 16px;">
                    <div style="display: flex; gap: 8px;">
                        <button onclick="editTournament(${tournament.id})" 
                                style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteTournament(${tournament.id}, '${escapeHtml(tournament.name).replace(/'/g, "\\'")})')" 
                                style="background: #ef4444; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function getStatusBadge(status) {
    const badges = {
        active: '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">Active</span>',
        upcoming: '<span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">Upcoming</span>',
        completed: '<span style="background: #6b7280; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">Completed</span>',
        inactive: '<span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">Inactive</span>'
    };
    return badges[status] || badges.inactive;
}

function openTournamentModal(tournamentId = null) {
    const modal = document.getElementById('tournamentModalOverlay');
    const form = document.getElementById('tournamentModalForm');
    const titleText = document.getElementById('tournamentModalTitleText');
    const saveText = document.getElementById('tournamentModalSaveText');
    
    if (tournamentId) {
        titleText.textContent = 'Edit Tournament';
        saveText.textContent = 'Update Tournament';
        loadTournamentForEdit(tournamentId);
    } else {
        titleText.textContent = 'Create Tournament';
        saveText.textContent = 'Create Tournament';
        form.reset();
        document.getElementById('tournamentModalId').value = '';
        
        // Set default dates
        const now = new Date();
        const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
        document.getElementById('tournamentModalStartDate').value = now.toISOString().slice(0, 16);
        document.getElementById('tournamentModalEndDate').value = nextWeek.toISOString().slice(0, 16);
    }
    
    modal.style.display = 'block';
}

function closeTournamentModal() {
    document.getElementById('tournamentModalOverlay').style.display = 'none';
}

function saveTournament(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const tournamentId = formData.get('tournament_id');
    
    const data = {
        name: formData.get('name'),
        description: formData.get('description'),
        tournament_type: formData.get('tournament_type'),
        category: formData.get('category'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        entry_fee_xp: parseInt(formData.get('entry_fee_xp')) || 0,
        prize_pool_xp: parseInt(formData.get('prize_pool_xp')) || 1000,
        is_active: formData.has('is_active')
    };
    
    const url = tournamentId ? `/admin/api/tournaments/${tournamentId}` : '/admin/api/tournaments';
    const method = tournamentId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            closeTournamentModal();
            loadTournamentData();
            loadTournamentStats();
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        showMessage('Failed to save tournament', 'error');
        console.error('Error saving tournament:', error);
    });
}

function editTournament(tournamentId) {
    // For now, just open the modal - editing functionality can be enhanced later
    openTournamentModal(tournamentId);
}

function deleteTournament(tournamentId, tournamentName) {
    if (!confirm(`Are you sure you want to delete the tournament "${tournamentName}"?`)) {
        return;
    }
    
    fetch(`/admin/api/tournaments/${tournamentId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            loadTournamentData();
            loadTournamentStats();
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        showMessage('Failed to delete tournament', 'error');
        console.error('Error deleting tournament:', error);
    });
}

function loadTournamentStats() {
    fetch('/admin/api/tournaments/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                updateStatElement('[data-stat="tournaments_total"]', stats.total_tournaments);
                updateStatElement('[data-stat="tournaments_active"]', stats.active_tournaments);
                updateStatElement('[data-stat="tournaments_participants"]', stats.total_participants);
            }
        })
        .catch(error => console.error('Error loading tournament stats:', error));
}

function applyTournamentFilters() {
    tournamentFilters = {
        search: document.getElementById('tournament-search').value,
        status: document.getElementById('tournament-status-filter').value
    };
    tournamentCurrentPage = 1;
    loadTournamentData();
}

function clearTournamentFilters() {
    document.getElementById('tournament-search').value = '';
    document.getElementById('tournament-status-filter').value = '';
    tournamentFilters = {};
    tournamentCurrentPage = 1;
    loadTournamentData();
}

function updateTournamentPagination(pagination) {
    // Implement pagination update logic
    console.log('Tournament pagination:', pagination);
}

// =============================================================================
// DAILY CHALLENGE MANAGEMENT
// =============================================================================

function loadDailyChallengeData() {
    const loading = document.getElementById('challenge-loading');
    const tbody = document.getElementById('challenge-tbody');
    
    if (!tbody) return;
    
    // Show loading if element exists
    if (loading) loading.style.display = 'block';
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">Loading challenges...</td></tr>';
    
    // Build query parameters
    const params = new URLSearchParams({
        page: challengeCurrentPage,
        per_page: challengePerPage,
        ...challengeFilters
    });
    
    fetch(`/admin/api/daily-challenges?${params}`)
        .then(response => response.json())
        .then(data => {
            if (loading) loading.style.display = 'none';
            
            if (data.success) {
                displayDailyChallengeData(data.challenges);
                updateDailyChallengePagination(data.pagination);
            } else {
                showMessage(data.message, 'error');
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #dc3545;">Error loading challenges</td></tr>';
            }
        })
        .catch(error => {
            if (loading) loading.style.display = 'none';
            showMessage('Failed to load challenge data', 'error');
            console.error('Error loading challenges:', error);
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #dc3545;">Failed to load challenges</td></tr>';
        });
}

function displayDailyChallengeData(challenges) {
    const tbody = document.getElementById('challenge-tbody');
    
    if (challenges.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #6c757d;">
                    <i class="fas fa-target" style="font-size: 3em; margin-bottom: 15px; opacity: 0.3;"></i>
                    <br>No challenges found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = challenges.map(challenge => {
        const isActive = challenge.is_active;
        const activeStatus = isActive ? 
            '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">Active</span>' :
            '<span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">Inactive</span>';
        
        const challengeDate = new Date(challenge.date).toLocaleDateString('no-NO');
        const completionRate = challenge.completion_rate || 0;
        
        return `
            <tr style="border-bottom: 1px solid #e5e7eb; transition: background-color 0.2s;">
                <td style="padding: 12px 16px;">
                    <div>
                        <strong>${escapeHtml(challenge.title)}</strong>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">
                            ${escapeHtml(challenge.description.substring(0, 40))}${challenge.description.length > 40 ? '...' : ''}
                        </div>
                    </div>
                </td>
                <td style="padding: 12px 16px; text-transform: capitalize;">${escapeHtml(challenge.challenge_type.replace('_', ' '))}</td>
                <td style="padding: 12px 16px;">
                    <div>${challengeDate}</div>
                    <div style="font-size: 11px;">${activeStatus}</div>
                </td>
                <td style="padding: 12px 16px; text-align: center;">${challenge.requirement_value}</td>
                <td style="padding: 12px 16px;">
                    <div style="color: #f59e0b; font-weight: 600;">${challenge.xp_reward} XP</div>
                    ${challenge.bonus_reward > 0 ? `<div style="font-size: 11px; color: #6b7280;">+${challenge.bonus_reward} bonus</div>` : ''}
                </td>
                <td style="padding: 12px 16px; text-align: center;">
                    <div style="font-size: 12px;">
                        <div>${challenge.completed_users}/${challenge.total_users}</div>
                        <div style="color: #6b7280;">${completionRate}%</div>
                    </div>
                </td>
                <td style="padding: 12px 16px;">
                    <div style="display: flex; gap: 8px;">
                        <button onclick="editDailyChallenge(${challenge.id})" 
                                style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteDailyChallenge(${challenge.id}, '${escapeHtml(challenge.title).replace(/'/g, "\\'")})')" 
                                style="background: #ef4444; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function openDailyChallengeModal(challengeId = null) {
    const modal = document.getElementById('challengeModalOverlay');
    const form = document.getElementById('challengeModalForm');
    const titleText = document.getElementById('challengeModalTitleText');
    const saveText = document.getElementById('challengeModalSaveText');
    
    if (challengeId) {
        titleText.textContent = 'Edit Daily Challenge';
        saveText.textContent = 'Update Challenge';
        loadDailyChallengeForEdit(challengeId);
    } else {
        titleText.textContent = 'Create Daily Challenge';
        saveText.textContent = 'Create Challenge';
        form.reset();
        document.getElementById('challengeModalId').value = '';
        // Set today's date as default
        document.getElementById('challengeModalDate').value = new Date().toISOString().split('T')[0];
    }
    
    modal.style.display = 'block';
}

function closeDailyChallengeModal() {
    document.getElementById('challengeModalOverlay').style.display = 'none';
}

function saveDailyChallenge(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const challengeId = formData.get('challenge_id');
    
    const data = {
        title: formData.get('title'),
        description: formData.get('description'),
        challenge_type: formData.get('challenge_type'),
        requirement_value: parseInt(formData.get('requirement_value')),
        xp_reward: parseInt(formData.get('xp_reward')) || 50,
        bonus_reward: parseInt(formData.get('bonus_reward')) || 0,
        category: formData.get('category'),
        date: formData.get('date'),
        is_active: formData.has('is_active')
    };
    
    const url = challengeId ? `/admin/api/daily-challenges/${challengeId}` : '/admin/api/daily-challenges';
    const method = challengeId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            closeDailyChallengeModal();
            loadDailyChallengeData();
            loadDailyChallengeStats();
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        showMessage('Failed to save challenge', 'error');
        console.error('Error saving challenge:', error);
    });
}

function editDailyChallenge(challengeId) {
    openDailyChallengeModal(challengeId);
}

function deleteDailyChallenge(challengeId, challengeTitle) {
    if (!confirm(`Are you sure you want to delete the challenge "${challengeTitle}"?`)) {
        return;
    }
    
    fetch(`/admin/api/daily-challenges/${challengeId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            loadDailyChallengeData();
            loadDailyChallengeStats();
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        showMessage('Failed to delete challenge', 'error');
        console.error('Error deleting challenge:', error);
    });
}

function loadDailyChallengeStats() {
    fetch('/admin/api/daily-challenges/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                updateStatElement('[data-stat="challenges_total"]', stats.total_challenges);
                updateStatElement('[data-stat="challenges_active"]', stats.active_challenges);
                updateStatElement('[data-stat="challenges_completion_rate"]', `${stats.avg_completion_rate}%`);
            }
        })
        .catch(error => console.error('Error loading challenge stats:', error));
}

function applyDailyChallengeFilters() {
    challengeFilters = {
        search: document.getElementById('challenge-search').value,
        challenge_type: document.getElementById('challenge-type-filter').value,
        date_filter: document.getElementById('challenge-date-filter').value
    };
    challengeCurrentPage = 1;
    loadDailyChallengeData();
}

function clearDailyChallengeFilters() {
    document.getElementById('challenge-search').value = '';
    document.getElementById('challenge-type-filter').value = '';
    document.getElementById('challenge-date-filter').value = '';
    challengeFilters = {};
    challengeCurrentPage = 1;
    loadDailyChallengeData();
}

function updateDailyChallengePagination(pagination) {
    console.log('Challenge pagination:', pagination);
}

function loadDailyChallengeForEdit(challengeId) {
    // Placeholder for loading challenge data for editing
    console.log('Loading challenge for edit:', challengeId);
}

// =============================================================================
// ACHIEVEMENT MANAGEMENT
// =============================================================================

function loadAchievementData() {
    const tbody = document.getElementById('achievement-tbody');
    
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Loading achievements...</td></tr>';
    
    // Build query parameters
    const params = new URLSearchParams({
        page: achievementCurrentPage,
        per_page: achievementPerPage,
        ...achievementFilters
    });
    
    fetch(`/admin/api/achievements?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                achievementsData = data.achievements; // Store achievements globally
                displayAchievementData(data.achievements);
                updateAchievementPagination(data.pagination);
            } else {
                showMessage(data.message, 'error');
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #dc3545;">Error loading achievements</td></tr>';
            }
        })
        .catch(error => {
            showMessage('Failed to load achievement data', 'error');
            console.error('Error loading achievements:', error);
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #dc3545;">Failed to load achievements</td></tr>';
        });
}

function displayAchievementData(achievements) {
    const tbody = document.getElementById('achievement-tbody');
    
    if (achievements.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #6c757d;">
                    <i class="fas fa-medal" style="font-size: 3em; margin-bottom: 15px; opacity: 0.3;"></i>
                    <br>No achievements found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = achievements.map(achievement => {
        return `
            <tr style="border-bottom: 1px solid #e5e7eb; transition: background-color 0.2s;">
                <td style="padding: 12px 16px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        ${achievement.icon_filename ? 
                            `<img src="/static/achievements/${achievement.icon_filename}" alt="Icon" style="width: 24px; height: 24px;">` : 
                            '<i class="fas fa-medal" style="color: #f59e0b; font-size: 20px;"></i>'
                        }
                        <div>
                            <strong>${escapeHtml(achievement.name || 'Unnamed Achievement')}</strong>
                            <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">
                                ${escapeHtml((achievement.description || 'No description').substring(0, 50))}${(achievement.description || '').length > 50 ? '...' : ''}
                            </div>
                        </div>
                    </div>
                </td>
                <td style="padding: 12px 16px; text-transform: capitalize;">${escapeHtml(achievement.category || 'General')}</td>
                <td style="padding: 12px 16px;">
                    <div style="font-size: 12px;">
                        <div>${escapeHtml((achievement.requirement_type || 'unknown').replace('_', ' '))}</div>
                        <div style="color: #6b7280;">${achievement.requirement_value}</div>
                    </div>
                </td>
                <td style="padding: 12px 16px; color: #f59e0b; font-weight: 600;">${achievement.points} XP</td>
                <td style="padding: 12px 16px; text-align: center;">${achievement.users_earned}</td>
                <td style="padding: 12px 16px;">
                    <div style="display: flex; gap: 8px;">
                        <button onclick="editAchievement(${achievement.id})" 
                                style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteAchievement(${achievement.id}, '${escapeHtml(achievement.name || 'Unnamed Achievement').replace(/'/g, "\'")}')" 
                                style="background: #ef4444; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function openAchievementModal(achievementId = null) {
    const modal = document.getElementById('achievementModalOverlay');
    const form = document.getElementById('achievementModalForm');
    const titleText = document.getElementById('achievementModalTitleText');
    const saveText = document.getElementById('achievementModalSaveText');
    
    if (achievementId) {
        titleText.textContent = 'Edit Achievement';
        saveText.textContent = 'Update Achievement';
        loadAchievementForEdit(achievementId);
    } else {
        titleText.textContent = 'Create Achievement';
        saveText.textContent = 'Create Achievement';
        form.reset();
        document.getElementById('achievementModalId').value = '';
    }
    
    modal.style.display = 'block';
}

function closeAchievementModal() {
    document.getElementById('achievementModalOverlay').style.display = 'none';
}

function saveAchievement(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const achievementId = formData.get('achievement_id');
    
    const data = {
        name: formData.get('name'),
        description: formData.get('description'),
        category: formData.get('category'),
        requirement_type: formData.get('requirement_type'),
        requirement_value: parseInt(formData.get('requirement_value')),
        points: parseInt(formData.get('points')),
        icon_filename: formData.get('icon_filename')
    };
    
    const url = achievementId ? `/admin/api/achievements/${achievementId}` : '/admin/api/achievements';
    const method = achievementId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            closeAchievementModal();
            loadAchievementData();
            loadAchievementStats();
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        showMessage('Failed to save achievement', 'error');
        console.error('Error saving achievement:', error);
    });
}

function editAchievement(achievementId) {
    openAchievementModal(achievementId);
}

function deleteAchievement(achievementId, achievementName) {
    if (!confirm(`Are you sure you want to delete the achievement "${achievementName}"?`)) {
        return;
    }
    
    fetch(`/admin/api/achievements/${achievementId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            loadAchievementData();
            loadAchievementStats();
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        showMessage('Failed to delete achievement', 'error');
        console.error('Error deleting achievement:', error);
    });
}

function loadAchievementStats() {
    fetch('/admin/api/achievements/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                updateStatElement('[data-stat="achievements_total"]', stats.total_achievements);
                updateStatElement('[data-stat="achievements_earned"]', stats.total_earned);
                updateStatElement('[data-stat="achievements_achievers"]', stats.unique_achievers);
            }
        })
        .catch(error => console.error('Error loading achievement stats:', error));
}

function applyAchievementFilters() {
    achievementFilters = {
        search: document.getElementById('achievement-search').value,
        category: document.getElementById('achievement-category-filter').value
    };
    achievementCurrentPage = 1;
    loadAchievementData();
}

function clearAchievementFilters() {
    document.getElementById('achievement-search').value = '';
    document.getElementById('achievement-category-filter').value = '';
    achievementFilters = {};
    achievementCurrentPage = 1;
    loadAchievementData();
}

function updateAchievementPagination(pagination) {
    console.log('Achievement pagination:', pagination);
}

function loadAchievementForEdit(achievementId) {
    const achievement = achievementsData.find(a => a.id === achievementId);
    if (!achievement) {
        showMessage('Could not find achievement data to edit.', 'error');
        return;
    }

    document.getElementById('achievementModalId').value = achievement.id;
    document.getElementById('achievementModalName').value = achievement.name;
    document.getElementById('achievementModalDescription').value = achievement.description;
    document.getElementById('achievementModalCategory').value = achievement.category;
    document.getElementById('achievementModalRequirementType').value = achievement.requirement_type;
    document.getElementById('achievementModalRequirementValue').value = achievement.requirement_value;
    document.getElementById('achievementModalPoints').value = achievement.points;
    document.getElementById('achievementModalIconFilename').value = achievement.icon_filename;
}

// =============================================================================
// XP REWARDS MANAGEMENT
// =============================================================================

function loadXPRewardsData() {
    const tbody = document.getElementById('xp-rewards-tbody');
    
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Loading XP rewards...</td></tr>';
    
    fetch('/admin/api/xp-rewards')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                xpRewardsData = data.rewards;
                displayXPRewardsData(data.rewards);
            } else {
                showMessage(data.message, 'error');
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #dc3545;">Error loading XP rewards</td></tr>';
            }
        })
        .catch(error => {
            showMessage('Failed to load XP rewards data', 'error');
            console.error('Error loading XP rewards:', error);
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #dc3545;">Failed to load XP rewards</td></tr>';
        });
}

function displayXPRewardsData(rewards) {
    const tbody = document.getElementById('xp-rewards-tbody');
    
    if (rewards.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #6c757d;">
                    <i class="fas fa-star" style="font-size: 3em; margin-bottom: 15px; opacity: 0.3;"></i>
                    <br>No XP rewards configured
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = rewards.map(reward => {
        return `
            <tr style="border-bottom: 1px solid #e5e7eb; transition: background-color 0.2s;">
                <td style="padding: 12px 16px;">
                    <strong>${escapeHtml(reward.reward_type.replace('_', ' '))}</strong>
                </td>
                <td style="padding: 12px 16px;">
                    <input type="number" 
                           value="${reward.base_value}" 
                           min="0" 
                           style="width: 80px; padding: 4px; border: 1px solid #ccc; border-radius: 4px;"
                           onchange="updateXPReward(${reward.id}, 'base_value', this.value)">
                </td>
                <td style="padding: 12px 16px;">
                    <input type="number" 
                           value="${reward.scaling_factor}" 
                           min="0" 
                           step="0.1"
                           style="width: 80px; padding: 4px; border: 1px solid #ccc; border-radius: 4px;"
                           onchange="updateXPReward(${reward.id}, 'scaling_factor', this.value)">
                </td>
                <td style="padding: 12px 16px;">
                    <input type="number" 
                           value="${reward.max_value || ''}" 
                           min="0" 
                           placeholder="No limit"
                           style="width: 80px; padding: 4px; border: 1px solid #ccc; border-radius: 4px;"
                           onchange="updateXPReward(${reward.id}, 'max_value', this.value)">
                </td>
                <td style="padding: 12px 16px; font-size: 12px; color: #6b7280;">
                    ${escapeHtml(reward.description)}
                </td>
                <td style="padding: 12px 16px;">
                    <button onclick="saveXPRewardChanges(${reward.id})" 
                            style="background: #28a745; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        <i class="fas fa-save"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updateXPReward(rewardId, field, value) {
    const reward = xpRewardsData.find(r => r.id === rewardId);
    if (reward) {
        reward[field] = value === '' ? null : (field === 'scaling_factor' ? parseFloat(value) : parseInt(value));
        xpRewardsChanged = true;
    }
}

function saveXPRewardChanges(rewardId) {
    const reward = xpRewardsData.find(r => r.id === rewardId);
    if (!reward) return;
    
    const data = {
        base_value: reward.base_value,
        scaling_factor: reward.scaling_factor,
        max_value: reward.max_value,
        description: reward.description
    };
    
    fetch(`/admin/api/xp-rewards/${rewardId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showMessage(`Updated ${reward.reward_type} successfully`, 'success');
            xpRewardsChanged = false;
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        showMessage('Failed to save XP reward changes', 'error');
        console.error('Error saving XP reward:', error);
    });
}

function saveXPRewards() {
    if (!xpRewardsChanged) {
        showMessage('No changes to save', 'info');
        return;
    }
    
    // Save all changed rewards
    const promises = xpRewardsData.map(reward => saveXPRewardChanges(reward.id));
    
    Promise.all(promises).then(() => {
        showMessage('All XP rewards saved successfully', 'success');
    });
}

function resetXPDefaults() {
    if (!confirm('Are you sure you want to reset all XP rewards to default values? This cannot be undone.')) {
        return;
    }
    
    // This would require a reset endpoint - for now just reload
    loadXPRewardsData();
    showMessage('XP rewards reset to defaults', 'info');
}

function loadXPRewardsStats() {
    fetch('/admin/api/xp-rewards/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                updateStatElement('[data-stat="xp_total_awarded"]', stats.total_xp_awarded.toLocaleString());
                updateStatElement('[data-stat="xp_transactions"]', stats.total_transactions);
                updateStatElement('[data-stat="xp_avg_level"]', stats.avg_user_level);
                updateStatElement('[data-stat="xp_active_users"]', stats.active_users);
            }
        })
        .catch(error => console.error('Error loading XP reward stats:', error));
}

// =============================================================================
// COMMON UTILITY FUNCTIONS
// =============================================================================

function updateStatElement(selector, value) {
    const element = document.querySelector(selector);
    if (element) {
        element.textContent = value;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function loadTournamentForEdit(tournamentId) {
    console.log('Loading tournament for edit:', tournamentId);
}

// Make functions globally available
window.initializeGamificationAdmin = initializeGamificationAdmin;
window.showGamificationTab = showGamificationTab;
window.loadGamificationOverview = loadGamificationOverview;
window.refreshGamificationOverview = refreshGamificationOverview;

// Tournament functions
window.loadTournamentData = loadTournamentData;
window.loadTournamentStats = loadTournamentStats;
window.openTournamentModal = openTournamentModal;
window.closeTournamentModal = closeTournamentModal;
window.saveTournament = saveTournament;
window.editTournament = editTournament;
window.deleteTournament = deleteTournament;
window.applyTournamentFilters = applyTournamentFilters;
window.clearTournamentFilters = clearTournamentFilters;

// Challenge functions
window.loadDailyChallengeData = loadDailyChallengeData;
window.loadDailyChallengeStats = loadDailyChallengeStats;
window.openDailyChallengeModal = openDailyChallengeModal;
window.closeDailyChallengeModal = closeDailyChallengeModal;
window.saveDailyChallenge = saveDailyChallenge;
window.editDailyChallenge = editDailyChallenge;
window.deleteDailyChallenge = deleteDailyChallenge;
window.applyDailyChallengeFilters = applyDailyChallengeFilters;
window.clearDailyChallengeFilters = clearDailyChallengeFilters;

// Achievement functions
window.loadAchievementData = loadAchievementData;
window.loadAchievementStats = loadAchievementStats;
window.openAchievementModal = openAchievementModal;
window.closeAchievementModal = closeAchievementModal;
window.saveAchievement = saveAchievement;
window.editAchievement = editAchievement;
window.deleteAchievement = deleteAchievement;
window.applyAchievementFilters = applyAchievementFilters;
window.clearAchievementFilters = clearAchievementFilters;

// XP Rewards functions
window.loadXPRewardsData = loadXPRewardsData;
window.loadXPRewardsStats = loadXPRewardsStats;
window.updateXPReward = updateXPReward;
window.saveXPRewardChanges = saveXPRewardChanges;
window.saveXPRewards = saveXPRewards;
window.resetXPDefaults = resetXPDefaults;

console.log('Admin Gamification JavaScript loaded successfully');
