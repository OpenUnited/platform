/**
 * Handles the 5-step challenge creation process:
 * 1. Choose type (single/multi skill)
 * 2. Add title and description
 * 3. Configure bounties
 * 4. Set status and priority
 * 5. Review summary
 */

const DEBUG = process.env.NODE_ENV !== 'production';
const log = {
    info: (...args) => DEBUG && console.log('[Challenge Flow]:', ...args),
    warn: (...args) => DEBUG && console.warn('[Challenge Flow]:', ...args),
    error: (...args) => console.error('[Challenge Flow]:', ...args),
    debug: (...args) => DEBUG && console.debug('[Challenge Flow]:', ...args),
    table: (data) => DEBUG && console.table(data)
};

class ChallengeFlow {
    constructor() {
        this.currentStep = 1;
        this.bounties = [];
        this.DEBUG = DEBUG;
        this.autoSaveInterval = 30000; // 30 seconds
        
        // Get product slug from the form's data attribute
        const form = document.querySelector('form');
        this.productSlug = form?.dataset.productSlug;
        if (!this.productSlug) {
            throw new Error('Product slug not found on form');
        }

        // Set up API endpoints based on urls.py
        this.endpoints = {
            submit: `/${this.productSlug}/challenge/create/`,
            skills: '/expertise-options/',
            expertise: (skillId) => `/expertise-options/?skill_id=${skillId}`
        };
        
        log.info('Initializing Challenge Flow');
        this.initializeElements();
        this.bindEvents();
        this.restoreProgress();
        this.startAutoSave();
    }

    /**
     * Finds and stores required DOM elements
     */
    initializeElements() {
        try {
            // Step navigation
            this.stepNumbs = document.querySelectorAll('[data-step-numb]');
            this.stepForms = document.querySelectorAll('[data-step-id]');
            this.stepCurrent = document.querySelector('[data-current-step]');
            this.nextButtons = document.querySelectorAll('[data-step-next]');
            this.prevButtons = document.querySelectorAll('[data-step-previous]');
            this.publishBtn = document.querySelector('#publish-challenge-btn');
            
            // Form elements (matching Django form fields)
            this.form = document.querySelector('form');
            this.titleInput = document.querySelector('[name="title"]');
            this.descriptionInput = document.querySelector('[name="description"]');
            this.shortDescriptionInput = document.querySelector('[name="short_description"]');
            this.statusSelect = document.querySelector('[name="status"]');
            this.prioritySelect = document.querySelector('[name="priority"]');
            this.rewardTypeInputs = document.querySelectorAll('[name="reward_type"]');
            this.initiativeSelect = document.querySelector('[name="initiative"]');
            this.productAreaSelect = document.querySelector('[name="product_area"]');
            this.videoUrlInput = document.querySelector('[name="video_url"]');
            
            // Bounty management
            this.bountyArea = document.getElementById('bounty_area');
            this.bountyTableBody = document.getElementById('bounty_table_body');
            this.addBountyButton = document.querySelector('.skills-modal__open');

            // Summary elements
            this.summaryTitle = document.getElementById('summary_title');
            this.summaryDescription = document.getElementById('summary_description');
            this.summaryBountyTable = document.getElementById('summary_bounty_table');
            this.summaryTotalPoints = document.getElementById('summary_total_points');

            // Error display
            this.errorContainer = document.getElementById('validation-errors');

            this.validateRequiredElements();
            log.info('Elements initialized');
        } catch (error) {
            this.handleError('Initialization failed', error);
        }
    }

    /**
     * Validates presence of required DOM elements
     */
    validateRequiredElements() {
        const required = [
            'form',
            '[name="title"]',
            '[name="description"]',
            '[name="status"]',
            '[name="priority"]',
            '[name="reward_type"]',
            '#bounty_area',
            '#validation-errors'
        ];

        const missing = required.filter(selector => 
            !document.querySelector(selector)
        );

        if (missing.length) {
            throw new Error(`Missing required elements: ${missing.join(', ')}`);
        }
    }

    /**
     * Binds all event listeners
     */
    bindEvents() {
        // Navigation
        this.nextButtons.forEach(btn => 
            btn.addEventListener('click', () => this.nextStep()));
        this.prevButtons.forEach(btn => 
            btn.addEventListener('click', () => this.previousStep()));
        
        // Form field changes
        this.form.addEventListener('input', () => this.saveProgress());
        this.form.addEventListener('change', () => this.saveProgress());

        // Bounty management
        if (this.addBountyButton) {
            this.addBountyButton.addEventListener('click', async () => {
                try {
                    const skills = await this.fetchSkillsList();
                    window.showModal(skills);
                } catch (error) {
                    this.handleError('Failed to load skills', error);
                }
            });
        }

        // Bounty events from modal
        document.addEventListener('bountyAdded', 
            (e) => this.handleBountyAdded(e.detail));
        document.addEventListener('bountyRemoved', 
            (e) => this.handleBountyRemoved(e.detail));

        // Form submission
        if (this.publishBtn) {
            this.publishBtn.addEventListener('click', (e) => this.handleSubmit(e));
        }

        log.info('Events bound');
    }

    /**
     * Fetches available skills from server
     */
    async fetchSkillsList() {
        try {
            const response = await fetch(this.endpoints.skills, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            if (!response.ok) throw new Error('Failed to fetch skills');
            const data = await response.json();
            return data.skills;
        } catch (error) {
            this.handleError('Failed to fetch skills', error);
            return [];
        }
    }

    /**
     * Fetches expertise options for a skill
     */
    async fetchExpertiseOptions(skillId) {
        try {
            const response = await fetch(this.endpoints.expertise(skillId), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            if (!response.ok) throw new Error('Failed to fetch expertise options');
            const data = await response.json();
            return data.expertise;
        } catch (error) {
            this.handleError('Failed to fetch expertise options', error);
            return [];
        }
    }

    /**
     * Handles bounty addition from modal
     */
    handleBountyAdded(bounty) {
        const formattedBounty = {
            title: bounty.skill,
            description: bounty.description || '',
            points: bounty.points,
            skill: bounty.skillId,
            expertise_ids: bounty.expertiseIds.join(',')
        };
        
        this.bounties.push(formattedBounty);
        this.bountyArea.classList.remove('hidden');
        this.updateBountyTable();
        this.saveProgress();
        log.info('Bounty added', formattedBounty);
    }

    /**
     * Handles bounty removal
     */
    handleBountyRemoved(index) {
        this.bounties.splice(index, 1);
        this.updateBountyTable();
        this.saveProgress();
        log.info('Bounty removed at index', index);
    }

    /**
     * Updates bounty display table
     */
    updateBountyTable() {
        if (!this.bountyTableBody) return;
        
        this.bountyTableBody.innerHTML = '';
        this.bounties.forEach((bounty, index) => {
            const row = `
                <tr class="border-b border-gray-200">
                    <td class="py-4 pl-4 pr-3 text-sm">
                        <div class="font-medium text-gray-900">${this.escapeHtml(bounty.title)}</div>
                        <div class="text-gray-500">${this.escapeHtml(bounty.description)}</div>
                    </td>
                    <td class="py-4 px-3 text-sm text-center">${bounty.points}</td>
                    <td class="py-4 px-3 text-sm text-right">
                        <button type="button" 
                                onclick="window.challengeFlow.handleBountyRemoved(${index})"
                                class="text-red-600 hover:text-red-900">
                            Remove
                        </button>
                    </td>
                </tr>
            `;
            this.bountyTableBody.insertAdjacentHTML('beforeend', row);
        });

        // Toggle empty state
        if (this.bounties.length === 0) {
            this.bountyArea.classList.add('hidden');
        }
    }

    /**
     * Validates current step
     */
    validateStep(stepNumber) {
        const errors = [];

        switch (stepNumber) {
            case 1:
                const rewardType = document.querySelector('input[name="reward_type"]:checked');
                if (!rewardType) errors.push('Please select a reward type');
                break;

            case 2:
                const title = this.titleInput.value;
                const description = this.descriptionInput.value;
                const shortDesc = this.shortDescriptionInput?.value;
                const videoUrl = this.videoUrlInput?.value;

                if (!title?.trim()) errors.push('Title is required');
                if (title?.length > 255) errors.push('Title must be less than 255 characters');
                
                if (!description?.trim()) errors.push('Description is required');
                
                if (shortDesc && shortDesc.length > 140) {
                    errors.push('Short description must be less than 140 characters');
                }
                
                if (videoUrl && !this.isValidVideoUrl(videoUrl)) {
                    errors.push('Invalid video URL format (must be YouTube or Vimeo)');
                }
                break;

            case 3:
                if (this.bounties.length === 0) {
                    errors.push('At least one bounty is required');
                }
                break;

            case 4:
                const status = this.statusSelect?.value;
                const priority = this.prioritySelect?.value;
                
                if (!status) errors.push('Status is required');
                if (!priority) errors.push('Priority is required');
                break;

            case 5:
                // Final validation before submission
                if (this.bounties.length === 0) {
                    errors.push('At least one bounty is required');
                }
                break;
        }

        return errors;
    }

    /**
     * Checks if a video URL is valid
     */
    isValidVideoUrl(url) {
        // Add your validation logic here
        return true;
    }

    /**
     * Moves to next step if validation passes
     */
    nextStep() {
        const errors = this.validateStep(this.currentStep);
        if (errors.length === 0) {
            this.currentStep = Math.min(this.currentStep + 1, 5);
            this.updateStepVisibility();
            if (this.currentStep === 5) {
                this.updateSummary();
            }
            log.info(`Moved to step ${this.currentStep}`);
        } else {
            this.showValidationErrors(errors);
        }
    }

    /**
     * Moves to previous step
     */
    previousStep() {
        this.currentStep = Math.max(this.currentStep - 1, 1);
        this.updateStepVisibility();
        log.info(`Moved to step ${this.currentStep}`);
    }

    /**
     * Updates step visibility
     */
    updateStepVisibility() {
        this.stepForms.forEach(step => {
            step.classList.toggle('hidden', step.dataset.stepId != this.currentStep);
        });
        this.stepCurrent.textContent = this.currentStep;
    }

    /**
     * Updates summary page content
     */
    updateSummary() {
        try {
            // Update basic info
            this.summaryTitle.textContent = this.titleInput.value;
            this.summaryDescription.textContent = this.descriptionInput.value;

            // Update bounty table
            this.summaryBountyTable.innerHTML = '';
            let totalPoints = 0;

            this.bounties.forEach(bounty => {
                const row = `
                    <tr class="border-b border-gray-200">
                        <td class="py-4 pl-4 pr-3 text-sm">
                            <div class="font-medium text-gray-900">${this.escapeHtml(bounty.title)}</div>
                            <div class="text-gray-500">${this.escapeHtml(bounty.description)}</div>
                        </td>
                        <td class="py-4 px-3 text-sm text-center">${bounty.points}</td>
                    </tr>
                `;
                this.summaryBountyTable.insertAdjacentHTML('beforeend', row);
                totalPoints += parseInt(bounty.points);
            });

            this.summaryTotalPoints.textContent = totalPoints;
            log.debug('Summary updated');
        } catch (error) {
            this.handleError('Failed to update summary', error);
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
            log.debug('Progress saved');
        } catch (error) {
            log.warn('Failed to save progress', error);
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
                log.info('Progress restored');
            }
        } catch (error) {
            log.warn('Failed to restore progress', error);
        }
    }

    /**
     * Starts auto-save interval
     */
    startAutoSave() {
        setInterval(() => this.saveProgress(), this.autoSaveInterval);
        log.info('Auto-save started');
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

    /**
     * Handles errors
     */
    handleError(context, error) {
        const message = `${context}: ${error.message}`;
        log.error(message, error);
        this.showValidationErrors([message]);
    }
}

// Start flow when page loads
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

export default ChallengeFlow; 