document.addEventListener('DOMContentLoaded', function() {
  const addButton = document.getElementById('add-website');
  const container = document.querySelector('.container-website');

  if(addButton) { 
    
    addButton.addEventListener('click', function() {
    const newRow = document.createElement('div');
    newRow.className = 'row-website flex flex-col md:flex-row md:items-center w-full space-y-4 md:space-y-0 md:space-x-6';
    newRow.innerHTML = `
      <div class="grow">
        <div class="relative h-9 flex items-center w-full">
          <div class="py-1.5 w-[68px] px-3 h-full rounded-l-sm bg-neutral-50 text-sm text-black/[0.85]
          shadow-[0px_-1px_0px_0px_#D9D9D9_inset,_0px_1px_0px_0px_#D9D9D9_inset,_1px_0px_0px_0px_#D9D9D9_inset]">http://</div>
          <input type="text" name="website" id="website" autocomplete="website"
            class="block w-full h-full max-w-full rounded-r-sm shadow-none border border-solid border-[#D9D9D9] py-1.5 px-3 text-gray-900 text-sm ring-0 
            placeholder:text-gray-400 focus:ring-0 focus-visible:outline-none sm:text-sm sm:leading-6 h-9"
            placeholder="janesmith">
        </div>
      </div>
      <div class="w-full md:w-[220px]">
        <div class="js-choice relative">
          <select id="type-of-website" name="type-of-website"
            class="type-of-website appearance-none block w-full rounded-sm border-0 py-1.5 pl-3 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-[#1890ff] focus-visible:outline-0 text-sm sm:leading-6 text-gray-500">
            <option value="">Make your choose</option>
            <option value="1">
              Personal
            </option>
            <option value="2">
              Company
            </option>
          </select>
        </div>
      </div>
    `;

    container.insertBefore(newRow, addButton.parentNode);

    const selectTypeOfWebsites = document.querySelectorAll('.type-of-website');

    selectTypeOfWebsites.forEach((item) => {
      if(item) {
        const choicesTypeOfWebsite = new Choices(item, {
          itemSelectText: '',
        });
      }
    })

    // Add the "Remove" button to the new row
    const removeButton = document.createElement('button');
    removeButton.setAttribute('type', 'button');
    removeButton.className = 'remove-button text-xs leading-5 text-red-500 text-left md:text-center';
    removeButton.textContent = 'Remove';

    // Add click event listener to remove the row when the remove button is clicked
    removeButton.addEventListener('click', function() {
      container.removeChild(newRow);
    });

    newRow.appendChild(removeButton);

  });
  }

});
