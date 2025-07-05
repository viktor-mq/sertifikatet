 (function () { 'use strict';
    //Javascript for marketing section
    // Marketing section JavaScript - keep all existing functionality
    let currentEmailId = null;

    function openTemplatesModal() {
        document.getElementById('templatesModal').style.display = 'flex';
        // Load templates content via AJAX
        fetch('/admin/marketing-templates')
            .then(response => response.text())
            .then(html => {
                // Extract content from the response
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const content = doc.querySelector('.container-fluid');
                if (content) {
                    document.getElementById('templatesContent').innerHTML = content.innerHTML;
                }
            })
            .catch(error => {
                document.getElementById('templatesContent').innerHTML = '<p>Error loading templates.</p>';
            });
    }

    function closeTemplatesModal() {
        document.getElementById('templatesModal').style.display = 'none';
    }

    function sendEmail(emailId) {
        currentEmailId = emailId;
        
        // Get recipient count
        fetch(`/admin/api/marketing-recipients?email_id=${emailId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('recipientCount').innerHTML = 
                    `<p><strong>Recipients:</strong> ${data.count} users will receive this email</p>`;
                
                document.getElementById('sendEmailModal').style.display = 'flex';
            });
    }

    function closeSendEmailModal() {
        document.getElementById('sendEmailModal').style.display = 'none';
    }

    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === document.getElementById('templatesModal')) {
            closeTemplatesModal();
        }
        if (event.target === document.getElementById('sendEmailModal')) {
            closeSendEmailModal();
        }
    });

    function initializeMarketing() {
        console.log('Marketing section initialized');
        
        // Fix display issue - ensure marketing section is visible
        const marketingSection = document.getElementById('marketingSection');
        if (marketingSection) {
            marketingSection.style.display = 'block';
            console.log('Marketing section display set to block');
        } else {
            console.error('Marketing section not found!');
        }
    }

    // Expose only the functions needed outside this module
    window.openTemplatesModal = openTemplatesModal;
    window.closeTemplatesModal = closeTemplatesModal;
    window.sendEmail = sendEmail;
    window.closeSendEmailModal = closeSendEmailModal;
    window.initializeMarketing = initializeMarketing;

    // Initialize event listeners when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Set up confirm send button event listener
        const confirmSendBtn = document.getElementById('confirmSend');
        if (confirmSendBtn) {
            confirmSendBtn.addEventListener('click', function() {
                if (currentEmailId) {
                    // Show loading state
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
                    this.disabled = true;
                    
                    // Send the email
                    fetch(`/admin/api/marketing-send`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({email_id: currentEmailId})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            closeSendEmailModal();
                            // Refresh the marketing section
                            if (typeof showSection === 'function') {
                                showSection('marketing');
                            }
                        } else {
                            alert('Error sending email: ' + data.error);
                            this.innerHTML = 'Send Now';
                            this.disabled = false;
                        }
                    })
                    .catch(error => {
                        alert('Error sending email: ' + error);
                        this.innerHTML = 'Send Now';
                        this.disabled = false;
                    });
                }
            });
        }
    });
// Expose only the functions needed outside this module
window.openTemplatesModal    = openTemplatesModal;
window.closeTemplatesModal   = closeTemplatesModal;
window.sendEmail             = sendEmail;
window.closeSendEmailModal   = closeSendEmailModal;
window.initializeMarketing   = initializeMarketing;
})();