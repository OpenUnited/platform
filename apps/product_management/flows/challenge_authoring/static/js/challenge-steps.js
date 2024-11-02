// Debug utility
const DEBUG = process.env.NODE_ENV !== 'production';
const log = DEBUG ? console.log.bind(console, '[Challenge Steps]:') : () => {};

class ChallengeStepManager {
    constructor() {
        this.initializeElements();
        this.currentStep = 1;
        this.bounties = [];
        this.bindEvents();
        log('ChallengeStepManager initialized');
    }

    initializeElements() {
        try {
            // Step navigation elements
            this.stepNumbs = document.querySelectorAll('[data-step-numb]');
            this.stepForms = document.querySelectorAll('[data-step-id]');
            this.stepCurrent = document.querySelector('[data-current-step]');
            this.stepNext = document.querySelector('[data-step-next]');
            this.stepPrevious = document.querySelector('[data-step-previous]');
            this.changeStepEdit = document.querySelector('#change-step-edit');
            this.publishBtn = document.querySelector('#publish-challenge-btn');
            this.bountyContainer = document.querySelector('#bounty_area');

            // Validate required elements
            if (!this.stepCurrent || !this.bountyContainer) {
                throw new Error('Required elements not found');
            }
        } catch (error) {
            this.handleError('Initialization failed', error);
        }
    }

    bindEvents() {
        try {
            if (this.changeStepEdit) {
                this.changeStepEdit.addEventListener('click', () => this.changeStep(2));
            }

            if (this.stepNext) {
                this.stepNext.addEventListener('click', () => this.handleStepNavigation('next'));
            }

            if (this.stepPrevious) {
                this.stepPrevious.addEventListener('click', () => this.handleStepNavigation('previous'));
            }
        } catch (error) {
            this.handleError('Event binding failed', error);
        }
    }

    handleStepNavigation(direction) {
        const currentStep = Number(this.stepCurrent.dataset.currentStep);
        
        if (direction === 'next' && currentStep === 5) return;
        if (direction === 'previous' && currentStep === 1) return;

        const newStep = direction === 'next' ? currentStep + 1 : currentStep - 1;
        this.changeStep(newStep);
    }

    changeStep(newStep) {
        try {
            this.stepCurrent.dataset.currentStep = Number(newStep);

            // Update step numbers
            this.stepNumbs.forEach(numb => {
                numb.classList.toggle('active', Number(numb.dataset.stepNumb) === newStep);
            });

            // Update form visibility
            this.stepForms.forEach(form => {
                form.classList.toggle('active', Number(form.dataset.stepId) === newStep);
            });

            // Handle navigation visibility
            this.stepPrevious?.classList.toggle('hidden', newStep === 1);
            
            if (newStep === 5) {
                log('Updating summary view');
                this.stepNext?.classList.add('hidden');
                this.publishBtn?.classList.remove('hidden');
                setTimeout(() => this.updateAllSummaries(), 100);
            } else {
                this.stepNext?.classList.remove('hidden');
                this.publishBtn?.classList.add('hidden');
            }
        } catch (error) {
            this.handleError('Step change failed', error);
        }
    }

    updateAllSummaries() {
        try {
            // Update challenge summary
            this.updateElementContent('summary_title', this.getElementValue('id_title'));
            this.updateElementContent('summary_description', this.getElementValue('id_description'));

            // Update bounties summary
            this.updateBountiesSummary();
        } catch (error) {
            this.handleError('Summary update failed', error);
        }
    }

    updateBountiesSummary() {
        const summaryTable = document.getElementById('summary_bounty_table');
        const bountyTable = document.getElementById('bounty_table_body');
        
        if (!summaryTable || !bountyTable) return;

        summaryTable.innerHTML = '';
        if (!bountyTable.children.length) return;

        let totalPoints = 0;

        Array.from(bountyTable.children).forEach(row => {
            const skillText = row.querySelector('div.font-medium')?.textContent || '';
            const points = parseInt(row.querySelector('input[type="number"]')?.value || '0');
            totalPoints += points;
            
            const newRow = this.createBountySummaryRow(skillText, points);
            summaryTable.insertAdjacentHTML('beforeend', newRow);
        });

        this.updateElementContent('summary_total_points', totalPoints.toString());
    }

    addBounty(event) {
        try {
            const bountyData = this.collectBountyData();
            if (!this.validateBountyData(bountyData)) return;

            const bountyTable = document.getElementById('bounty_table_body');
            if (!bountyTable) throw new Error('Bounty table not found');

            const row = this.createBountyTableRow(bountyData);
            bountyTable.appendChild(row);

            this.updateFormCount(1);
            this.hideModalShowContainer();
            this.updateAllSummaries();
            
            log('Bounty added successfully', bountyData);
        } catch (error) {
            this.handleError('Adding bounty failed', error);
        }
    }

    deleteBounty(index) {
        try {
            const bountyTable = document.getElementById('bounty_table_body');
            if (!bountyTable) return;

            const rows = bountyTable.getElementsByTagName('tr');
            if (rows[index]) {
                rows[index].remove();
                this.updateFormCount(-1);
                this.updateAllSummaries();

                if (bountyTable.children.length === 0) {
                    this.bountyContainer.classList.add('hidden');
                }
                
                log('Bounty deleted successfully', { index });
            }
        } catch (error) {
            this.handleError('Deleting bounty failed', error);
        }
    }

    // Helper methods
    collectBountyData() {
        return {
            totalForms: document.getElementById('id_bounty-TOTAL_FORMS')?.value || '0',
            title: this.getElementValue('id_bounty-0-title'),
            description: this.getElementValue('id_bounty-0-description'),
            skill: this.getElementValue('id_bounty-0-skill'),
            skillLabel: document.getElementById('id_bounty-0-skill')?.querySelector('option:checked')?.textContent.trim() || '',
            status: this.getElementValue('id_bounty-0-status') || 'DRAFT',
            expertiseIds: this.getElementValue('id_bounty-0-expertise_ids'),
            expertiseString: this.collectExpertiseString()
        };
    }

    validateBountyData(data) {
        const errors = [];
        if (!data.title) errors.push('Title is required');
        if (!data.skill) errors.push('Skill is required');
        if (!data.expertiseIds) errors.push('At least one expertise must be selected');

        if (errors.length) {
            this.showValidationErrors(errors);
            return false;
        }
        return true;
    }

    collectExpertiseString() {
        const container = document.getElementById('ul_expertise_0');
        if (!container) return '';

        const checkedBoxes = container.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkedBoxes)
            .map(checkbox => checkbox.parentElement?.querySelector('label')?.textContent.trim())
            .filter(Boolean)
            .join(', ');
    }

    updateFormCount(change) {
        const inputTotalForms = document.getElementById('id_bounty-TOTAL_FORMS');
        if (inputTotalForms) {
            const currentCount = parseInt(inputTotalForms.value) || 0;
            inputTotalForms.value = Math.max(0, currentCount + change);
        }
    }

    hideModalShowContainer() {
        document.querySelector('.modal-wrap__skills')?.classList.add('hidden');
        this.bountyContainer?.classList.remove('hidden');
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

    handleError(context, error) {
        const message = `${context}: ${error.message}`;
        log('Error:', message);
        // You could add UI error handling here
        throw new Error(message);
    }

    showValidationErrors(errors) {
        log('Validation errors:', errors);
        // Implement UI error display
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.challengeManager = new ChallengeStepManager();
    } catch (error) {
        console.error('Failed to initialize ChallengeStepManager:', error);
    }
});
