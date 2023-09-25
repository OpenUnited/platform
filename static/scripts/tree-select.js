const skillsField = document.querySelector(".treeselect-skills");
const expertiseField = document.querySelector(".treeselect-expertise");

// These two are hidden input fields that hold the ids of skill and expertise objects
const hiddenSkillsField = document.getElementById("selected-skills");
const hiddenExpertiseField = document.getElementById("selected-expert");

const skillExpertiseTable = document.getElementById("skill-expertise-table");

// Fetch and initialize skills and expertise options
let skillTreeSelectField = fetchAndInitializeSkillField("/talent/get-skills/", "/talent/get-current-skills/", skillsField);
let expertiseTreeSelectField = fetchAndInitializeExpertiseField("/talent/get-current-expertise/", expertiseField);

// Everytime a user makes changes on the skills input, we update the related expertise options
skillsField.addEventListener("input", e => updateExpertiseField(e));

// When expertise is selected, we add skill - expertise pair to the table
expertiseField.addEventListener("input", e => updateSkillAndExpertiseTable(e));

async function updateSkillAndExpertiseTable(event) {
    hiddenExpertiseField.value = JSON.stringify(event.detail);
    const listSkillAndExpertiseURL = "/talent/list-skill-and-expertise/?skills=" + encodeURIComponent(hiddenSkillsField.value) + "&&" + "expertise=" + encodeURIComponent(hiddenExpertiseField.value);

    const response = await fetchData(listSkillAndExpertiseURL);
    const skillExpertiseTable = document.getElementById("skill-expertise-table");

    // In case we don't want to list skill-expertise pairs
    if (skillExpertiseTable) {
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
    }
}

function createTreeSelect(domElement, initValues, options) {
    return new Treeselect({
        parentHtmlContainer: domElement,
        value: initValues,
        options: mapOptionsExpertiseToOptions(options),
    });
}

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

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            console.log(response);
            throw new Error("Network response was not OK");
        }
        return response.json();
    }
    catch (error) {
        console.log("Fetch error:", error);
        throw error;
    }
}

async function fetchAndInitializeSkillField(getSkillsURL, getSelectedSkillsURL, domElement) {
    const skillOptions = await fetchData(getSkillsURL);
    const selectedSkillOptions = await fetchData(getSelectedSkillsURL);

    hiddenSkillsField.value = JSON.stringify(selectedSkillOptions);
    return createTreeSelect(domElement, selectedSkillOptions, skillOptions);
}

async function fetchAndInitializeExpertiseField(getSelectedExpertiseURL, domElement) {
    const response = await fetchData(getSelectedExpertiseURL);

    hiddenExpertiseField.value = JSON.stringify(response.expertiseIDList);
    return createTreeSelect(domElement, response.expertiseIDList, response.expertiseList);
}

async function fetchAndUpdateExpertiseField(expertiseTreeSelectField, getExpertiseURL, domElement) {
    Promise.resolve(expertiseTreeSelectField).then(field => field.destroy());
    const response = await fetchData(getExpertiseURL);

    return createTreeSelect(domElement, response.expertiseIDList, response.expertiseList);
}

async function updateExpertiseField(event) {
    const selectedSkills = event.detail;
    hiddenSkillsField.value = JSON.stringify(selectedSkills);

    const expertiseURL = "/talent/get-expertise/?selected_skills=" + encodeURIComponent(JSON.stringify(selectedSkills));
    expertiseTreeSelectField = await fetchAndUpdateExpertiseField(expertiseTreeSelectField, expertiseURL, expertiseField);
}
