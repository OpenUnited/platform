window.bounties = [];

const BOUNTY_TABLE_URL = document.querySelector('#challenge-form')?.dataset.bountyTableUrl;

class ChallengeFlowBounties {
    constructor(tableUrl) {
        this.tableUrl = tableUrl;
        this.initializeListeners();
        this.modal = document.getElementById('bounty-modal');
    }

    initializeListeners() {
        const addBountyBtn = document.getElementById('add-bounty-btn');
        if (addBountyBtn) {
            addBountyBtn.addEventListener('click', () => this.showBountyModal());
        }

        const bountyForm = document.getElementById('bounty-form');
        if (bountyForm) {
            bountyForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleBountySubmit(e);
            });
        }
    }

    showBountyModal() {
        if (this.modal) {
            this.modal.classList.add('modal-open');
            const skillSelect = document.getElementById('bounty-skill');
            const titleInput = document.getElementById('bounty-title');
            const pointsInput = document.getElementById('bounty-points');
            if (skillSelect) skillSelect.value = '';
            if (titleInput) titleInput.value = '';
            if (pointsInput) pointsInput.value = '';
            if (window.bountyDescriptionEditor) {
                bountyDescriptionEditor.setText('');
            }
        }
    }

    handleBountySubmit(event) {
        const form = event.target;
        const skillSelect = form.querySelector('#skill-select');
        const pointsInput = form.querySelector('#points-input');
        const descriptionInput = form.querySelector('#bounty-description');

        const bountyData = {
            id: Date.now(), // Temporary ID for frontend handling
            skill_id: skillSelect.value,
            skill_name: skillSelect.options[skillSelect.selectedIndex].text,
            points: pointsInput.value,
            description: descriptionInput.value
        };

        this.addBounty(bountyData);
        this.modal.classList.remove('modal-open');
        form.reset();
    }

    addBounty(bountyData) {
        window.bounties.push(bountyData);
        this.renderBounties();
    }

    getBounties() {
        return window.bounties;
    }

    renderBounties() {
        const container = document.getElementById('bounties-container');
        if (!container) return;
        
        fetch(this.tableUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ bounties: window.bounties })
        })
        .then(response => response.text())
        .then(html => {
            container.innerHTML = html;
        });
    }

    removeBounty(id) {
        window.bounties = window.bounties.filter(bounty => bounty.id !== id);
        this.renderBounties();
    }
}

// Add this helper function globally
window.hideModal = function() {
    const modal = document.getElementById('bounty-modal');
    if (modal) {
        modal.classList.remove('modal-open');
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing challenge authoring page...');

    // Initialize Quill
    if (window.Quill) {
        const quill = new Quill('#editor', {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['link']
                ]
            },
            placeholder: 'Enter description...'
        });

        // Update hidden input whenever Quill content changes
        quill.on('text-change', function() {
            const descriptionInput = document.getElementById('description');
            if (descriptionInput) {
                descriptionInput.value = quill.root.innerHTML;
            }
        });
    }

    // Initialize file upload handling
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const dropArea = document.getElementById('file-upload-area');

    if (fileInput && fileList && dropArea) {
        // File input change handler
        fileInput.addEventListener('change', (e) => {
            const files = e.target.files;
            handleFiles(files);
        });

        // Drag and drop handlers
        dropArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropArea.classList.add('border-primary');
        });

        dropArea.addEventListener('dragleave', () => {
            dropArea.classList.remove('border-primary');
        });

        dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            dropArea.classList.remove('border-primary');
            const files = e.dataTransfer.files;
            handleFiles(files);
        });
    }

    // Initialize bounties handling
    const form = document.getElementById('challenge-form');
    if (form) {
        window.challengeFlowBounties = new ChallengeFlowBounties(
            form.dataset.bountyTableUrl
        );

        // Form submission handler
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log('Form submitted');
            
            const formData = new FormData(form);
            
            // Explicitly stringify the bounties array
            if (window.bounties && window.bounties.length > 0) {
                console.log('Adding bounties to form:', window.bounties);
                formData.append('bounties', JSON.stringify(window.bounties));
            } else {
                formData.append('bounties', JSON.stringify([]));
            }
            
            // Log all form data for debugging
            for (let pair of formData.entries()) {
                console.log('Form data:', pair[0], pair[1]);
            }
            
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        console.error('Server response:', text);
                        throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to save challenge. Please try again.');
            });
        });
    }

    // Initialize cancel button
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            window.history.back();
        });
    }

    // Set focus on title input
    setTimeout(() => {
        const titleInput = document.getElementById('title-input');
        if (titleInput) {
            titleInput.focus();
            console.log('Focus set on title input');
        }
    }, 100);
});

// File handling function
function handleFiles(files) {
    const fileList = document.getElementById('file-list');
    if (!fileList) return;

    Array.from(files).forEach(file => {
        // Add your file handling logic here
        console.log('Handling file:', file.name);
    });
}

// Update saveBounty function to use the global bounties array
window.saveBounty = function(event) {
    // Prevent any default behavior and stop event propagation
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('Saving bounty...');
    
    // Ensure bounties array exists
    if (!window.bounties) {
        window.bounties = [];
    }
    
    // Get all the bounty data
    const skillSelect = document.getElementById('bounty-skill');
    const skillId = skillSelect.value;
    const skillName = skillSelect.options[skillSelect.selectedIndex].text.replace(/^-+\s*/, '');
    const title = document.getElementById('bounty-title').value;
    const description = bountyDescriptionEditor.root.innerHTML;
    const points = document.getElementById('bounty-points').value;

    // Create unique ID for the bounty
    const bountyId = Date.now();
    
    // Check if this bounty already exists (prevent duplicates)
    if (window.bounties.some(b => b.title === title && b.skill.id === skillId)) {
        console.log('Bounty already exists, skipping...');
        return false;
    }

    // Create bounty object
    const bounty = {
        id: bountyId,
        skill: {
            id: skillId,
            name: skillName
        },
        title: title,
        description: description,
        points: parseInt(points, 10)
    };

    // Add to bounties array
    window.bounties.push(bounty);
    console.log('Updated bounties array:', window.bounties);

    // Update the table
    fetch(BOUNTY_TABLE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ bounties: window.bounties })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
    })
    .then(html => {
        document.getElementById('bounties-container').innerHTML = html;
        
        // Clear the form
        skillSelect.value = '';
        document.getElementById('bounty-title').value = '';
        bountyDescriptionEditor.setText('');
        document.getElementById('bounty-points').value = '';
        
        // Hide the modal
        hideModal();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save bounty. Please try again.');
    });

    return false; // Prevent form submission
};

// Remove any existing click handlers from the save button
document.addEventListener('DOMContentLoaded', function() {
    const saveBountyBtn = document.querySelector('#bounty-modal .modal-action button.btn-primary');
    if (saveBountyBtn) {
        // Remove all existing click listeners
        const newBtn = saveBountyBtn.cloneNode(true);
        saveBountyBtn.parentNode.replaceChild(newBtn, saveBountyBtn);
        
        // Add single click listener
        newBtn.addEventListener('click', saveBounty);
    }
}); 