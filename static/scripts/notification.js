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

  $.confirm({
    type: "blue",
    typeAnimated: true,
    boxWidth: '350px',
    useBootstrap: false,
    icon: 'fa fa-info-circle',
    title: 'Sign In or Sign Up',
    content: `
        <div class="bg-white mt-4 bg-indigo-600">
          <div class="form-group ">
            <p class="text-gray-700 mb-4">To claim a bounty you need to be signed in.</p>
            <p class="text-gray-700 mb-4">
              Already have an account?
              <a href="${signInUrl}" class="text-blue-500 hover:text-blue-700">Sign in here</a>
            </p>
            <p class="text-gray-700 mb-4">
              New to OpenUnited?
              <a href="${signUpUrl}" class="text-blue-500 hover:text-blue-700">Sign up here</a>
            </p>
          </div>
        </div>
    `,
    buttons: {
        cancel: function () {},
    },
});
}

