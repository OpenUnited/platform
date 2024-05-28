// video popup open

const videoBtnsOpen = document.querySelectorAll(".btn-video__open");
const modalWrap = document.querySelector(".modal-wrap");
const modalWrapCloseBtn = document.querySelector(".btn-video__close");

const btnModapOpen = document.querySelectorAll(".btn-modal__open");
const modalWrapFilter = document.querySelector(".modal-wrap-filter");
const btnModalClose = document.querySelector(".btn-modal__close");


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
