const initExample = () => {
  document.getElementById("showcase_i_checkbox").indeterminate = true
  const ratingExample = document.querySelectorAll('#rating_example input[type="checkbox"]')

  ratingExample.forEach((star, index) => {
    star.addEventListener("change", () => {
      ratingExample.forEach((star, i) => {
        star.checked = false
      })
      ratingExample[index].checked = true
    })
  })
}

const initTopBar = () => {
  const topBar = document.getElementById("landing_top_bar")
  const onWindowScroll = () => {
    if (window.scrollY < 30) {
      topBar.classList.add("z-[60]", "border-transparent")
      topBar.classList.remove(
        "z-20",
        "border-b",
        "border-base-content/10",
        "bg-base-100",
        "lg:bg-opacity-90",
        "dark:lg:bg-opacity-95"
      )
    } else {
      topBar.classList.remove("z-[60]", "border-transparent")
      topBar.classList.add(
        "z-20",
        "border-b",
        "border-base-content/10",
        "bg-base-100",
        "lg:bg-opacity-90",
        "dark:lg:bg-opacity-95"
      )
    }
  }
  window.addEventListener("scroll", onWindowScroll)
  onWindowScroll()
}

document.addEventListener("DOMContentLoaded", function () {
  initExample()
  initTopBar()
})
