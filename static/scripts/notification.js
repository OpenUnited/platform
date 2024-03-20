const showNotification = (data) =>{
    const type = data.type? data.type: "red"
    const message = data.message? data.message: "Something went wrong!"
    const title = data.title? data.title: 'Error!'
    $.alert({
        title: title,
        content: message,
        useBootstrap: false,
        boxWidth: '350px',
        type: type,
        typeAnimated: true,
    });
}

const showConfirm = (data) =>{
  const type = data.type? data.type: "red"
  const message = data.message? data.message: "Something went wrong!"
  const title = data.title? data.title: 'Error!'
  const callback = data.callback
  const callback_data = data.callback_data

  $.confirm({
    title: 'Warning!',
    content: 'Are you sure you want to delete this item?',
    type: 'red',
    typeAnimated: true,
    boxWidth: '350px',
    useBootstrap: false,
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

