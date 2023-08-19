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
const skillExpertiseTable = document.getElementById("skill-expertise-table");

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

    const listSkillAndExpertiseURL = "/talent/list-skill-and-expertise/?skills=" + encodeURIComponent(hiddenSkillsField.value) + "&&" + "expertise=" + encodeURIComponent(hiddenExpertiseField.value);

    makeAjaxRequest(listSkillAndExpertiseURL, response => {
        const skillExpertiseTable = document.getElementById("skill-expertise-table");

        if (response.length > 0) {
            skillExpertiseTable.classList.remove("hidden");

            // Clear existing rows before adding new ones
            const tbody = skillExpertiseTable.querySelector("tbody");
            while (tbody.firstChild) {
                tbody.removeChild(tbody.firstChild);
            }

            response.forEach(pair => {
                const newRow = tbody.insertRow();
                
                const skillCell = newRow.insertCell(0);
                skillCell.textContent = pair.skill;
                skillCell.classList.add("py-3.5", "pl-4", "pr-3", "text-left", "text-sm", "font-semibold", "text-gray-900", "sm:pl-0");
                
                const expertiseCell = newRow.insertCell(1);
                expertiseCell.textContent = pair.expertise;
                expertiseCell.classList.add("py-3.5", "pl-4", "pr-3", "text-left", "text-sm", "font-semibold", "text-gray-900", "sm:pl-0");
            });
        } else {
            // Hide the table if there's no data
            skillExpertiseTable.classList.add("hidden");
        }
    });
});
