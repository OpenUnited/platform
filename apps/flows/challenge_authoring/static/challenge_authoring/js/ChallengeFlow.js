/**
 * Main challenge creation flow class.
 * Combines core functionality with bounty management and adds:
 * - Form submission
 * - Progress management
 * - Error handling
 * - Utility functions
 */

import { ChallengeFlowBounties } from './ChallengeFlowBounties.js';

export class ChallengeFlow extends ChallengeFlowBounties {
    constructor() {
        console.log('ChallengeFlow constructor called');
        super();
        this.initializeElements();
        this.bindEvents();
        console.log('ChallengeFlow initialization complete');
    }

    initializeElements() {
        this.form = document.getElementById('challenge-form');
        this.publishBtn = document.querySelector('.btn-primary[type="submit"]');
        this.errorContainer = document.querySelector('.error-container');
        
        console.log('Form found:', !!this.form);
        console.log('Publish button found:', !!this.publishBtn);
    }

    handleBountyAdded(bounty) {
        this.bounties.push(bounty);
        this.updateBountyTable();
        this.saveProgress();
    }

    handleBountyRemoved(index) {
        this.bounties.splice(index, 1);
        this.updateBountyTable();
        this.saveProgress();
    }

    /**
     * Extends core event binding
     */
    bindEvents() {
        super.bindEvents();
        
        if (this.publishBtn) {
            console.log('Binding click handler to save button');
            this.publishBtn.addEventListener('click', (e) => {
                console.log('Save button clicked'); // Debug log
                e.preventDefault();
                e.stopPropagation();
                this.handleSubmit(e);
            });
        } else {
            console.error('Save button not found - check the selector');
        }
    }

    /**
     * Handles form submission
     */
    async handleSubmit(e) {
        if (this.isSubmitting) return; // Prevent multiple submissions
        this.isSubmitting = true;
        
        try {
            const formData = new FormData(this.form);
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                window.location.href = data.redirect_url;
            } else {
                this.showError(data.message || 'Submission failed');
            }
        } catch (error) {
            console.error('Submission error:', error);
            this.showError('An unexpected error occurred');
        } finally {
            this.isSubmitting = false;
        }
        
        return false;
    }

    /**
     * Shows validation errors to user
     */
    showValidationErrors(errors) {
        if (!this.errorContainer) return;
        
        this.errorContainer.innerHTML = errors.map(error => 
            `<div class="text-red-600 text-sm">${this.escapeHtml(error)}</div>`
        ).join('');
        this.errorContainer.classList.remove('hidden');
        
        // Scroll to errors
        this.errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Formats server-side validation errors
     */
    formatServerErrors(errors) {
        const formatted = [];
        
        if (errors.non_field_errors) {
            formatted.push(...errors.non_field_errors);
        }

        Object.entries(errors).forEach(([field, fieldErrors]) => {
            if (field === 'non_field_errors') return;
            
            if (field.startsWith('bounty_')) {
                const [_, index, fieldName] = field.split('_');
                formatted.push(`Bounty ${parseInt(index) + 1} ${fieldName}: ${fieldErrors.join(', ')}`);
            } else {
                formatted.push(`${field}: ${fieldErrors.join(', ')}`);
            }
        });

        return formatted;
    }

    /**
     * Saves current progress to localStorage
     */
    saveProgress() {
        try {
            const data = {
                step: this.currentStep,
                formData: Object.fromEntries(new FormData(this.form)),
                bounties: this.bounties,
                lastSaved: new Date().toISOString()
            };
            localStorage.setItem('challengeProgress', JSON.stringify(data));
            this.log.debug('Progress saved');
        } catch (error) {
            this.log.warn('Failed to save progress', error);
        }
    }

    /**
     * Restores saved progress if available
     */
    restoreProgress() {
        try {
            const saved = localStorage.getItem('challengeProgress');
            if (saved) {
                const data = JSON.parse(saved);
                this.currentStep = data.step;
                this.bounties = data.bounties;
                
                // Restore form data
                Object.entries(data.formData).forEach(([key, value]) => {
                    const input = this.form.querySelector(`[name="${key}"]`);
                    if (input) {
                        if (input.type === 'radio') {
                            this.form.querySelector(`[name="${key}"][value="${value}"]`)?.click();
                        } else {
                            input.value = value;
                        }
                    }
                });

                this.updateStepVisibility();
                this.updateBountyTable();
                this.log.info('Progress restored');
            }
        } catch (error) {
            this.log.warn('Failed to restore progress', error);
        }
    }

    /**
     * Starts auto-save interval
     */
    startAutoSave() {
        setInterval(() => this.saveProgress(), this.autoSaveInterval);
        this.log.info('Auto-save started');
    }

    /**
     * Validates video URL format
     */
    isValidVideoUrl(url) {
        try {
            const urlObj = new URL(url);
            return ['youtube.com', 'youtu.be', 'vimeo.com'].some(domain => 
                urlObj.hostname.includes(domain));
        } catch {
            return false;
        }
    }

    /**
     * Prevents XSS in HTML content
     */
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Optional error display method
    showError(message) {
        // Add your error display logic here
        console.error(message);
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.challengeFlow = new ChallengeFlow();
        console.info('Challenge Flow mounted');
    } catch (error) {
        console.error('Init failed:', error);
        const errorContainer = document.createElement('div');
        errorContainer.className = 'error-message';
        errorContainer.textContent = 'Failed to initialize challenge flow. Please refresh.';
        document.body.prepend(errorContainer);
    }
});
