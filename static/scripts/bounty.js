const viewMore = document.querySelectorAll(".view-more");
viewMore.forEach((button) => {
  button.addEventListener("click", function (event) {
    const hiddenDiv = event.target.nextElementSibling;
    toggleDivVisibility(hiddenDiv, button);
  });
});
const viewMoreContent = `
View more
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor"
  class="h-5 w-5 text-gray-400 fill-gray-400">
  <path fillRule="evenodd"
    d="M4.22 6.22a.75.75 0 0 1 1.06 0L8 8.94l2.72-2.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.28a.75.75 0 0 1 0-1.06Z"
    clipRule="evenodd" />
</svg>
`;
function toggleDivVisibility(hiddenDiv, button) {
  hiddenDiv.classList.toggle("hidden");
  const a = hiddenDiv.parentNode;
  if (hiddenDiv.classList.contains("hidden")) {
    button.innerHTML = viewMoreContent;
  } else {
    button.innerHTML = `
      View less
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor"
        class="h-5 w-5 text-gray-400 fill-gray-400 rotate-180">
        <path fillRule="evenodd"
          d="M4.22 6.22a.75.75 0 0 1 1.06 0L8 8.94l2.72-2.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.28a.75.75 0 0 1 0-1.06Z"
          clipRule="evenodd" />
      </svg>
    `;
  }

  if (!hiddenDiv.classList.contains("hidden")) {
    const allDivs = document.querySelectorAll(".more_detail_bountry");
    allDivs.forEach((div) => {
      if (div !== hiddenDiv) {
        div.classList.add("hidden");
        const prevButton = div.previousElementSibling;
        prevButton.innerHTML = viewMoreContent;
      }
    });
  }
}

document.addEventListener("click", function (event) {
  const viewMoreButtons = document.querySelectorAll(".view-more");
  viewMoreButtons.forEach((button) => {
    const hiddenDiv = button.nextElementSibling;
    if (!hiddenDiv.contains(event.target) && event.target !== button) {
      hiddenDiv.classList.add("hidden");
      button.innerHTML = viewMoreContent;
    }
  });
});
