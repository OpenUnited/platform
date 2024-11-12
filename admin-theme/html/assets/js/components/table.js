const createTable = (table) => {
  const allCheckbox = table.querySelector("[data-slot=all-checkbox]")
  const checkboxes = table.querySelectorAll("[data-slot=single-checkbox]")

  if (allCheckbox) {
    allCheckbox.addEventListener("change", (event) => {
      for (let checkbox of checkboxes) {
        checkbox.checked = event.target.checked
      }
    })
  }

  const updateSelectAllCheckbox = () => {
    let allChecked = true
    let anyChecked = false

    for (let checkbox of checkboxes) {
      if (!checkbox.checked) {
        allChecked = false
      } else {
        anyChecked = true
      }
    }

    if (allCheckbox) {
      allCheckbox.checked = !anyChecked ? false : allChecked
      allCheckbox.indeterminate = allChecked ? false : anyChecked
    }
  }

  for (let checkbox of checkboxes) {
    checkbox.addEventListener("change", () => {
      updateSelectAllCheckbox()
    })
  }

  const fileRows = table.querySelectorAll("tbody tr")
  for (let row of fileRows) {
    row.addEventListener("click", (event) => {
      if (event.target.tagName.toLowerCase() === "input") return

      const checkbox = row.querySelector(".checkbox")
      checkbox.checked = !checkbox.checked
      updateSelectAllCheckbox()
    })
  }
}

const initTable = () => {
  document.querySelectorAll("[data-component=table]").forEach(createTable)
}

document.addEventListener("DOMContentLoaded", function () {
  initTable()
})
