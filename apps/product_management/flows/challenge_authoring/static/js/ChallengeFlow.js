/**
 * Main challenge creation flow class.
 * Combines core functionality with bounty management and adds:
 * - Form submission
 * - Progress management
 * - Error handling
 * - Utility functions
 */

import { ChallengeFlowBounties } from './ChallengeFlowBounties';

export class ChallengeFlow extends ChallengeFlowBounties {
    constructor() {
        super();
        this.restoreProgress();
        this.startAutoSave();
    }

    /**
     * Extends core event binding
     */
    bindEvents() {
        super.bindEvents();
        
        // Form submission
        if (this.publishBtn) {
            this.publishBtn.addEventListener('click', (e) => this.handleSubmit(e));
        }
    }

    /**
     * Handles form submission
     */
    async handleSubmit(e) {
        e.preventDefault();
        
        try {
            const errors = this.validateStep(5);
            if (errors.length > 0) {
                this.showValidationErrors(errors);
                return;
            }

            const formData = new FormData(this.form);

            // Add bounty formset data
            this.bounties.forEach((bounty, index) => {
                formData.append(`bounty-${index}-title`, bounty.title);
                formData.append(`bounty-${index}-description`, bounty.description);
                formData.append(`bounty-${index}-points`, bounty.points);
                formData.append(`bounty-${index}-skill`, bounty.skill);
                formData.append(`bounty-${index}-expertise_ids`, bounty.expertise_ids);
            });

            // Django formset management form
            formData.append('bounty-TOTAL_FORMS', this.bounties.length.toString());
            formData.append('bounty-INITIAL_FORMS', '0');
            formData.append('bounty-MIN_NUM_FORMS', '1');
            formData.append('bounty-MAX_NUM_FORMS', '10');

            const response = await fetch(this.endpoints.submit, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const data = await response.json();

            if (data.status === 'success') {
                localStorage.removeItem('challengeProgress');
                window.location.href = data.redirect_url;
            } else {
                this.showValidationErrors(this.formatServerErrors(data.errors));
            }
        } catch (error) {
            this.handleError('Submission failed', error);
        }
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
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.challengeFlow = new ChallengeFlow();
        log.info('Challenge Flow mounted');
    } catch (error) {
        log.error('Init failed:', error);
        const errorContainer = document.createElement('div');
        errorContainer.className = 'error-message';
        errorContainer.textContent = 'Failed to initialize challenge flow. Please refresh.';
        document.body.prepend(errorContainer);
    }
});
