// // We are selecting only one because there has to be only one skill dropdown field
// const skillsField = document.querySelector(".treeselect-skills");
// const expertiseField = document.querySelector(".treeselect-expertise")

// const hiddenSkillsField = document.getElementById("selected_skills");
// const hiddenExpertiseField = document.getElementById("selected-expertise");

// function mapOptionsExpertiseToOptions(optionsExpertise) {
//     const newOptions = [];

//     optionsExpertise.forEach(expertiseOption => {
//         const {
//             id,
//             name,
//             parent_id
//         } = expertiseOption;

//         // Find the parent option based on parent_id
//         const parentOption = newOptions.find(option => option.value === parent_id);

//         // Create the new option object
//         const newOption = {
//             name,
//             value: id,
//             children: []
//         };

//         // If parentOption exists, add the new option to its children array
//         if (parentOption) {
//             parentOption.children.push(newOption);
//         } else {
//             // If parentOption doesn't exist, add the new option to the top-level newOptions array
//             newOptions.push(newOption);
//         }
//     });

//     return newOptions;
// }

// function initializeTreeselect(options, domElement) {
//     const treeselect = new Treeselect({
//         parentHtmlContainer: domElement,
//         value: [],
//         options: mapOptionsExpertiseToOptions(options),
//     });

//     treeselect.srcElement.addEventListener('input', (e) => {
//         console.log('Selected value:', e.detail);
//     });

//     return treeselect;
// }

// function getOptionsWithAJAX(url, domElement) {
//     let xmlhttp = new XMLHttpRequest();

//     xmlhttp.onreadystatechange = function () {
//         if (xmlhttp.readyState == XMLHttpRequest.DONE) {
//             if (xmlhttp.status == 200) {
//                 const options = JSON.parse(xmlhttp.responseText);
//                 initializeTreeselect(options, domElement);
//             } else if (xmlhttp.status == 400) {
//                 alert('There was an error 400');
//             } else {
//                 alert('Something else other than 200 was returned');
//             }
//         }
//     };

//     xmlhttp.open("GET", url, true);
//     xmlhttp.send();
// }

// getOptionsWithAJAX("/talent/get-skills/", skillsField);
// let expertiseTreeField = initializeTreeselect([], expertiseField);

// skillsField.addEventListener("input", e => {
//     hiddenSkillsField.value = JSON.stringify(e.detail);

//     const selectedSkills = e.detail;
//     const expertiseURL = "/talent/get-expertise/?selected_skills=" + encodeURIComponent(JSON.stringify(selectedSkills));

//     let xmlhttp = new XMLHttpRequest();

//     xmlhttp.onreadystatechange = function () {
//         if (xmlhttp.readyState == XMLHttpRequest.DONE) {
//             if (xmlhttp.status == 200) {
//                 const options = JSON.parse(xmlhttp.responseText);
//                 expertiseTreeField.destroy();
//                 expertiseTreeField = new Treeselect({
//                     parentHtmlContainer: expertiseField,
//                     value: [],
//                     options: mapOptionsExpertiseToOptions(options),
//                 });

//                 // expertiseTreeField.mount();
//             } else if (xmlhttp.status == 400) {
//                 alert('There was an error 400');
//             } else {
//                 alert('Something else other than 200 was returned');
//             }
//         }
//     };

//     xmlhttp.open("GET", expertiseURL, true);
//     xmlhttp.send();
// });

// expertiseField.addEventListener("input", e => {
//     hiddenExpertiseField.value = JSON.stringify(e.detail);
// });


// Reusable utility function to make an AJAX request
function makeAjaxRequest(url, callback) {
    const xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState === XMLHttpRequest.DONE) {
            if (xmlhttp.status === 200) {
                const response = JSON.parse(xmlhttp.responseText);
                callback(response);
            } else if (xmlhttp.status === 400) {
                alert('There was an error 400');
            } else {
                alert('Something else other than 200 was returned');
            }
        }
    };

    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

// Function to initialize Treeselect
function initializeTreeselect(options, domElement) {
    const treeselect = new Treeselect({
        parentHtmlContainer: domElement,
        value: [],
        options: mapOptionsExpertiseToOptions(options),
    });

    // Kept for debugging purposes
    treeselect.srcElement.addEventListener('input', e => {
        console.log('Selected value:', e.detail);
    });

    return treeselect;
}

// Function to fetch and initialize options using AJAX
function fetchAndInitializeOptions(url, domElement) {
    makeAjaxRequest(url, options => {
        initializeTreeselect(options, domElement);
    });
}

// Function to map expertise options to tree structure
function mapOptionsExpertiseToOptions(optionsExpertise) {
    const newOptions = [];

    optionsExpertise.forEach(expertiseOption => {
        const { id, name, parent_id } = expertiseOption;
        const newOption = { name, value: id, children: [] };
        
        const parentOption = newOptions.find(option => option.value === parent_id);
        if (parentOption) {
            parentOption.children.push(newOption);
        } else {
            newOptions.push(newOption);
        }
    });

    return newOptions;
}

// We are selecting only one because there has to be only one skill dropdown field
const skillsField = document.querySelector(".treeselect-skills");
const expertiseField = document.querySelector(".treeselect-expertise");

const hiddenSkillsField = document.getElementById("selected_skills");
const hiddenExpertiseField = document.getElementById("selected-expertise");

// Fetch and initialize skills options
fetchAndInitializeOptions("/talent/get-skills/", skillsField);

// Since expertise will be selected according to skills, we pass empty array to the options
let expertiseTreeField = initializeTreeselect([], expertiseField);

skillsField.addEventListener("input", e => {
    const selectedSkills = e.detail;
    hiddenSkillsField.value = JSON.stringify(selectedSkills);

    const expertiseURL = "/talent/get-expertise/?selected_skills=" + encodeURIComponent(JSON.stringify(selectedSkills));

    makeAjaxRequest(expertiseURL, options => {
        expertiseTreeField.destroy();
        expertiseTreeField = initializeTreeselect(options, expertiseField);
    });
});

expertiseField.addEventListener("input", e => {
    hiddenExpertiseField.value = JSON.stringify(e.detail);
});
