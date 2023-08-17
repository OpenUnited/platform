// Data to be pulled from the back-end
let optionsSkills = [];

// We are selecting only one because there has to be only one skill dropdown field
const skillsField = document.querySelector(".treeselect-skills");
const expertiseField = document.querySelector(".treeselect-expertise")

const hiddenSkillsField = document.getElementById("selected_skills");
const hiddenExpertiseField = document.getElementById("selected_expertise");

skillsField.addEventListener("input", e => {
    hiddenSkillsField.value = JSON.stringify(e.detail);
});

expertiseField.addEventListener("input", e => {
    hiddenExpertiseField.value = JSON.stringify(e.detail);
});

function mapOptionsExpertiseToOptions(optionsExpertise) {
    const newOptions = [];

    optionsExpertise.forEach(expertiseOption => {
        const {
            id,
            name,
            parent_id
        } = expertiseOption;

        // Find the parent option based on parent_id
        const parentOption = newOptions.find(option => option.value === parent_id);

        // Create the new option object
        const newOption = {
            name,
            value: id,
            children: []
        };

        // If parentOption exists, add the new option to its children array
        if (parentOption) {
            parentOption.children.push(newOption);
        } else {
            // If parentOption doesn't exist, add the new option to the top-level newOptions array
            newOptions.push(newOption);
        }
    });

    return newOptions;
}

function initializeTreeselectForSkills(options, domElement) {

    const treeselect = new Treeselect({
        parentHtmlContainer: domElement,
        value: [],
        options: mapOptionsExpertiseToOptions(optionsSkills),
    })

    treeselect.srcElement.addEventListener('input', (e) => {
        console.log('Selected value:', e.detail)
    });
}

function initializeTreeselectForExpertise(options, domElement) {

    const treeselect = new Treeselect({
        parentHtmlContainer: domElement,
        value: [],
        options: mapOptionsExpertiseToOptions(optionsSkills),
    })

    treeselect.srcElement.addEventListener('input', (e) => {
        console.log('Selected value:', e.detail)
    });
}

function getSkillOptionsWithAJAX() {
    let xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == XMLHttpRequest.DONE) {
            if (xmlhttp.status == 200) {
                optionsSkills = JSON.parse(xmlhttp.responseText);

                initializeTreeselectForSkills(optionsSkills, skillsField);
            } else if (xmlhttp.status == 400) {
                alert('There was an error 400');
            } else {
                alert('Something else other than 200 was returned');
            }
        }
    };

    xmlhttp.open("GET", "/talent/get-skills/", true);
    xmlhttp.send();
}

function getExpertiseOptionsWithAJAX() {
    let xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == XMLHttpRequest.DONE) {
            if (xmlhttp.status == 200) {
                optionsSkills = JSON.parse(xmlhttp.responseText);
                console.log(optionsSkills);
                initializeTreeselectForExpertise(optionsSkills, expertiseField);
            } else if (xmlhttp.status == 400) {
                alert('There was an error 400');
            } else {
                alert('Something else other than 200 was returned');
            }
        }
    };

    xmlhttp.open("GET", "/talent/get-expertise/", true);
    xmlhttp.send();
}

getSkillOptionsWithAJAX();
getExpertiseOptionsWithAJAX();