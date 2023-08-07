// Get all tab links and tab bodies
const tabLinks = document.querySelectorAll('.tab-link');
const tabBodies = document.querySelectorAll('.tab-body');
const ideasBtnModal = document.querySelector('.ideas-btn-modal');

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

    if (tabLink.classList.contains('active') && tabLink.classList.contains('tab-link-ideas')) {
      ideasBtnModal.innerHTML = "Add Idea";
      ideasBtnModal.dataset.id = "modal-idea"
    } else {
      ideasBtnModal.innerHTML = "Add Bug";
      ideasBtnModal.dataset.id = "modal-bug"
    }

  });
});
