// Get all tab links and tab bodies
const tabLinks = document.querySelectorAll('.tab-link');
const tabBodies = document.querySelectorAll('.tab-body');

// Add click event listeners to tab links
tabLinks.forEach((tabLink, index) => {
  tabLink.addEventListener('click', (e) => {
    e.preventDefault();

    // Remove active class from all tab links and tab bodies
    tabLinks.forEach((link) => link.classList.remove('active'));
    tabBodies.forEach((body) => body.classList.remove('active'));

    // Add active class to the clicked tab link and corresponding tab body
    tabLink.classList.add('active');
    tabBodies[index].classList.add('active');
  });
});

// filter modal open

const btnModapOpen = document.querySelectorAll(".btn-modal__open");
const modalWrapFilter = document.querySelector(".modal-wrap-filter");
const btnModalClose = document.querySelector(".btn-modal__close");

btnModapOpen.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrapFilter.classList.remove("hidden");
  });
});

btnModalClose.addEventListener("click", () => {
  modalWrapFilter.classList.add("hidden");
});

// form for idea / bug in modal open

const btnAddModapOpen = document.querySelectorAll(".btn-add-modal__open");
const modalWrapIdeasBugs = document.querySelector(".modal-wrap-ideas-bugs");
const btnAddModalClose = document.querySelector(".btn-add-modal__close");

btnAddModapOpen.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrapIdeasBugs.classList.remove("hidden");
  });
});

btnAddModalClose.addEventListener("click", () => {
  modalWrapIdeasBugs.classList.add("hidden");
});

// video popup open

const videoBtnsOpen = document.querySelectorAll(".btn-video__open");
const modalWrap = document.querySelector(".modal-wrap");
const modalWrapCloseBtn = document.querySelector(".btn-video__close");

modalWrap.querySelector("iframe").src = "";

videoBtnsOpen.forEach((btn) => {
  btn.addEventListener("click", () => {
    modalWrap.classList.remove("hidden");
    modalWrap.querySelector("iframe").src = btn.dataset.video;
  });
});

modalWrapCloseBtn.addEventListener("click", () => {
  modalWrap.classList.add("hidden");
});

// product tree functionality

const nestedTableNames = document.querySelectorAll(".nested-item__label-icon");

nestedTableNames.forEach((item) => {
  item.addEventListener("click", () => {
    const child = item.closest(".nested-item__label").nextElementSibling;
    child.classList.toggle("hidden");

    const categoryOpenBtn = item.querySelector(".category-open-btn");
    const categoryCloseBtn = item.querySelector(".category-close-btn");

    if (child.classList.contains("hidden")) {
      categoryCloseBtn.classList.remove("hidden");
      categoryOpenBtn.classList.add("hidden");
    } else {
      categoryCloseBtn.classList.add("hidden");
      categoryOpenBtn.classList.remove("hidden");
    }
  });
});

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

openMenuButton.addEventListener("click", openMobileMenu);
closeMenuButton.addEventListener("click", closeMobileMenu);
menuOverlay.addEventListener("click", closeMobileMenu);

// setup for select

const selectControlRefSortedBy = document.querySelector('#control-ref_sortedBy');
const selectControlRefPriority = document.querySelector('#control-ref_priority');
const selectControlRefCategories = document.querySelector('#control-ref_categories');
const selectControlRefTags = document.querySelector('#control-ref_tags');
const selectControlRefStatuses = document.querySelector('#control-ref_statuses');

const choicesSortedBy = new Choices(selectControlRefSortedBy, {

});
const choicesPriority = new Choices(selectControlRefPriority, {
  placeholder: true,
  removeItems: true,
  removeItemButton: true,
});
const choicesCategories = new Choices(selectControlRefCategories, {
  placeholder: true,
  removeItems: true,
  removeItemButton: true,
});
const choicesTags = new Choices(selectControlRefTags, {
  placeholder: true,
  removeItems: true,
  removeItemButton: true,
});
const choicesStatuses = new Choices(selectControlRefStatuses, {
  placeholder: true,
  removeItems: true,
  removeItemButton: true,
});
