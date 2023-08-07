// filter modal open

const btnModapOpen = document.querySelectorAll(".btn-modal__open");
const modalWrapFilter = document.querySelector(".modal-wrap-filter");
const btnModalClose = document.querySelector(".btn-modal__close");

btnModapOpen.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrapFilter.classList.remove("hidden");
  });
});

if(btnModalClose) {

  btnModalClose.addEventListener("click", () => {
    modalWrapFilter.classList.add("hidden");
  });
}

// cancel modal open

const btnCancel = document.querySelectorAll(".btn-cancel");
const modalCancel = document.querySelector(".modal-cancel");
const btnCancelClose = document.querySelector(".btn-cancel__close");

btnCancel.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalCancel.classList.remove("hidden");
  });
});

if(btnCancelClose) {

  btnCancelClose.addEventListener("click", () => {
    modalCancel.classList.add("hidden");
  });
}

// modal: form for idea / bug

const btnAddModapOpen = document.querySelector(".btn-add-modal__open");
const modalWrapIdeasBugs = document.querySelectorAll(".modal-wrap-ideas-bugs");
const btnsIdeaModalClose = document.querySelectorAll(".btn-idea-modal__close");

if (btnAddModapOpen) {

  btnAddModapOpen.addEventListener("click", () => {

    modalWrapIdeasBugs.forEach((modal) => {

      if (ideasBtnModal.dataset.id === modal.dataset.modal) {
        modal.classList.remove("hidden");
      } else {
        modal.classList.add("hidden");
      }

    })
  });

}

btnsIdeaModalClose.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrapIdeasBugs.forEach((modal) => {
      modal.classList.add("hidden");
    })
  });
});

// video popup open

const videoBtnsOpen = document.querySelectorAll(".btn-video__open");
const modalWrap = document.querySelector(".modal-wrap");
const modalWrapCloseBtn = document.querySelector(".btn-video__close");

if(modalWrap) {
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

// skills popup open

const skillsBtnOpen = document.querySelector(".skills-modal__open");
const modalWrapSkills = document.querySelector(".modal-wrap__skills");
const modalSkillsCloseBtn = document.querySelector(".btn-skills__close");

if (skillsBtnOpen) {
  skillsBtnOpen.addEventListener("click", () => {
    modalWrapSkills.classList.remove("hidden");
    // console.log(modalWrapSkills);
  });
}

if(modalSkillsCloseBtn) {
  modalSkillsCloseBtn.addEventListener("click", () => {
    modalWrapSkills.classList.add("hidden");
  });
}
