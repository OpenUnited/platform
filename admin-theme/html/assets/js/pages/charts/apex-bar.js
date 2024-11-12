const getTheme = () => window.themeConfig.theme

let chartWithGoalsBar = null
let chartGroupedBar = null
let chartStackedBar = null
let chartNegativeValuedBar = null

const initWithGoalsChart = () => {
  if (!window.ApexCharts) return
  const seriesDataWithYaxisAndGoalValue = [
    {
      y: 488,
      goals: {
        name: "Predicted Sales",
        value: 680,
        strokeDashArray: 2,
      },
    },
    {
      y: 680,
      goals: {
        name: "Predicted Sales",
        value: 710,
        strokeDashArray: 2,
      },
    },
    {
      y: 722,
      goals: {
        name: "Predicted Sales",
        value: 680,
      },
    },
    {
      y: 539,
      goals: {
        name: "Predicted Sales",
        value: 594,
        strokeDashArray: 2,
      },
    },
    {
      y: 461,
      goals: {
        name: "Predicted Sales",
        value: 397,
      },
    },
    {
      y: 322,
      goals: {
        name: "Predicted Sales",
        value: 300,
      },
    },
  ]

  const currentYear = new Date().getFullYear()
  const seriesWithGoals = seriesDataWithYaxisAndGoalValue.map((data, index) => ({
    ...data,
    x: (currentYear - index).toString(),
    goals: [{ ...data.goals, strokeWidth: 6, strokeColor: "#EB6440" }],
  }))

  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      type: "numeric",
      title: { text: "(Million USD)", style: { fontWeight: "500" } },
      labels: {
        formatter: (value) => value + "M",
      },
    },
    tooltip: {
      y: {
        formatter: (value) => value + "M",
      },
    },
    grid: {
      show: false,
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "bar",
      height: 380,
      toolbar: {
        show: true,
      },
      background: "transparent",
    },
    colors: ["#3e5eff"],
    fill: {
      type: "solid",
    },
    legend: {
      show: true,
      showForSingleSeries: true,
    },
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: 28,
      },
    },
    series: [
      {
        name: "Total Sales",
        data: seriesWithGoals,
      },
    ],
  }

  chartWithGoalsBar = new ApexCharts(document.querySelector("#chart_with_goals_bar"), options)

  chartWithGoalsBar.render()
}

const initGroupedChart = () => {
  if (!window.ApexCharts) return
  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: ["Atlas", "Phoenix", "Zenith", "Forge"],
      title: {
        text: "Expense Breakdown",
        style: { fontWeight: "500" },
      },
      labels: {
        formatter: (value) => value + "K",
      },
    },
    grid: {
      show: false,
    },
    stroke: {
      show: true,
      width: 1,
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
    tooltip: {
      shared: true,
      intersect: false,
      y: {
        formatter: (value) => value + "K",
      },
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "bar",
      height: 380,
      toolbar: {
        show: true,
      },
      background: "transparent",
    },
    colors: ["#3e5eff", "#FDA403", "#FB6D48", "#8E7AB5"],
    fill: {
      type: "solid",
    },
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: 14,
      },
    },
    series: [
      {
        name: "Labor",
        data: [122, 215, 180, 210],
      },
      {
        name: "Material",
        data: [158, 169, 143, 133],
      },
      {
        name: "Marketing",
        data: [146, 98, 123, 111],
      },
      {
        name: "Travel",
        data: [59, 42, 71, 28],
      },
    ],
  }

  chartGroupedBar = new ApexCharts(document.querySelector("#chart_grouped_bar"), options)

  chartGroupedBar.render()
}

const initStackedChart = () => {
  if (!window.ApexCharts) return

  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: ["Alabama", "Florida", "Georgia", "Nevada", "Texas", "South Carolina"],
      title: {
        text: "Regional Ratio Of Sale",
        style: { fontWeight: "500" },
      },
      labels: {
        formatter: (value) => value + "%",
      },
    },
    grid: {
      show: false,
    },
    yaxis: {},
    tooltip: {
      shared: true,
      intersect: false,
      y: {
        formatter: (value) => value + "%",
      },
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "bar",
      height: 380,
      toolbar: {
        show: true,
      },
      background: "transparent",
      stacked: true,
      stackType: "100%",
    },
    colors: ["#3e5eff", "#FB6D48", "#A25772", "#FDA403", "#8E7AB5"],
    fill: {
      type: "solid",
    },
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: 28,
      },
    },
    series: [
      {
        name: "Clothing",
        data: [12, 34, 20, 27, 22, 14],
      },
      {
        name: "Electronics",
        data: [24, 20, 12, 18, 23, 8],
      },
      {
        name: "Homeware",
        data: [10, 18, 9, 10, 21, 29],
      },
      {
        name: "Cosmetics",
        data: [28, 18, 39, 40, 25, 30],
      },
      {
        name: "Toys",
        data: [26, 10, 20, 5, 9, 19],
      },
    ],
  }

  chartStackedBar = new ApexCharts(document.querySelector("#chart_stacked_bar"), options)

  chartStackedBar.render()
}

const initNegativeValueChart = () => {
  if (!window.ApexCharts) return

  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: [
        "Smart Watches",
        "Wireless Headphones",
        "Earbuds",
        "Wired Earphones",
        "Speakers",
        "Soundbars",
        "Personalised Products",
        "Accessories",
      ],
      title: {
        text: "Product Review Sentiment",
        style: { fontWeight: "500" },
      },
      labels: {
        formatter: (value) => Math.abs(Number(value)).toString(),
      },
    },
    dataLabels: {
      formatter: (value) => Math.abs(Number(value)).toString(),
    },
    tooltip: {
      shared: false,
      y: {
        formatter: (val) => Math.abs(val).toString() + " Reviews",
      },
    },
    grid: {
      show: false,
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "bar",
      height: 380,
      toolbar: {
        show: true,
      },
      background: "transparent",
      stacked: true,
    },
    colors: ["#3e5eff", "#FDA403"],
    fill: {
      type: "solid",
    },
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: 28,
      },
    },
    series: [
      {
        name: "Positive",
        data: [379, 293, 411, 387, 242, 434, 321, 357],
      },
      {
        name: "Negative",
        data: [151, 208, 90, 113, 268, 76, 189, 88].map((value) => -value),
      },
    ],
  }

  chartNegativeValuedBar = new ApexCharts(
    document.querySelector("#chart_negative_value_bar"),
    options
  )

  chartNegativeValuedBar.render()
}

const initCharts = () => {
  initWithGoalsChart()
  initGroupedChart()
  initStackedChart()
  initNegativeValueChart()
}

document.addEventListener("custom.layout-changed", () => {
  chartWithGoalsBar?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  chartGroupedBar?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
  })
  chartStackedBar?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  chartNegativeValuedBar?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
})

document.addEventListener("DOMContentLoaded", function () {
  initCharts()
})
