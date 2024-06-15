function preSetup(data){
    let {index,textElementId, visibleWords} = data;

    let textElement = document.getElementById(`${textElementId}`);
    let fullText = textElement.textContent;
    let words = fullText.split(" ");

    //let initialText = words.slice(0, visibleWords).join(" ") + "...";
    let initialText = words.slice(0, visibleWords).join(" ");
    let remainingText = ""

    if (words.length > visibleWords) {
        remainingText = words.slice(visibleWords).join(" ");
        let span = `<span class="hidden" id="more_text_${index}"> ${remainingText} </span>`
        let dots = `<span class="font-bold" id="three_dots_${index}"> ... </span>`
        textElement.innerHTML = initialText + dots + span;
    }
    else{
        document.getElementById(`read_more_btn_${index}`).classList.add("hidden")
    }

}
function readMoreFunction(index){
    let readMoreBtn = document.getElementById(`read_more_btn_${index}`);
    let moreText = document.getElementById(`more_text_${index}`);
    console.log(moreText)

    if (moreText.classList.contains("hidden")) {
        moreText.classList.remove("hidden");
        document.getElementById(`three_dots_${index}`).classList.add("hidden")
        readMoreBtn.textContent = "Read Less";
    } else {
        document.getElementById(`three_dots_${index}`).classList.remove("hidden")
        moreText.classList.add("hidden")
        readMoreBtn.textContent = "Read More"
    }

}

window.preSetup = preSetup;
window.readMoreFunction = readMoreFunction;
