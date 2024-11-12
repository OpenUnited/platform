// // Select - Choices
if (window.Choices) {
  if (document.querySelector("[data-choice]")) new window.Choices("[data-choice]", {allowHTML: true})
}

// // File Upload - FilePond
if (window.FilePond) {
  if (window.FilePondPluginImagePreview) {
    FilePond.registerPlugin(FilePondPluginImagePreview)
  }

  document.querySelectorAll("[data-component=filepond]").forEach((fp) => {
    window.FilePond.create(fp, { credits: false })
  })
}

class LayoutCustomizer {
  constructor() {
    this.defaultConfig = {
      theme: "dark",
      leftbar: {
        hide: false,
        type: "full",
      },
    }
    const configCache = localStorage.getItem("__NEXUS__HTML__ADMIN__LAYOUT__")
    if (configCache) {
      this.config = JSON.parse(configCache)
    } else {
      this.config = this.defaultConfig
    }
    this.html = document.querySelector("html")

    window.themeConfig = this.config
  }

  notifyLayoutChanges = () => {
    const themeEvent = new Event("custom.layout-changed")

    document.dispatchEvent(themeEvent)
  }

  updateTheme = () => {
    localStorage.setItem("__NEXUS__HTML__ADMIN__LAYOUT__", JSON.stringify(this.config))

    if (this.config.theme === "dark") {
      this.html.classList.add("dark")
    } else {
      this.html.classList.remove("dark")
    }
    this.html.setAttribute("data-theme", this.config.theme)
    if (this.config.leftbar.hide) {
      this.html.setAttribute("data-leftbar-hide", "")
    } else {
      this.html.removeAttribute("data-leftbar-hide")
    }
    this.html.setAttribute("data-leftbar-type", this.config.leftbar.type)
  }

  initEventListener = () => {
    const themeToggleBtn = document.querySelectorAll("[data-action=theme-toggle]")
    themeToggleBtn.forEach((toggle) => {
      toggle.addEventListener("click", () => {
        this.config.theme = this.config.theme === "light" ? "dark" : "light"
        this.updateTheme()
        this.notifyLayoutChanges()
      })
    })
  }

  initLeftmenu = () => {
    const initLeftmenuHandler = () => {
      const leftbarToggle = document.querySelector("[data-action=leftbar-toggle]")
      leftbarToggle?.addEventListener("click", () => {
        this.config.leftbar.hide = !this.config.leftbar.hide
        this.updateTheme()
      })
    }

    const initMenuResizer = () => {
      const resizeFn = () => {
        this.config.leftbar.type = window.innerWidth < 1023 ? "mobile" : "full"
        this.config.leftbar.hide = this.config.leftbar.type === "mobile"
        this.updateTheme()
      }
      window.addEventListener("resize", resizeFn)
      resizeFn()
    }

    const initLeftbarBackdrop = () => {
      const leftbarToggle = document.querySelector(".leftbar-backdrop")
      leftbarToggle?.addEventListener("click", () => {
        this.config.leftbar.hide = true
        this.updateTheme()
      })
    }

    const initMenuActivation = () => {
      const menuItems = document.querySelectorAll(".leftmenu-wrapper .menu a")
      let currentURL = window.location.href
      if (window.location.pathname === "/") {
        currentURL += "dashboards-ecommerce"
      }
      menuItems.forEach((item) => {
        if (item.href === currentURL) {
          item.classList.add("active")
          const detailEl = item.parentElement.parentElement.parentElement
          if (detailEl && detailEl.tagName.toLowerCase() === "details") {
            detailEl.setAttribute("open", "")
          }
          const detailEl2 = detailEl.parentElement.parentElement.parentElement
          if (detailEl2 && detailEl2.tagName.toLowerCase() === "details") {
            detailEl2.setAttribute("open", "")
          }
        }
      })
    }

    const scrollToActiveMenu = () => {
      const simplebarEl = document.querySelector(".leftmenu-wrapper [data-simplebar]")
      const activatedItem = document.querySelector(".leftmenu-wrapper .menu a.active")
      if (simplebarEl && activatedItem) {
        const simplebar = new SimpleBar(simplebarEl)
        const top = activatedItem?.getBoundingClientRect().top
        if (top && top !== 0) {
          simplebar.getScrollElement().scrollTo({ top: top - 300, behavior: "smooth" })
        }
      }
    }

    initLeftmenuHandler()
    initMenuResizer()
    initLeftbarBackdrop()
    initMenuActivation()
    scrollToActiveMenu()
  }

  afterInit = () => {
    this.initEventListener()
    this.initLeftmenu()
  }

  init = () => {
    this.updateTheme()
    window.addEventListener("DOMContentLoaded", this.afterInit)
  }
}

new LayoutCustomizer().init()
