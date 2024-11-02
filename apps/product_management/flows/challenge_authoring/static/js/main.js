/**
 * Main JavaScript for the Challenge Authoring flow
 * Manages multi-step form process with validation
 */

// Debug utility
const DEBUG = process.env.NODE_ENV !== 'production';
const log = DEBUG ? console.log.bind(console, '[Challenge Flow]:') : () => {};

import ChallengeFormValidation from './form_validation.js';

class ChallengeFlow {
    constructor() {
        this.currentStep = 1;
        this.bounties = [];
        this.initializeElements();
        this.bindEvents();
        this.validator = new ChallengeFormValidation();
        log('ChallengeFlow initialized');
    }

    initializeElements() {
        try {
            // Step navigation
            this.stepNumbs = document.querySelectorAll('[data-step-numb]');
            this.stepForms = document.querySelectorAll('[data-step-id]');
            this.stepCurrent = document.querySelector('[data-current-step]');
            this.nextButtons = document.querySelectorAll('[data-step-next]');
            this.prevButtons = document.querySelectorAll('[data-step-previous]');
            this.publishBtn = document.querySelector('#publish-challenge-btn');
            
            // Bounty management
            this.bountyArea = document.getElementById('bounty_area');
            this.bountyTableBody = document.getElementById('bounty_table_body');
            this.addBountyButton = document.querySelector('.skills-modal__open');

            // Validate required elements
            if (!this.stepCurrent || !this.bountyArea) {
                throw new Error('Required elements not found');
            }
        } catch (error) {
            this.handleError('Initialization failed', error);
        }
    }

    bindEvents() {
        // Step navigation
        this.nextButtons.forEach(btn => 
            btn.addEventListener('click', () => this.nextStep()));
        this.prevButtons.forEach(btn => 
            btn.addEventListener('click', () => this.previousStep()));

        // Bounty management
        if (this.addBountyButton) {
            this.addBountyButton.addEventListener('click', () => {
                // Using the imported showModal function
                window.showModal();
            });
        }

        // Form validation on step change
        document.addEventListener('beforeStepChange', (e) => {
            const { from, to } = e.detail;
            if (!this.validateStep(from)) {
                e.preventDefault();
            }
        });

        // Update summary when reaching final step
        document.addEventListener('stepChanged', (e) => {
            const { to } = e.detail;
            if (to === 5) { // Summary step
                this.updateSummary();
            }
        });
    }

    validateStep(stepNumber) {
        let isValid = false;
        
        switch (stepNumber) {
            case 1:
                isValid = this.validator.validateStepOne();
                break;
            case 2:
                isValid = this.validator.validateStepTwo();
                break;
            case 3:
                isValid = this.validator.validateStepThree();
                break;
            case 4:
                isValid = this.validator.validateStepFour();
                break;
            default:
                isValid = true;
        }

        if (!isValid) {
            this.validator.showErrors();
        }

        return isValid;
    }

    updateBountyTable(bounty) {
        if (!bounty) return;

        const skillText = bounty.querySelector('div.font-medium')?.textContent || '';
        const points = parseInt(bounty.querySelector('input[type="number"]')?.value || '0');

        const newRow = this.createBountySummaryRow(skillText, points);
        this.summaryBountyTable.insertAdjacentHTML('beforeend', newRow);

        this.summaryTotalPoints.textContent = (parseInt(this.summaryTotalPoints.textContent) + points).toString();
    }

    createBountySummaryRow(skillText, points) {
        return `
            <tr class="border-b border-gray-200">
                <td class="max-w-0 py-5 pl-4 pr-3 text-xs sm:pl-0">
                    <div class="font-medium text-gray-900">${this.escapeHtml(skillText)}</div>
                </td>
                <td class="py-5 pl-3 pr-4 text-sm text-gray-500 sm:pr-0 text-center">
                    ${points}
                </td>
            </tr>
        `;
    }

    // Utility methods
    getElementValue(id) {
        return document.getElementById(id)?.value || '';
    }

    updateElementContent(id, content) {
        const element = document.getElementById(id);
        if (element) element.textContent = content;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    isValidVideoUrl(url) {
        return url.match(/^(https?:\/\/)?(www\.)?(youtube\.com|vimeo\.com)\/.+$/i);
    }

    showValidationErrors(errors) {
        log('Validation errors:', errors);
        const errorContainer = document.getElementById('validation-errors');
        if (errorContainer) {
            errorContainer.innerHTML = errors.map(error => 
                `<div class="error-message">${this.escapeHtml(error)}</div>`
            ).join('');
            errorContainer.classList.remove('hidden');
        }
    }

    handleError(context, error) {
        const message = `${context}: ${error.message}`;
        log('Error:', message);
        this.showValidationErrors([message]);
        throw new Error(message);
    }

    // New methods for our enhanced validation
    async validateChallengeDetails() {
        const form = document.getElementById('challenge-form');
        const errors = [];
        
        // Enhanced validation rules
        const title = form.querySelector('[name="title"]').value;
        if (!title || title.length > 255) {
            errors.push('Title must be between 1 and 255 characters');
        }
        
        const description = form.querySelector('[name="description"]').value;
        if (!description || description.length < 50) {
            errors.push('Description must be at least 50 characters');
        }
        
        const videoUrl = form.querySelector('[name="video_url"]').value;
        if (videoUrl && !this.isValidVideoUrl(videoUrl)) {
            errors.push('Video URL must be from YouTube or Vimeo');
        }
        
        if (errors.length) {
            this.showValidationErrors(errors);
            return false;
        }
        return true;
    }

    log(...args) {
        if (this.DEBUG) {
            console.log('[Challenge Authoring]:', ...args);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.challengeFlow = new ChallengeFlow();
    } catch (error) {
        console.error('Failed to initialize ChallengeFlow:', error);
    }
}); 