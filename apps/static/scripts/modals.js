// video popup open

const videoBtnsOpen = document.querySelectorAll(".btn-video__open");
const modalWrap = document.querySelector(".modal-wrap");
const modalWrapCloseBtn = document.querySelector(".btn-video__close");

const btnModapOpen = document.querySelectorAll(".btn-modal__open");
const modalWrapFilter = document.querySelector(".modal-wrap-filter");
const btnModalClose = document.querySelector(".btn-modal__close");


if(modalWrap) {
  if(modalWrap.querySelector("iframe"))
    modalWrap.querySelector("iframe").src = "";
}

videoBtnsOpen.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrap.classList.remove("hidden");
    modalWrap.querySelector("iframe").src = btn.dataset.video;
  });
});

if(modalWrapCloseBtn) {
  modalWrapCloseBtn.addEventListener("click", () => {
    modalWrap.classList.add("hidden");
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

const skillsBtnOpen = document.querySelector(".skills-modal__open");
const modalWrapSkills = document.querySelector(".modal-wrap__skills");
const modalSkillsCloseBtn = document.querySelector(".btn-skills__close");

if (skillsBtnOpen) {
  skillsBtnOpen.addEventListener("click", () => {
    document.getElementById('bounty_title').value = "";
    document.getElementById('bounty_description').value = "";

    modalWrapSkills.classList.remove("hidden");
  });
}

if (modalSkillsCloseBtn) {
  modalSkillsCloseBtn.addEventListener("click", () => {
    modalWrapSkills.classList.add("hidden");
  });
}


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
