const createPasswordField = (component) => {
  const input = component.querySelector("[data-slot=input]")

  const visibilityToggle = component.querySelector("[data-slot=visibility-toggle]")
  if (input && visibilityToggle) {
    visibilityToggle.addEventListener("click", () => {
      const show = visibilityToggle.getAttribute("data-slot-value") === "show"
      visibilityToggle.setAttribute("data-slot-value", show ? "hide" : "show")
      input.setAttribute("type", show ? "password" : "text")
    })
  }
}

const initPasswordField = () => {
  document.querySelectorAll("[data-component=password-field]").forEach(createPasswordField)
}

document.addEventListener("DOMContentLoaded", function () {
  initPasswordField()
})
