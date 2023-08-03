// for challenges steps

const stepsUser = document.querySelectorAll('[data-user-step]');
const stepsContent = document.querySelectorAll('[data-user-content]');
const stepCurrentUser = document.querySelector('[data-user-steps');
const stepNextBtns = document.querySelectorAll('[data-btn]');

function changeStepUser(currentStep) {

  stepCurrentUser.dataset.userSteps = Number(currentStep);

  stepsUser.forEach((numb) => {

    if (Number(numb.dataset.userStep) === currentStep) {
      numb.classList.add('active');
    } else {
      numb.classList.remove('active');
    }
  });

  stepsContent.forEach((form) => {

    if (Number(form.dataset.userContent) === currentStep) {
      form.classList.add('active');
    } else {
      form.classList.remove('active');
    }
  });

}

stepNextBtns.forEach((btn) => {
  btn.addEventListener('click', () => {

    if(Number(stepCurrentUser.dataset.userSteps) === 3) {
      return
    }
    
    changeStepUser(Number(stepCurrentUser.dataset.userSteps) + 1);
  });
});
