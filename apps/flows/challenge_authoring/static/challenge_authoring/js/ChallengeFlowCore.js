/**
 * Core functionality for the challenge creation flow.
 * Handles initialization, navigation, and basic validation.
 */

// Replace process.env with a browser-compatible debug flag
const DEBUG = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

export class ChallengeFlowCore {
    constructor() {
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
        this.productSlug = window.PRODUCT_SLUG;

        if (!this.productSlug) {
            console.error('Product slug not found in window context');
            throw new Error('Product slug not found');
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

            // Set focus to title input
            if (this.titleInput) {
                this.titleInput.focus();
            }

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
        // Form field changes
        if (this.form) {
            this.form.addEventListener('input', () => this.saveProgress());
            this.form.addEventListener('change', () => this.saveProgress());
        }

        this.log.info('Core events bound');
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
