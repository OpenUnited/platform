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
