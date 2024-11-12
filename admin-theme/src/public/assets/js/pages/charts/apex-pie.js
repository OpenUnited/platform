const getTheme = () => window.themeConfig.theme

let chartSimplePie = null
let chartGradientDonut = null
let chartPatternDonut = null
let chartMonochromePie = null

const initCharSimplePie = () => {
  if (!window.ApexCharts) return

  const options = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "pie",
      height: 380,
      toolbar: {
        show: false,
      },
      background: "transparent",
    },
    theme: { mode: getTheme() },
    stroke: {
      show: true,
      width: 1,
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
    title: {
      text: "Website Traffic",
      style: { fontWeight: "500" },
      align: "right",
    },
    tooltip: {
      enabled: true,
      y: {
        formatter: (value) => value + " Visitors",
      },
    },
    labels: ["Search", "Direct", "Referral", "Social", "Webinars", "Advertisement"],
    colors: ["#3e5eff", "#FDA403", "#FB6D48", "#A25772", "#8E7AB5", "#FFA299"],
    series: [428, 180, 88, 209, 91, 52],
  }

  chartSimplePie = new ApexCharts(document.querySelector("#chart_simple_pie"), options)

  chartSimplePie.render()
}

const initCharGradientDonut = () => {
  if (!window.ApexCharts) return

  const gradientDonutSeriesData = [50, 30, 40, 20, 25, 15, 10]

  const options = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "donut",
      height: 380,
      toolbar: {
        show: false,
      },
      background: "transparent",
    },
    theme: {
      mode: getTheme(),
    },
    title: {
      text: "Marketing Budget",
      style: { fontWeight: "500" },
      align: "right",
    },
    stroke: {
      show: true,
      width: 1,
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
    fill: {
      type: "gradient",
      gradient: {
        shade: getTheme(),
        shadeIntensity: getTheme() === "light" ? 0.4 : 0.25,
      },
    },
    plotOptions: {
      pie: {
        startAngle: -45,
        endAngle: 315,
        donut: {
          size: "60%",
          labels: {
            show: true,
            value: {
              formatter: (value) => "$" + value + "K",
            },
            total: {
              show: true,
              color: "#FF4560",
              formatter: () =>
                "$" + gradientDonutSeriesData.reduce((acc, cur) => acc + cur, 0) + "K",
            },
          },
        },
      },
    },
    tooltip: {
      enabled: true,
      y: {
        formatter: (value) => "$" + value + "K",
      },
    },
    responsive: [
      {
        breakpoint: 480,
        options: {
          chart: {
            width: 200,
          },
          legend: {
            position: "bottom",
          },
        },
      },
    ],
    labels: [
      "Content",
      "Social Media",
      "SEO",
      "Paid Display",
      "Affiliate",
      "Magazine",
      "Promotional Items",
    ],
    colors: ["#3e5eff", "#FDA403", "#FB6D48", "#A25772", "#8E7AB5", "#FFA299", "#E3C878"],
    series: gradientDonutSeriesData,
  }

  chartGradientDonut = new ApexCharts(document.querySelector("#chart_gradient_donut"), options)

  chartGradientDonut.render()
}

const initChartPatternDonut = () => {
  if (!window.ApexCharts) return

  const patternDonutSeriesData = [2512, 1003, 2009, 4322, 521]

  const options = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "donut",
      height: 380,
      toolbar: {
        show: false,
      },
      background: "transparent",
      dropShadow: {
        enabled: true,
        color: "#111",
        top: -1,
        left: 3,
        blur: 3,
        opacity: 0.2,
      },
    },
    theme: {
      mode: getTheme(),
    },
    title: {
      text: "Inventory",
      style: { fontWeight: "500" },
      align: "right",
      offsetX: -24,
    },
    legend: {
      position: "right",
    },
    stroke: {
      show: true,
      width: 1,
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
    fill: {
      type: "pattern",
      pattern: {
        style: ["squares", "verticalLines", "slantedLines", "circles", "horizontalLines"],
        width: 4,
        height: 4,
        strokeWidth: 1,
      },
    },
    plotOptions: {
      pie: {
        startAngle: -45,
        endAngle: 315,
        donut: {
          size: "60%",
          labels: {
            show: true,
            value: {
              formatter: (value) => value + " Units",
            },
            total: {
              show: true,
              color: "#FF4560",
              formatter: () => patternDonutSeriesData.reduce((acc, cur) => acc + cur, 0) + " Units",
            },
          },
        },
      },
    },
    tooltip: {
      enabled: true,
      y: {
        formatter: (value) => value + " Units",
      },
    },
    labels: ["Smartwatch", "Smartphone", "Tablet", "Headphone", "Laptop"],
    colors: ["#3e5eff", "#FB6D48", "#FDA403", "#A25772", "#8E7AB5"],
    series: patternDonutSeriesData,
  }

  chartPatternDonut = new ApexCharts(document.querySelector("#chart_pattern_donut"), options)

  chartPatternDonut.render()
}

const initChartMonochromePie = () => {
  if (!window.ApexCharts) return

  const options = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "donut",
      height: 380,
      toolbar: {
        show: false,
      },
      background: "transparent",
    },
    theme: {
      mode: getTheme(),
      monochrome: {
        enabled: true,
        color: "#3e5eff",
        shadeTo: "light",
        shadeIntensity: 0.8,
      },
    },
    stroke: {
      show: true,
      width: 1,
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
    title: {
      text: "App Downloads",
      style: { fontWeight: "500" },
      align: "right",
    },
    tooltip: {
      enabled: true,
      y: {
        formatter: (value) => value + " Downloads",
      },
    },
    labels: ["Android", "iOS", "Windows", "MacOS", "Amazon FireOS"],
    series: [39243, 22187, 6947, 3375, 2688],
  }
  chartMonochromePie = new ApexCharts(document.querySelector("#chart_monochrome_pie"), options)

  chartMonochromePie.render()
}

const initCharts = () => {
  initCharSimplePie()
  initCharGradientDonut()
  initChartPatternDonut()
  initChartMonochromePie()
}

document.addEventListener("custom.layout-changed", () => {
  chartSimplePie?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
  })
  chartGradientDonut?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
    fill: {
      gradient: {
        shade: getTheme(),
        shadeIntensity: getTheme() === "light" ? 0.4 : 0.25,
      },
    },
  })
  chartPatternDonut?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
  })
  chartMonochromePie?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
  })
})

document.addEventListener("DOMContentLoaded", function () {
  initCharts()
})
