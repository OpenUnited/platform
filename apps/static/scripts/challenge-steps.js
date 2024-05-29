// for challenges steps

const stepNumbs = document.querySelectorAll('[data-step-numb]');
const stepForms = document.querySelectorAll('[data-step-id]');
const stepCurrent = document.querySelector('[data-current-step');
const stepNext = document.querySelector('[data-step-next]');
const stepPrevious = document.querySelector('[data-step-previous]');
const changeStepEdit = document.querySelector('#change-step-edit');
const publishBtn = document.querySelector('#publish-challenge-btn');

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
    stepNext.classList.add('hidden');
    publishBtn.classList.remove('hidden');
  } else {
    stepNext.classList.remove('hidden');
    publishBtn.classList.add('hidden');
  };

  if(currentStep === 5) {
    const title = document.getElementById('id_title').value;
    const desc = document.getElementById('id_description').value;

    document.getElementById('summary_title').innerHTML = title;
    document.getElementById('summary_description').innerHTML = desc;

    const summaryBountyTable = document.getElementById('summary_bounty_table');
    const bountyTable = document.getElementById('bounty_table_body');

    var div, button, tr, td, input;
    var total = 0;

    summaryBountyTable.innerHTML = "";

    bountyTable.querySelectorAll('tr').forEach((elem, idx) => {
      let skillStr = elem.querySelectorAll('td')[0].querySelector('div').innerHTML;
      let points = parseInt(elem.querySelectorAll('input')[6].value);

      tr = document.createElement('tr');
      tr.className = 'border-b border-gray-200';
      td = document.createElement('td');
      td.className = 'max-w-0 py-5 pl-4 pr-3 text-xs sm:pl-0';
      div = document.createElement('div');
      div.className = 'font-medium text-gray-900';
      div.innerHTML = skillStr;
      td.appendChild(div);
      tr.appendChild(td);

      td = document.createElement('td');
      td.className = 'py-5 pl-3 pr-4 text-sm text-gray-500 sm:pr-0 text-center';
      td.innerHTML = points;
      tr.appendChild(td);

      summaryBountyTable.appendChild(tr);

      total = total + points;
    });

    document.getElementById('summary_total_points').innerHTML = total;

  }

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
  console.log("delete please....", index)
  const bountyTable = document.getElementById('bounty_table_body');
  bountyTable.querySelectorAll('tr')[index].remove();

  const inputTotalForms = document.getElementById('id_form-TOTAL_FORMS');
  const skillCount = parseInt(inputTotalForms.value);
  inputTotalForms.value = skillCount - 1;

  const allRows = bountyTable.querySelectorAll('tr');
  allRows.forEach((elem, idx) => {
    let td = elem.querySelectorAll('td')[2];
    td.onclick = function() { deleteBounty(idx); return false; };
  });
}


function addBounty(event) {
  const bountyContainer = document.getElementById(`bounty_area`);
  const inputTotalForms = document.getElementById('id_form-TOTAL_FORMS');
  const skillCount = parseInt(inputTotalForms.value);

  const bountyTitle = document.getElementById('bounty_title').value;
  const bountyDesc = document.getElementById('bounty_description').value;
  const bountySkill = document.getElementById('id_skill').value;
  const bountySkillLabel = document.getElementById('id_skill').querySelector('option:checked').textContent.trim();
  const bountyStatus = document.getElementById('id_bounty_status').value;
  const bountyIsActive = document.getElementById('id_is_active').value;

  var bountyExpertise = [];
  var expertiseStr = "";
  var expertiseIds = "";
  document.getElementById('id_skills-0-expertise')
      .querySelectorAll('option:checked')
      .forEach((elem) => {
          bountyExpertise.push({'id': elem.value, 'title': elem.textContent.trim()});
          if(expertiseStr.length > 0) {
              expertiseStr += ", ";
              expertiseIds += ",";
          }
          expertiseStr += elem.textContent.trim();
          expertiseIds += elem.value;
      });

  const bountyTable = document.getElementById('bounty_table_body');

  var div, button, tr, td, input;

  tr = document.createElement('tr');
  tr.className = 'border-b border-gray-200';
  td = document.createElement('td');
  td.className = 'max-w-0 py-5 pl-4 pr-3 text-xs sm:pl-0';
  div = document.createElement('div');
  div.className = 'font-medium text-gray-900';
  div.innerHTML = bountySkillLabel + " (" + expertiseStr + ")";
  td.appendChild(div);

  input = document.createElement('input');
  input.type = 'hidden';
  input.value = bountyTitle;
  input.name = `form-${skillCount}-title`;
  td.appendChild(input);

  input = document.createElement('input');
  input.type = 'hidden';
  input.value = bountyDesc;
  input.name = `form-${skillCount}-description`;
  td.appendChild(input);

  input = document.createElement('input');
  input.type = 'hidden';
  input.value = bountySkill;
  input.name = `form-${skillCount}-skill_id`;
  td.appendChild(input);

  input = document.createElement('input');
  input.type = 'hidden';
  input.value = expertiseIds;
  input.name = `form-${skillCount}-expertise_ids`;
  td.appendChild(input);

  input = document.createElement('input');
  input.type = 'hidden';
  input.value = bountyStatus;
  input.name = `form-${skillCount}-status`;
  td.appendChild(input);

  input = document.createElement('input');
  input.type = 'hidden';
  input.value = bountyIsActive;
  input.name = `form-${skillCount}-is_active`;
  td.appendChild(input);

  tr.appendChild(td);

  td = document.createElement('td');
  td.className = 'py-5 pr-1.5 sm:pr-4 text-sm text-gray-500 text-right md:text-left';
  input = document.createElement('input');
  input.className = 'w-12 sm:w-[72px] h-7 rounded-sm border border-solid border-[#1890FF] shadow-[0px_0px_0px_2px_rgba(24,144,255,0.20)] p-1.5';
  input.value = 0;
  input.type = 'number';
  input.name = `form-${skillCount}-points`;
  td.appendChild(input);
  tr.appendChild(td);

  // td = document.createElement('td');
  // td.className = 'py-5 pl-1.5 md:pl-3 pr-2 md:pr-4 text-xs sm:text-sm text-gray-500 sm:pr-0 text-left';
  // button = document.createElement('button');
  // button.className = 'appearance-none text-sm leading-[22px] text-[#1890FF] transition-all underline-offset-2 no-underline hover:underline';
  // button.innerHTML = 'Edit';
  // td.appendChild(button);
  // tr.appendChild(td);

  td = document.createElement('td');
  td.className = 'py-5 pl-1.5 md:pl-3 pr-2 md:pr-4 text-xs sm:text-sm text-gray-500 sm:pr-0 text-left';
  button = document.createElement('button');
  button.className = 'appearance-none text-sm leading-[22px] text-[#1890FF] transition-all underline-offset-2 no-underline hover:underline';
  button.innerHTML = 'Delete';
  button.onclick = function() { deleteBounty(skillCount); return false;};
  td.appendChild(button);
  tr.appendChild(td);

  bountyTable.appendChild(tr);

  inputTotalForms.value = skillCount + 1;

  const modalWrapSkills = document.querySelector(".modal-wrap__skills");
  modalWrapSkills.classList.add("hidden");
  bountyContainer.classList.remove("hidden");

}
