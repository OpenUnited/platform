import { defineConfig } from "vite"
import injectHTML from "vite-plugin-html-inject"
import { resolve } from "node:path"
import fs from "node:fs"

const getHtmlFiles = (dir) => {
  let results = []
  const list = fs.readdirSync(dir)
  list.forEach((file) => {
    file = resolve(dir, file)
    const stat = fs.statSync(file)
    if (stat && stat.isDirectory()) {
      if (file.endsWith("/partials")) {
        return
      }
      results = results.concat(getHtmlFiles(file))
    } else if (file.endsWith(".html")) {
      results.push(file)
    }
  })
  return results
}

const htmlFiles = getHtmlFiles("src")
const input = Object.fromEntries(
  htmlFiles.map((file) => [
    file.replace(resolve(__dirname, "src"), "").replace(".html", "").replace(/^\//, ""),
    file,
  ])
)

const removecors = () => {
  return {
    name: "remove-cors",
    transformIndexHtml: {
      order: "post",
      handler(html) {
        return html.replace(/crossorigin\s*/g, "")
      },
    },
  }
}

export default defineConfig({
  base: "",
  server: {
    open: "/",
  },
  plugins: [injectHTML(), removecors()],
  root: "src",
  build: {
    outDir: "../html",
    emptyOutDir: true,
    rollupOptions: {
      input,
      output: {
        entryFileNames: `assets/[name].js`,
        chunkFileNames: `assets/[name].js`,
        assetFileNames: `assets/[name].[ext]`
      }
    },
  },
})
