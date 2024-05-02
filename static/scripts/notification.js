const typeSuccess="success"
const typeError="error"

{/* 

*/}

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
    const message = data.message|| "Something went wrong!"
    const title =  data.title|| 'Error'
    alertify.set('notifier', 'position', 'top-right');
    alertify.notify(message, type)
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





