const typeSuccess = "success"
const typeError = "error"

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

const showNotification = (data) => {
  const type = data.type || typeError
  const message = `<span class="text-white">${data.message || "Something went wrong!"} </span>`
  alertify.set('notifier', 'position', 'top-right');

  if (type == typeSuccess) {
    alertify.success(message);
  }
  else if (type == typeError) {
    alertify.error(message);
  }
}


const showConfirm = (data) => {
  const type = data.type || "red"
  const message = data.message || "Are you sure you want to delete this item?"
  const title = data.title || 'Warning!'
  return new Promise((resolve) => {
    alertify.confirm(title, message, function (confirmed) {
      resolve(confirmed)
    }, function () { });
  })
}



const authPopUp = (event, signUpUrl, signInUrl) => {
  const currentPageUrl = window.location.href;
  signUpUrl += '?next=' + encodeURIComponent(currentPageUrl);
  signInUrl += '?next=' + encodeURIComponent(currentPageUrl);

  alertify.alert().set({ 'frameless': true, padding: false }).setting({
    message: `
      <div class="relative overflow-hidden rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 border border-gray-200 px-4 py-3 text-left shadow-xl transition-all">
        <div class="border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold leading-6 text-gray-900 px-4 py-2" id="modal-title">
            <i class="fa fa-sign-in text-indigo-600 w-5" aria-hidden="true"></i>
            Sign In or Sign Up
          </h3>
        </div>
        <div class="sm:flex sm:items-start">
          <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
            <div class="border-t border-gray-200 px-4 py-2">
              <p class="text-gray-800">To claim a bounty, please sign in.</p>
              <p class="text-gray-800">Already have an account? <a href="${signInUrl}" class="text-blue-500 hover:text-blue-700">Sign in here</a></p>
              <p class="text-gray-800">New to OpenUnited? <a href="${signUpUrl}" class="text-blue-500 hover:text-blue-700">Sign up here</a></p>
            </div>
          </div>
        </div>
        <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse m-2">
          <button type="button" onclick="alertify.alert().close();" class="mt-3 inline-flex justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:mt-0 sm:w-auto">
            Close
          </button>
        </div>
      </div>
    `,
  }).show()

}


// function claimConfirm(event, bounty_id, agreement_status, termConditionUrl) {
function claimConfirm(event, termConditionUrl) {
  // if (!agreement_status) {
  //   // alert("need to accept agreement...")
  //   console.log(bounty_id)
  //   document.querySelector(".modal-wrap").classList.remove("hidden");
  //   var input_clicked_bounty = document.getElementById("clicked_bounty");

  //   if(input_clicked_bounty.value == "")
  //     input_clicked_bounty.value = bounty_id;
  // }
  // else {

    alertify.confirm('Bounty Claim', `
    <hr><br>
    <form class="w-full confirm-form">
        <div class="w-full px-3">
            <label class="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" for="expected_submission_date">
                Expected Submission Date
            </label>
            <input class="appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500" id="expected_submission_date" type="date" placeholder="DD/MM/YY" required>
        </div>

        <div class="mt-3 w-full px-3">
            <input id="is_agreement_accepted" type="checkbox" class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600  focus:ring-2" required>
            <label for="is_agreement_accepted" class="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300">
            I have read and agree to the <a href="${termConditionUrl}" target="_blank" class="text-blue-600 dark:text-blue-500 hover:underline">Contribution Agreement</a>.</label>
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
          is_agreement_accepted: true,
          expected_finish_date: inputField.value,
        };
        event.target.setAttribute("hx-vals", JSON.stringify(data));

        event.detail.issueRequest()
        this.close();
      }
    }, function () { }).set('labels', { ok: 'Request claim', cancel: 'Cancel' })

  // }

}
