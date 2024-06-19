function searchableDropdownFilterInput(event, url){
  if (event.target.value.length>1){
    htmxRequest({
      url: url,
      values:{"search": event.target.value},
      target: `#searchable-dropdown-list`,
      swap:"innerHTML"
    })
  }
  else{
    document.getElementById("searchable-dropdown-list").innerHTML = ""
  }
}

function selectItem(event){
  const listItem = event.target

  // Iterate over the NodeList and remove each element
  document.querySelectorAll(".searchable-dropdown-li").forEach(icon => icon.classList.remove("bg-gray-100"));

  listItem.classList.add('bg-gray-100');

  document.getElementById('selectfield-selectfield').value = listItem.id
  document.getElementById('searchable-dropdown').classList.toggle('hidden');
  document.getElementById('searchable-dropdown-label').textContent = event.target.textContent || 'Please Select';

}

function toggleMenu(event) {
  document.getElementById('searchable-dropdown').classList.toggle('hidden');
}

window.searchableDropdownFilterInput = searchableDropdownFilterInput
window.selectItem = selectItem
window.toggleMenu = toggleMenu
