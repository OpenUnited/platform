export class BountyModal {
    constructor() {
        this.modal = document.getElementById('bounty-modal');
        this.bountiesContainer = document.getElementById('bounties-container');
        this.bindEvents();
    }

    bindEvents() {
        window.showModal = () => this.show();
        window.hideModal = () => this.hide();
        window.saveBounty = () => this.saveBounty();
    }

    async saveBounty() {
        const skillSelect = document.getElementById('bounty-skill');
        const skillId = skillSelect.value;
        const skillName = skillSelect.options[skillSelect.selectedIndex].text.replace(/^-+\s*/, '');
        const title = document.getElementById('bounty-title').value;
        const description = document.querySelector('#bounty-description-editor .ql-editor').innerHTML;
        const points = document.getElementById('bounty-points').value;

        if (!title || !points || !skillId) {
            alert('Please fill in all required fields');
            return;
        }

        const bounty = {
            id: Date.now(),
            skill: {
                id: skillId,
                name: skillName
            },
            title: title,
            description: description,
            points: points
        };

        try {
            const response = await fetch(BOUNTY_TABLE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ bounties: [bounty] })
            });

            if (!response.ok) throw new Error('Failed to save bounty');
            
            const html = await response.text();
            this.bountiesContainer.innerHTML = html;
            this.hide();
            this.clearForm();
        } catch (error) {
            console.error('Error saving bounty:', error);
            alert('Failed to save bounty. Please try again.');
        }
    }

    clearForm() {
        document.getElementById('bounty-skill').value = '';
        document.getElementById('bounty-title').value = '';
        document.querySelector('#bounty-description-editor .ql-editor').innerHTML = '';
        document.getElementById('bounty-points').value = '';
    }

    show() {
        this.modal.classList.add('modal-open');
    }

    hide() {
        this.modal.classList.remove('modal-open');
        this.clearForm();
    }
}