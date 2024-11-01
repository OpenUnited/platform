// for challenges steps

const stepNumbs = document.querySelectorAll('[data-step-numb]');
const stepForms = document.querySelectorAll('[data-step-id]');
const stepCurrent = document.querySelector('[data-current-step');
const stepNext = document.querySelector('[data-step-next]');
const stepPrevious = document.querySelector('[data-step-previous]');
const changeStepEdit = document.querySelector('#change-step-edit');
const publishBtn = document.querySelector('#publish-challenge-btn');
const bountyContainer = document.querySelector('#bounty_area');

function updateAllSummaries() {
    // Update title and description
    const titleElem = document.getElementById('summary_title');
    const descElem = document.getElementById('summary_description');
    if (titleElem) titleElem.textContent = document.getElementById('id_title')?.value || '';
    if (descElem) descElem.textContent = document.getElementById('id_description')?.value || '';

    // Update bounties table
    const summaryTable = document.getElementById('summary_bounty_table');
    const bountyTable = document.getElementById('bounty_table_body');
    
    if (summaryTable && bountyTable) {
        // Clear the placeholder row
        summaryTable.innerHTML = '';
        
        // If no bounties, exit
        if (!bountyTable.children.length) return;

        let totalPoints = 0; // Initialize total points

        // Copy bounties
        Array.from(bountyTable.children).forEach(row => {
            const skillText = row.querySelector('div.font-medium')?.textContent || '';
            const points = parseInt(row.querySelector('input[type="number"]')?.value || '0');
            totalPoints += points; // Add to running total
            
            const newRow = `
                <tr class="border-b border-gray-200">
                    <td class="max-w-0 py-5 pl-4 pr-3 text-xs sm:pl-0">
                        <div class="font-medium text-gray-900">${skillText}</div>
                    </td>
                    <td class="py-5 pl-3 pr-4 text-sm text-gray-500 sm:pr-0 text-center">
                        ${points}
                    </td>
                </tr>
            `;
            summaryTable.insertAdjacentHTML('beforeend', newRow);
        });

        // Update total points
        const totalElement = document.getElementById('summary_total_points');
        if (totalElement) {
            totalElement.textContent = totalPoints;
        }
    }
}

function changeStep(currentStep) {

  stepCurrent.dataset.currentStep = Number(currentStep);

  stepNumbs.forEach((numb) => {

    if (Number(numb.dataset.stepNumb) === currentStep) {
      numb.classList.add('active');
    } else {
      numb.classList.remove('active');
    }
  });

  stepForms.forEach((form) => {

    if (Number(form.dataset.stepId) === currentStep) {
      form.classList.add('active');
    } else {
      form.classList.remove('active');
    }
  });

  if (currentStep === 1) {
    stepPrevious.classList.add('hidden');
  } else {
    stepPrevious.classList.remove('hidden');
  };

  if (currentStep === 5) {
    console.log("Updating summary table...");
    stepNext.classList.add('hidden');
    publishBtn.classList.remove('hidden');
    setTimeout(updateAllSummaries, 100);
  } else {
    stepNext.classList.remove('hidden');
    publishBtn.classList.add('hidden');
  };

}

if (changeStepEdit) {
  changeStepEdit.addEventListener('click', () => {
    changeStep(2);
  })
}

if (stepNext) {
  stepNext.addEventListener('click', () => {
    if (Number(stepCurrent.dataset.currentStep) === 5) {
      return;
    }
    changeStep(Number(stepCurrent.dataset.currentStep) + 1);
  });
}

if (stepPrevious) {

  stepPrevious.addEventListener('click', () => {
    if (Number(stepCurrent.dataset.currentStep) === 1) {
      return;
    }
    changeStep(Number(stepCurrent.dataset.currentStep) - 1);
  });
}


function deleteBounty(index) {
    // Find and remove the row from bounty table
    const bountyTable = document.getElementById('bounty_table_body');
    if (!bountyTable) return;

    // Find the row to delete
    const rows = bountyTable.getElementsByTagName('tr');
    if (rows[index]) {
        rows[index].remove();
    }

    // Update the TOTAL_FORMS count
    const inputTotalForms = document.getElementById('id_bounty-TOTAL_FORMS');
    if (inputTotalForms) {
        inputTotalForms.value = Math.max(0, parseInt(inputTotalForms.value) - 1);
    }

    // Update the summary table
    updateAllSummaries();

    // If no bounties left, show empty state
    if (bountyTable.children.length === 0 && bountyContainer) {
        bountyContainer.classList.add("hidden");
    }
}


function addBounty(event) {
    // Debug logging
    console.log('TOTAL_FORMS element:', document.getElementById('id_bounty-TOTAL_FORMS'));
    console.log('title element:', document.getElementById('id_bounty-0-title'));
    console.log('description element:', document.getElementById('id_bounty-0-description'));
    console.log('skill element:', document.getElementById('id_bounty-0-skill'));
    console.log('expertise_ids element:', document.getElementById('id_bounty-0-expertise_ids'));
    console.log('status element:', document.getElementById('id_bounty-0-status'));

    // Declare all variables at the top
    const inputTotalForms = document.getElementById('id_bounty-TOTAL_FORMS') || { value: '0' };
    const skillCount = parseInt(inputTotalForms.value);
    const bountyTitle = document.getElementById('id_bounty-0-title')?.value || '';
    const bountyDesc = document.getElementById('id_bounty-0-description')?.value || '';
    const bountySkill = document.getElementById('id_bounty-0-skill')?.value || '';
    const bountySkillLabel = document.getElementById('id_bounty-0-skill')?.querySelector('option:checked')?.textContent.trim() || '';
    const bountyStatus = document.getElementById('id_bounty-0-status')?.value || 'DRAFT';
    var bountyExpertise = [];
    var expertiseStr = "";
    var expertiseIds = document.getElementById('id_bounty-0-expertise_ids')?.value || "";

    const expertiseContainer = document.getElementById('ul_expertise_0');
    if (expertiseContainer) {
        const checkedBoxes = expertiseContainer.querySelectorAll('input[type="checkbox"]:checked');
        checkedBoxes.forEach((checkbox) => {
            const label = checkbox.parentElement.querySelector('label');
            if (label) {
                if (expertiseStr.length > 0) {
                    expertiseStr += ", ";
                }
                expertiseStr += label.textContent.trim();
            }
        });
    }

    const bountyTable = document.getElementById('bounty_table_body');
    if (!bountyTable) {
        console.error('Bounty table not found');
        return;
    }

    // Create table row
    var tr = document.createElement('tr');
    tr.className = 'border-b border-gray-200';

    // First column with skill and hidden inputs
    var td = document.createElement('td');
    td.className = 'max-w-0 py-5 pl-4 pr-3 text-xs sm:pl-0';
    
    var div = document.createElement('div');
    div.className = 'font-medium text-gray-900';
    const displayText = bountySkillLabel + (expertiseStr ? ` (${expertiseStr})` : '');
    div.innerHTML = displayText;
    td.appendChild(div);

    // Add hidden inputs
    const hiddenInputs = [
        { name: 'title', value: bountyTitle },
        { name: 'description', value: bountyDesc },
        { name: 'skill', value: bountySkill },
        { name: 'expertise_ids', value: expertiseIds },
        { name: 'status', value: bountyStatus }
    ];

    hiddenInputs.forEach(input => {
        var hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.value = input.value;
        hiddenInput.name = `bounty-${skillCount}-${input.name}`;
        td.appendChild(hiddenInput);
    });

    tr.appendChild(td);

    // Rest of the row (points and delete button)
    td = document.createElement('td');
    td.className = 'py-5 pr-1.5 sm:pr-4 text-sm text-gray-500 text-right md:text-left';
    var input = document.createElement('input');
    input.className = 'w-12 sm:w-[72px] h-7 rounded-sm border border-solid border-[#1890FF] shadow-[0px_0px_0px_2px_rgba(24,144,255,0.20)] p-1.5';
    input.value = 0;
    input.type = 'number';
    input.name = `bounty-${skillCount}-points`;
    td.appendChild(input);
    tr.appendChild(td);

    td = document.createElement('td');
    td.className = 'py-5 pl-1.5 md:pl-3 pr-2 md:pr-4 text-xs sm:text-sm text-gray-500 sm:pr-0 text-left';
    var button = document.createElement('button');
    button.className = 'appearance-none text-sm leading-[22px] text-[#1890FF] transition-all underline-offset-2 no-underline hover:underline';
    button.innerHTML = 'Delete';
    
    // Fix: Use row index instead of form count
    button.onclick = function() { 
        const row = this.closest('tr');
        const index = Array.from(bountyTable.children).indexOf(row);
        deleteBounty(index); 
        return false; 
    };
    
    td.appendChild(button);
    tr.appendChild(td);

    bountyTable.appendChild(tr);
    inputTotalForms.value = skillCount + 1;

    // Hide modal and show bounty container
    const modalWrapSkills = document.querySelector(".modal-wrap__skills");
    if (modalWrapSkills) {
        modalWrapSkills.classList.add("hidden");
    }
    
    if (bountyContainer) {
        bountyContainer.classList.remove("hidden");
    }

    // Update summary table
    updateAllSummaries();
}
