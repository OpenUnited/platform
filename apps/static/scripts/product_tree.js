function resetTree(event){
    showConfirm({"message":"Create a new Product Tree and lose your changes?"}).then(function(){
        document.getElementById("reset_tree").submit()
    })
}
function editTreeName(event){
    document.getElementById('shareable_product_tree').classList.remove('hidden')
    document.getElementById('shareable_product_tree_name').classList.add('hidden')
}
function copyReferralLink() {
    const copyText = document.getElementById("sharable_link");
    navigator.clipboard.writeText(copyText.value);
    var tooltip = document.getElementById("myTooltip");
    tooltip.innerHTML = "Copied!";
}

function toggleVisibility(event) {
    event.preventDefault()
    const targetElement = event.target.closest("li");
    const ul = targetElement.querySelector("ul");
    const icon = targetElement.querySelector(".icon-arrow");
    if (icon.getAttribute("data-icon")=="circle-chevron-down"){
        icon.setAttribute("data-icon","circle-chevron-right");
        ul.classList.add("hidden");
    }
    else{
        icon.setAttribute("data-icon","circle-chevron-down");
        ul.classList.remove("hidden");
    }
}

function drop(event) {
    let data = event.dataTransfer.getData("text");
    let draggedElement = document.getElementById(data)
    let targetElement = event.target.closest("li")

    let existingUl = targetElement.querySelector("ul");
    let parentUl = targetElement.closest("ul");

    let parentClass = parentUl.className;

    let currentMarginLeft = parseInt(parentClass.match(/pl-([0-9]+)/)[1])
    let childMargin = currentMarginLeft + 4
    let childClass = parentClass.replace(/pl-[0-9]+/, "pl-" + childMargin);

    if (!existingUl) {
        existingUl = document.createElement("ul");
        existingUl.className = childClass;
        targetElement.appendChild(existingUl);
    }
    existingUl.appendChild(draggedElement);
    const targetId = draggedElement.getAttribute("data-id")
    const parentId = targetElement.getAttribute("data-id")
    targetElement.querySelector(".toggleVisibility").classList.remove("hidden")

    const targetUrl = document.getElementById(`li_node_${targetId}`).getAttribute("target_url")
    htmxRequest({
        url: targetUrl,
        method: 'POST',
        values: {
            "has_dropped": true,
            "parent_id": parentId
        }
        }).then(({event, data}) => {
        const parentButton = document.getElementById(`toggleVisibility_${data.target_parent_id}`)
        if (parentButton && data.child_count < 1){
            parentButton.classList.add("hidden");
        }
        }).catch(({event, data}) => {});
}

function allowDrop(event) {
    event.preventDefault();
}

function drag(event) {
    event.dataTransfer.setData("text", event.target.id);
}

function searchTree(event){
    const treeContainer = document.getElementById("product_tree");
    const treeNodes = treeContainer.querySelectorAll("li");
    const searchTerm = event.currentTarget.value.trim().toLowerCase();
    const searchEmptyElement = document.querySelector(".search_empty");

    if (searchTerm === "") {
        searchEmptyElement.classList.add("hidden");
        treeNodes.forEach(function(node) {
            node.classList.remove("hidden");
        });
    }
    else {
        let foundMatch = false;
        treeNodes.forEach(function(node) {
            let textContent = node.textContent.trim().toLowerCase();
            if (textContent.includes(searchTerm)) {
            node.classList.remove("hidden");
            foundMatch = true;
            } else {
            node.classList.add("hidden");
            }
        });

        if (!foundMatch) {
            searchEmptyElement.classList.remove("hidden");
        } else {
            searchEmptyElement.classList.add("hidden");
        }
    }
}

window.resetTree = resetTree;
window.toggleVisibility = toggleVisibility;
window.editTreeName = editTreeName;
window.copyReferralLink = copyReferralLink;
window.drop = drop;
window.allowDrop = allowDrop;
window.drag = drag;
window.searchTree = searchTree;
