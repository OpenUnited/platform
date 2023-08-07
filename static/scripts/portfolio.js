// show more button for work list

const btnJobsMore = document.querySelector('.btn-jobs__more');
const btnJobsMoreText = document.querySelector('.btn-jobs__more-text');
const btnJobsMoreIcon = document.querySelector('.btn-jobs__more-icon');
const jobsList = document.querySelector('.jobs-list');
const jobsListItems = document.querySelectorAll('.jobs-list__item');

if (btnJobsMore) {
  btnJobsMore.addEventListener('click', () => {

    if(btnJobsMore.classList.contains('show')) {

      btnJobsMore.classList.remove('show');
      btnJobsMoreText.innerHTML = 'Show more';
      btnJobsMoreIcon.classList.remove('rotate-180');
  
      jobsListItems.forEach((item, i) => {
        
        if (i !== 0 && i !== 1) {
          item.classList.add('hidden');
        }
      });
      
    } else {

      btnJobsMore.classList.add('show');
      btnJobsMoreText.innerHTML = 'Show less';
      btnJobsMoreIcon.classList.add('rotate-180');
  
      jobsListItems.forEach((item) => {
        item.classList.remove('hidden');
      });
    }
  });
}
