document.addEventListener('DOMContentLoaded', function() {
    initializeSkillTree();
    initializeSkillSelection();
    initializeFormSubmission();
});

function initializeSkillTree() {
    const toggleButtons = document.querySelectorAll('.toggle-children');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const skillItem = this.closest('.skill-item');
            const childSkills = skillItem.querySelector('.child-skills');
            const icon = this.querySelector('svg');
            
            if (childSkills) {
                childSkills.classList.toggle('hidden');
                icon.style.transform = childSkills.classList.contains('hidden') 
                    ? 'rotate(0deg)' 
                    : 'rotate(90deg)';
            }
        });
    });
}

function initializeSkillSelection() {
    document.querySelectorAll('.skill-radio').forEach(radio => {
        radio.addEventListener('change', async function() {
            const skillId = this.value;
            const expertiseContainer = document.getElementById('expertise-container');

            if (!skillId) {
                expertiseContainer.innerHTML = '';
                return;
            }

            try {
                expertiseContainer.innerHTML = '<p class="text-gray-500">Loading expertise options...</p>';
                
                const response = await fetch(`/get-expertise/?skill_id=${skillId}`);
                if (!response.ok) throw new Error('Network response was not ok');
                
                const html = await response.text();
                expertiseContainer.innerHTML = html;
                
                // Clear any existing error
                const errorElement = document.querySelector('.expertise-error');
                if (errorElement) errorElement.remove();
            } catch (error) {
                console.error('Error:', error);
                expertiseContainer.innerHTML = '<p class="text-red-500">Error loading expertise options</p>';
            }
        });
    });
}

function initializeFormSubmission() {
    const form = document.getElementById('bounty-form');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Collect form data
        const formData = new FormData(this);
        const selectedExpertise = Array.from(document.querySelectorAll('input[name="expertise"]:checked'))
            .map(cb => cb.value)
            .join(',');
        formData.append('expertise_ids', selectedExpertise);

        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            });

            const data = await response.json();
            
            if (data.success) {
                closeModal();
                window.location.href = data.redirect_url;
            } else {
                handleFormErrors(data.errors);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
}

function handleFormErrors(errors) {
    Object.keys(errors).forEach(field => {
        const errorElement = document.getElementById(`${field}-error`);
        if (errorElement) {
            errorElement.textContent = errors[field].join(', ');
            errorElement.classList.remove('hidden');
        }
    });
}

function closeModal() {
    document.querySelector('.modal-wrap__skills').classList.add('hidden');
    // Clear form and errors
    document.getElementById('bounty-form').reset();
    document.querySelectorAll('.error-message').forEach(el => {
        el.classList.add('hidden');
        el.textContent = '';
    });
}

function showModal() {
    document.querySelector('.modal-wrap__skills').classList.remove('hidden');
}

export { showModal, closeModal }; 