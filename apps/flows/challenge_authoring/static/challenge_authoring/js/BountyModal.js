export class BountyModal {
    constructor() {
        this.modal = document.getElementById('bounty-modal');
        this.bindEvents();
        this.initialize();
    }

    initialize() {
        // Add modal HTML if it doesn't exist
        if (!this.modal) {
            const modalHTML = `
                <div id="bounty-modal" class="modal">
                    <div class="modal-box">
                        <h3 class="font-bold text-lg">Add Bounty</h3>
                        <div class="py-4">
                            <!-- Bounty Form -->
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">Title</span>
                                </label>
                                <input type="text" id="bounty-title" class="input input-bordered" />
                            </div>
                            <div class="form-control mt-4">
                                <label class="label">
                                    <span class="label-text">Points</span>
                                </label>
                                <input type="number" id="bounty-points" class="input input-bordered" />
                            </div>
                        </div>
                        <div class="modal-action">
                            <button class="btn btn-ghost" onclick="window.hideModal()">Cancel</button>
                            <button class="btn btn-primary" onclick="window.addBounty()">Add</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            this.modal = document.getElementById('bounty-modal');
        }
    }

    bindEvents() {
        // Expose methods to window for button clicks
        window.showModal = () => this.show();
        window.hideModal = () => this.hide();
        window.addBounty = () => this.addBounty();

        // Add button click handler
        const addBountyBtn = document.getElementById('add-bounty-btn');
        if (addBountyBtn) {
            addBountyBtn.addEventListener('click', () => this.show());
        }
    }

    show() {
        this.modal.classList.add('modal-open');
    }

    hide() {
        this.modal.classList.remove('modal-open');
    }

    addBounty() {
        const title = document.getElementById('bounty-title').value;
        const points = document.getElementById('bounty-points').value;

        if (!title || !points) {
            alert('Please fill in all fields');
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
                    <iconify-icon icon="lucide:x" height="18"></iconify-icon>
                </button>
            </div>
        `;
        container.appendChild(bountyElement);

        // Clear form and close modal
        document.getElementById('bounty-title').value = '';
        document.getElementById('bounty-points').value = '';
        this.hide();
    }
}