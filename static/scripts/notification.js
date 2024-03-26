const showNotification = (data) =>{
    const type = data.type? data.type: "red"
    const message = data.message? data.message: "Something went wrong!"
    const title = data.title? data.title: 'Error!'
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
    }, 1500); 
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

