export class BountyModal {
    constructor() {
        this.modal = document.getElementById('bounty-modal');
        this.bindEvents();
    }

    bindEvents() {
        // Expose methods to window for button clicks
        window.showModal = () => this.show();
        window.hideModal = () => this.hide();
        window.saveBounty = () => this.saveBounty();

        // Add button click handler
        const addBountyBtn = document.getElementById('add-bounty-btn');
        if (addBountyBtn) {
            addBountyBtn.addEventListener('click', () => {
                console.log('Add Bounty button clicked!');
                this.show();
            });
        }
    }

    show() {
        this.modal.classList.add('modal-open');
    }

    hide() {
        this.modal.classList.remove('modal-open');
        // Clear form
        document.getElementById('bounty-title').value = '';
        document.getElementById('bounty-points').value = '';
        document.getElementById('bounty-skill').value = '';
    }

    saveBounty() {
        const title = document.getElementById('bounty-title').value;
        const points = document.getElementById('bounty-points').value;
        const skill = document.getElementById('bounty-skill').value;

        if (!title || !points || !skill) {
            alert('Please fill in all required fields');
            return;
        }

        const container = document.getElementById('bounties-container');
        const bountyElement = document.createElement('div');
        bountyElement.className = 'card bg-base-100 border shadow-sm';
        bountyElement.innerHTML = `
            <div class="card-body p-4 flex-row justify-between items-center">
                <div>
                    <h3 class="font-medium">${title}</h3>
                    <p class="text-sm text-base-content/70">${points} points</p>
                </div>
                <button onclick="this.closest('.card').remove()" class="btn btn-ghost btn-sm btn-square">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        container.appendChild(bountyElement);

        this.hide();
    }
}