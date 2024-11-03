/**
 * Core functionality for the challenge creation flow.
 * Handles initialization, navigation, and basic validation.
 */

const DEBUG = process.env.NODE_ENV !== 'production';

export class ChallengeFlowCore {
    constructor() {
        this.currentStep = 1;
        this.bounties = [];
        this.DEBUG = DEBUG;
        this.autoSaveInterval = 30000; // 30 seconds
        
        // Initialize logging
        this.log = this.initializeLogging();
        
        // Setup and validate
        this.initializeEndpoints();
        this.initializeElements();
        this.bindEvents();
    }

    /**
     * Initializes logging utilities
     */
    initializeLogging() {
        return {
            info: (...args) => DEBUG && console.log('[Challenge Flow]:', ...args),
            warn: (...args) => DEBUG && console.warn('[Challenge Flow]:', ...args),
            error: (...args) => console.error('[Challenge Flow]:', ...args),
            debug: (...args) => DEBUG && console.debug('[Challenge Flow]:', ...args),
            table: (data) => DEBUG && console.table(data)
        };
    }

    /**
     * Sets up API endpoints
     */
    initializeEndpoints() {
        const form = document.querySelector('form');
        this.productSlug = form?.dataset.productSlug;
        if (!this.productSlug) {
            throw new Error('Product slug not found on form');
        }

        this.endpoints = {
            submit: `/${this.productSlug}/challenge/create/`,
            skills: '/expertise-options/',
            expertise: (skillId) => `/expertise-options/?skill_id=${skillId}`
        };
    }

    /**
     * Initializes DOM elements
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
            
            // Form elements
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
            
            // Error display
            this.errorContainer = document.getElementById('validation-errors');

            this.validateRequiredElements();
            this.log.info('Elements initialized');
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
     * Binds core event listeners
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

        this.log.info('Core events bound');
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
            this.log.info(`Moved to step ${this.currentStep}`);
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
        this.log.info(`Moved to step ${this.currentStep}`);
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

            case 4:
                const status = this.statusSelect?.value;
                const priority = this.prioritySelect?.value;
                
                if (!status) errors.push('Status is required');
                if (!priority) errors.push('Priority is required');
                break;
        }

        return errors;
    }

    /**
     * Basic error handler - can be overridden
     */
    handleError(context, error) {
        const message = `${context}: ${error.message}`;
        this.log.error(message, error);
        this.showValidationErrors([message]);
    }
}
