// video popup open

const videoBtnsOpen = document.querySelectorAll(".btn-video__open");
const modalWrap = document.querySelector(".modal-wrap");
const modalWrapCloseBtn = document.querySelector(".btn-video__close");

const btnModapOpen = document.querySelectorAll(".btn-modal__open");
const modalWrapFilter = document.querySelector(".modal-wrap-filter");
const btnModalClose = document.querySelector(".btn-modal__close");


if(modalWrap && modalWrap.querySelector("iframe")) {
    modalWrap.querySelector("iframe").src = "";
}

if (videoBtnsOpen) {
    videoBtnsOpen.forEach((btn) => {
        btn.addEventListener("click", () => {
            if (modalWrap && modalWrap.querySelector("iframe")) {
                modalWrap.classList.remove("hidden");
                modalWrap.querySelector("iframe").src = btn.dataset.video || "";
            }
        });
    });
}

if(modalWrapCloseBtn && modalWrap) {
    modalWrapCloseBtn.addEventListener("click", () => {
        modalWrap.classList.add("hidden");
        if (modalWrap.querySelector("iframe")) {
            modalWrap.querySelector("iframe").src = "";
        }
    });
}


// Filter modal
/* TODO add a modal filter.
 btnModapOpen.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrapFilter.classList.remove("hidden");
  });
});

if (btnModalClose) {
  btnModalClose.addEventListener("click", () => {
    modalWrapFilter.classList.add("hidden");
  });
} */

// challenge & bounty popup open

document.addEventListener('DOMContentLoaded', function() {
    const skillsBtnOpen = document.querySelector(".skills-modal__open");
    const modalWrapSkills = document.querySelector(".modal-wrap__skills");
    const modalSkillsCloseBtn = document.querySelector(".btn-skills__close");

    if (skillsBtnOpen) {
        skillsBtnOpen.addEventListener("click", (e) => {
            e.preventDefault(); // Prevent any default button behavior
            
            // First check if modal exists
            if (modalWrapSkills) {
                // Try to reset form, but don't fail if elements don't exist
                try {
                    resetBountyForm();
                } catch (error) {
                    console.log("Some form elements were not found:", error);
                }
                
                modalWrapSkills.classList.remove("hidden");
            }
        });
    }

    if (modalSkillsCloseBtn) {
        modalSkillsCloseBtn.addEventListener("click", () => {
            if (modalWrapSkills) {
                modalWrapSkills.classList.add("hidden");
            }
        });
    }
});

// open create new challange modal

const btnCreateChallanegOpen = document.querySelectorAll(
  ".btn-modal-challenge"
);
const modalWrapCreateChallenge = document.querySelector(
  ".modal-wrap-create-challange"
);
const btnChallengeModalClose = document.querySelector(".btn-challenge__close");

btnCreateChallanegOpen.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrapCreateChallenge.classList.remove("hidden");
  });
});

if (btnChallengeModalClose) {
  btnChallengeModalClose.addEventListener("click", () => {
    modalWrapCreateChallenge.classList.add("hidden");
  });
}

// Update resetBountyForm to be more defensive
function resetBountyForm() {
    // Create an array of form field IDs to reset
    const formFields = [
        'id_bounty-0-title',
        'id_bounty-0-description',
        'id_bounty-0-skill',
        'id_bounty-0-expertise_ids',
        'id_bounty-0-expertise'
    ];

    // Try to reset each field, skip if not found
    formFields.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (element) {
            element.value = '';
        }
    });

    // Try to reset checkboxes if they exist
    try {
        const expertiseChecks = document.querySelectorAll('input[type="checkbox"][name^="expertise"]');
        expertiseChecks.forEach(check => {
            if (check) {
                check.checked = false;
            }
        });
    } catch (error) {
        console.log("No expertise checkboxes found");
    }
}

// Keep the showBountyModal function for external use
function showBountyModal() {
    const modalWrap = document.querySelector(".modal-wrap__skills");
    if (modalWrap) {
        try {
            resetBountyForm();
        } catch (error) {
            console.log("Error resetting form:", error);
        }
        modalWrap.classList.remove("hidden");
    }
}

// Bounty modal specific handling
document.addEventListener('DOMContentLoaded', function() {
    // Modal elements
    const bountyButton = document.querySelector('.skills-modal__open');
    const bountyModal = document.querySelector('.modal-wrap__skills');
    const closeButton = document.querySelector('.btn-skills__close');
    const overlay = document.querySelector('.modal-wrap__overlay');
    
    // Show modal
    if (bountyButton) {
        bountyButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (bountyModal) {
                bountyModal.classList.remove('hidden');
            }
        });
    }

    // Close modal - close button
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            if (bountyModal) {
                bountyModal.classList.add('hidden');
            }
        });
    }

    // Close modal - overlay
    if (overlay) {
        overlay.addEventListener('click', function() {
            if (bountyModal) {
                bountyModal.classList.add('hidden');
            }
        });
    }
});

// Expose global modal functions
window.showBountyModal = function() {
    const modal = document.querySelector('.modal-wrap__skills');
    if (modal) {
        modal.classList.remove('hidden');
    }
};

window.hideBountyModal = function() {
    const modal = document.querySelector('.modal-wrap__skills');
    if (modal) {
        modal.classList.add('hidden');
    }
};
