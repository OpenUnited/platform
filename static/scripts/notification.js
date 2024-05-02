const typeSuccess="success"
const typeError="error"

const openVideoModal = (videoLink) => {
  alertify.alert().setting({
      modal: true,
      basic: true,
      message: `
          <div style="height: 50vh; width: 100%;">
            <iframe style="height: 100%; width: 100%" frameborder="0" allowfullscreen src="${videoLink}"></iframe> 
          </div>
      `,
      onshow: function () {
          this.elements.dialog.style.maxWidth = "none"; 
          this.elements.dialog.style.width = "60%";
          this.elements.dialog.style.height = "auto"; 
      }
  }).show();
}

const showNotification = (data) =>{
    const type = data.type || typeError
    const message = `<span class="text-white">${data.message|| "Something went wrong!"} </span>`
    alertify.set('notifier', 'position', 'top-right');
    alertify.error(message, type);
  }


const showConfirm = (data) =>{
  const type =  data.type|| "red"
  const message = data.message|| "Are you sure you want to delete this item?"
  const title = data.title|| 'Warning!'
  return new Promise((resolve) => {
    alertify.confirm(title, message, function (confirmed) {
      resolve(confirmed)}, function(){});
})
}



const authPopUp = (event, signUpUrl, signInUrl) =>{
  const currentPageUrl = window.location.href;
  signUpUrl += '?next=' + encodeURIComponent(currentPageUrl);
  signInUrl += '?next=' + encodeURIComponent(currentPageUrl);

  alertify.alert().set({'frameless':true, padding: false}).setting({
    title: 'Sign In or Sign Up',
    message: `
      <div class="">
        <div class="relative transform overflow-hidden rounded-lg bg-white px-1 pb-1 pt-5 text-left shadow-xl transition-all">
          <div class="sm:flex sm:items-start"> 
            <div class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-600">
                <i class="fa fa-info text-white"></i>
            </div>
            <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
              <h3 class="text-base font-semibold leading-6 text-gray-900" id="modal-title">Sign In or Sign Up</h3>
              <div class="mt-2">
                  <p class="text-gray-700 mb-1">To claim a bounty you need to be signed in.</p>
                  <p class="text-gray-700 mb-1">
                    Already have an account?
                    <a href="${signInUrl}" class="text-blue-500 hover:text-blue-700">Sign in here</a>
                  </p>
                  <p class="text-gray-700 mb-1">
                    New to OpenUnited?
                    <a href="${signUpUrl}" class="text-blue-500 hover:text-blue-700">Sign up here</a>
                  </p>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse m-2">
            <button  type="button" onclick="alertify.alert().close();" class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto">Cancel</button>
          </div>
        </div>
      </div>
    `,
  }).show();

}


function claimConfirm(event, termConditionUrl){
  alertify.confirm('Bounty Claim', `
  <hr><br>
  <form class="w-full max-w-sm confirm-form">
      <div class="w-full px-3">
          <label class="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" for="expected_submission_date">
              Expected Submission Date
          </label>
          <input class="appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500" id="expected_submission_date" type="date" placeholder="DD/MM/YY" required>
      </div>

      <div class="w-full px-3">
          <input id="term_checkbox" type="checkbox" class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600  focus:ring-2" required>
          <label for="term_checkbox" class="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300">I accept the <a href="${termConditionUrl}" target="_blank" class="text-blue-600 dark:text-blue-500 hover:underline">terms and conditions</a>.</label>
      </div>
  </form>
`, function () {
      const inputField = document.getElementById("expected_submission_date");
      const checkbox = document.getElementById("term_checkbox");
      const form = document.querySelector('.confirm-form');
      if (!form.checkValidity()) {
          const formControls = form.querySelectorAll('input');
          formControls.forEach(function (control) {
              if (!control.checkValidity()) {
                  control.reportValidity();
              }   
          });
          return false;
      } else {
          const data = {
              are_terms_accepted: true,
              expected_finish_date: inputField.value,
          };
          event.target.setAttribute("hx-vals", JSON.stringify(data));

          event.detail.issueRequest()
          this.close();
      }
  }, function () {}).set('labels', {ok: 'Request claim', cancel: 'Cancel'})
}