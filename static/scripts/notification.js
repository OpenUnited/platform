const typeSuccess="success"
const typeError="error"


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

