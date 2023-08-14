let fullNameField = document.getElementById("id_0-full_name");
let preferredNameField = document.getElementById("id_0-preferred_name");

fullNameField.addEventListener("input", event => {
    preferredNameField.value = fullNameField.value.split(" ")[0];
});