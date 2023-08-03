// for challenges steps

const stepNumbs = document.querySelectorAll('[data-step-numb]');
const stepForms = document.querySelectorAll('[data-step-id]');
const stepCurrent = document.querySelector('[data-current-step');
const stepNext = document.querySelector('[data-step-next]');
const stepPrevious = document.querySelector('[data-step-previous]');
const changeStepEdit = document.querySelector('#change-step-edit');
const publishBtn = document.querySelector('#publish-btn');

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
