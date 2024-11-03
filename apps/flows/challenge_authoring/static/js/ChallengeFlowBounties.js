/**
 * Bounty management functionality for the challenge creation flow.
 * Handles bounty CRUD operations, API calls, and UI updates.
 */

import { ChallengeFlowCore } from './ChallengeFlowCore';

export class ChallengeFlowBounties extends ChallengeFlowCore {
    /**
     * Extends core initialization
     */
    initializeElements() {
        super.initializeElements();
        
        // Bounty management elements
        this.bountyArea = document.getElementById('bounty_area');
        this.bountyTableBody = document.getElementById('bounty_table_body');
        this.addBountyButton = document.querySelector('.skills-modal__open');
        
        // Summary elements
        this.summaryTitle = document.getElementById('summary_title');
        this.summaryDescription = document.getElementById('summary_description');
        this.summaryBountyTable = document.getElementById('summary_bounty_table');
        this.summaryTotalPoints = document.getElementById('summary_total_points');
    }

    /**
     * Extends core event binding
     */
    bindEvents() {
        super.bindEvents();

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

        this.log.info('Bounty events bound');
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
        this.log.info('Bounty added', formattedBounty);
    }

    /**
     * Handles bounty removal
     */
    handleBountyRemoved(index) {
        this.bounties.splice(index, 1);
        this.updateBountyTable();
        this.saveProgress();
        this.log.info('Bounty removed at index', index);
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
            this.log.debug('Summary updated');
        } catch (error) {
            this.handleError('Failed to update summary', error);
        }
    }

    /**
     * Extends core step validation
     */
    validateStep(stepNumber) {
        const errors = super.validateStep(stepNumber);
        
        // Add bounty-specific validation
        if (stepNumber === 3 || stepNumber === 5) {
            if (this.bounties.length === 0) {
                errors.push('At least one bounty is required');
            }
        }
        
        return errors;
    }
}