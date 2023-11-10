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
