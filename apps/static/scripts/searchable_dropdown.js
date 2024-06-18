function searchableDropdownFilterInput(event){
    const filterInput = document.getElementById('searchable-dropdown-input');
    const dropdownList = document.getElementById('searchable-dropdown-list');
    const value = filterInput.value.toLowerCase();
    const listItems = dropdownList.children;


    if (value.length === 0){
      return document.querySelectorAll(".searchable-dropdown-li").forEach(item => item.classList.add("hidden"));
    }
    else {
      for (let i = 0; i < listItems.length; i++) {
        const listItem = listItems[i];
        if (listItem.textContent.toLowerCase().includes(value)) {
          listItem.classList.remove("hidden");
        } else {
          listItem.classList.add("hidden");
        }
      }
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
