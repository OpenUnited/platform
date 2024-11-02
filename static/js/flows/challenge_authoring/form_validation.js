// Validation utilities
const REQUIRED_MESSAGE = 'This field is required';
const MIN_LENGTH_MESSAGE = (field, length) => `${field} must be at least ${length} characters`;
const MAX_LENGTH_MESSAGE = (field, length) => `${field} must be less than ${length} characters`;

class ChallengeFormValidation {
    constructor() {
        this.errors = new Map();
    }

    validateStepOne() {
        this.errors.clear();
        
        // Validate challenge type selection
        const skillsCount = document.querySelector('input[name="skills-count"]:checked');
        if (!skillsCount) {
            this.errors.set('skills-count', REQUIRED_MESSAGE);
        }

        // Validate reward type selection
        const rewardType = document.querySelector('input[name="reward_type"]:checked');
        if (!rewardType) {
            this.errors.set('reward_type', REQUIRED_MESSAGE);
        }

        return this.errors.size === 0;
    }

    validateStepTwo() {
        this.errors.clear();

        // Validate title
        const title = document.getElementById('id_title').value.trim();
        if (!title) {
            this.errors.set('title', REQUIRED_MESSAGE);
        } else if (title.length < 10) {
            this.errors.set('title', MIN_LENGTH_MESSAGE('Title', 10));
        } else if (title.length > 200) {
            this.errors.set('title', MAX_LENGTH_MESSAGE('Title', 200));
        }

        // Validate description
        const description = document.getElementById('id_description').value.trim();
        if (!description) {
            this.errors.set('description', REQUIRED_MESSAGE);
        } else if (description.length < 50) {
            this.errors.set('description', MIN_LENGTH_MESSAGE('Description', 50));
        } else if (description.length > 5000) {
            this.errors.set('description', MAX_LENGTH_MESSAGE('Description', 5000));
        }

        // Validate product area (if required)
        const productArea = document.getElementById('id_product_area');
        if (productArea && productArea.required && !productArea.value) {
            this.errors.set('product_area', REQUIRED_MESSAGE);
        }

        // Validate initiative (if required)
        const initiative = document.getElementById('id_initiative');
        if (initiative && initiative.required && !initiative.value) {
            this.errors.set('initiative', REQUIRED_MESSAGE);
        }

        return this.errors.size === 0;
    }

    validateStepThree() {
        this.errors.clear();

        // Validate at least one bounty is added
        const bountyTableBody = document.getElementById('bounty_table_body');
        if (!bountyTableBody || bountyTableBody.children.length === 0) {
            this.errors.set('bounties', 'At least one skill & expertise must be added');
            return false;
        }

        // Validate total points (if there's a maximum)
        const totalPoints = Array.from(bountyTableBody.querySelectorAll('tr'))
            .reduce((sum, row) => {
                const points = parseInt(row.querySelector('td:nth-child(2)').textContent);
                return sum + (isNaN(points) ? 0 : points);
            }, 0);

        const MAX_POINTS = 1000; // Configure as needed
        if (totalPoints > MAX_POINTS) {
            this.errors.set('total_points', `Total points cannot exceed ${MAX_POINTS}`);
        }

        return this.errors.size === 0;
    }

    validateStepFour() {
        this.errors.clear();

        // Validate status
        const status = document.getElementById('id_status');
        if (status && status.required && !status.value) {
            this.errors.set('status', REQUIRED_MESSAGE);
        }

        // Validate priority
        const priority = document.getElementById('id_priority');
        if (priority && priority.required && !priority.value) {
            this.errors.set('priority', REQUIRED_MESSAGE);
        }

        // Validate attachments (if any required fields)
        const requiredAttachments = document.querySelectorAll('.attachment-input[required]');
        requiredAttachments.forEach(attachment => {
            if (!attachment.value) {
                this.errors.set(attachment.id, REQUIRED_MESSAGE);
            }
        });

        return this.errors.size === 0;
    }

    showErrors() {
        // Clear existing error messages
        document.querySelectorAll('.error-message').forEach(el => {
            el.textContent = '';
            el.classList.add('hidden');
        });

        // Show new error messages
        this.errors.forEach((message, field) => {
            const errorElement = document.getElementById(`${field}-error`);
            if (errorElement) {
                errorElement.textContent = message;
                errorElement.classList.remove('hidden');
            } else {
                // Create error element if it doesn't exist
                const input = document.getElementById(`id_${field}`) || 
                             document.querySelector(`[name="${field}"]`);
                if (input) {
                    const errorDiv = document.createElement('div');
                    errorDiv.id = `${field}-error`;
                    errorDiv.className = 'error-message text-red-500 text-sm mt-1';
                    errorDiv.textContent = message;
                    input.parentNode.appendChild(errorDiv);
                }
            }
        });
    }
}

export default ChallengeFormValidation; 