const showNotification = (data) =>{
    const type = data.type? data.type: "red"
    const message = data.message? data.message: "Something went wrong!"
    const title = data.title? data.title: 'Error!'
    const displayTime = data.displayTime? data.displayTime: 1500
    var alert  = $.alert({
        title: title,
        content: message,
        useBootstrap: false,
        boxWidth: '350px',
        type: type,
        typeAnimated: true,
        icon: 'fa fa-exclamation-circle',
    });

    setTimeout(function() {
      alert.close();
    }, displayTime); 
}

const showConfirm = (data) =>{
  const type = data.type? data.type: "red"
  const message = data.message? data.message: "Are you sure you want to delete this item?"
  const title = data.title? data.title: 'Warning!'
  const callback = data.callback
  const callback_data = data.callback_data

  $.confirm({
    title: title,
    content: message,
    type: type,
    typeAnimated: true,
    boxWidth: '350px',
    useBootstrap: false,
    icon: 'fa fa-exclamation-circle',
    buttons: {
        confirm: {
            text: 'Confirm!',
            btnClass: 'btn-red',
            action: function(){
              if (callback){
                callback(callback_data)
              }
            }
        },
        close: function () {
        }
    }
});
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

