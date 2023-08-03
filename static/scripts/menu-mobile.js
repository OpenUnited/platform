// functionality for open mobile menu

const menuWrap = document.querySelector(".menu-wrap");
const menuOverlay = document.querySelector(".menu-overlay");
const openMenuButton = document.querySelector(".btn-open-menu");
const closeMenuButton = document.querySelector(".btn-close-menu");
const body = document.body;

function openMobileMenu() {
  menuWrap.classList.add("menu-open");
  body.classList.add("overflow-hidden");
}

function closeMobileMenu() {
  menuWrap.classList.remove("menu-open");
  body.classList.remove("overflow-hidden");
}

if(openMenuButton) {
  openMenuButton.addEventListener("click", openMobileMenu);
}

if(closeMenuButton) {
  closeMenuButton.addEventListener("click", closeMobileMenu);
}

if(menuOverlay) {
  menuOverlay.addEventListener("click", closeMobileMenu);
}
