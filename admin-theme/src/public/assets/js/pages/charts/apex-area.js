window.ApexCharts = ApexCharts

const getTheme = () => window.themeConfig.theme

let chartSplineArea = null
let chartNegativeValueArea = null
let chartIrregularTimeSeriesArea = null
let chartSelectionResultArea = null
let chartSelectionTargetArea = null

const initSplineChart = () => {
  if (!window.ApexCharts) return

  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
    },
    yaxis: {
      labels: {
        formatter: function (value) {
          return "₹" + value + "K"
        },
      },
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "area",
      height: 380,
      toolbar: {
        show: true,
        tools: {
          download: true,
          zoom: false,
          zoomin: false,
          zoomout: false,
          pan: false,
          reset: false,
        },
      },
      background: "transparent",
    },
    colors: ["#3e5eff", "#FDA403"],
    fill: {
      type: "solid",
      opacity: 0.6,
    },
    stroke: {
      curve: "smooth",
      width: 2,
    },
    dataLabels: {
      enabled: false,
    },
    legend: {
      show: true,
      position: "top",
    },
    series: [
      {
        name: "Basic Plan",
        data: [31, 40, 28, 51, 42, 72, 60],
      },
      {
        name: "Premium Plan",
        data: [11, 32, 45, 32, 34, 52, 41],
      },
    ],
  }

  chartSplineArea = new ApexCharts(document.querySelector("#chart_spline_area"), options)

  chartSplineArea.render()
}

const initNegativeValueChart = () => {
  if (!window.ApexCharts) return

  const negativeDataValues = {
    north: [319, 320, 324, 344, 345, 340, 329, 315, 325, 328],
    northeast: [227, 254, 223, 233, 262, 254, 249, 267, 302, 209],
    midwest: [147, 155, 123, 127, 157, 157, 133, 169, 199, 121],
    west: [168, 91, 48, 20, -1, -37, -88, -130, -90, -78],
  }

  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: Array.from(
        { length: 10 },
        (_, index) => new Date().getFullYear() - index - 1
      ).reverse(),
    },
    yaxis: {
      labels: {
        formatter: function (value) {
          return (value < 0 ? "-" : "") + "₹" + Math.abs(value) + "K"
        },
      },
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "area",
      height: 380,
      toolbar: {
        show: true,
        tools: {
          download: true,
          zoom: false,
          zoomin: false,
          zoomout: false,
          pan: false,
          reset: false,
        },
      },
      background: "transparent",
    },
    colors: ["#3e5eff", "#FFC470", "#67C6E3", "#FFC700"],
    fill: {
      type: "solid",
      opacity: 0.6,
    },
    stroke: {
      curve: "smooth",
      width: 1,
    },
    dataLabels: {
      enabled: false,
    },
    legend: {
      show: true,
      position: "top",
    },
    series: [
      {
        name: "North",
        data: negativeDataValues["north"],
      },
      {
        name: "Northeast",
        data: negativeDataValues["northeast"],
      },
      {
        name: "Midwest",
        data: negativeDataValues["midwest"],
      },
      {
        name: "West",
        data: negativeDataValues["west"],
      },
    ],
  }

  chartNegativeValueArea = new ApexCharts(
    document.querySelector("#chart_negative_value_area"),
    options
  )

  chartNegativeValueArea.render()
}

const initIrregularTimeSeriesChart = () => {
  if (!window.ApexCharts) return

  const dataA = [
    {
      x: new Date("1/1/2025"),
      y: 150,
    },
    {
      x: new Date("1/2/2025"),
      y: 160,
    },
    {
      x: new Date("1/3/2025"),
      y: 145,
    },
    {
      x: new Date("1/4/2025"),
      y: 155,
    },
    {
      x: new Date("1/5/2025"),
      y: 160,
    },
    {
      x: new Date("1/6/2025"),
      y: 150,
    },
    {
      x: new Date("1/7/2025"),
      y: 142,
    },
    {
      x: new Date("1/8/2025"),
      y: 160,
    },
    {
      x: new Date("1/9/2025"),
      y: 148,
    },
  ]

  const dataB = [
    {
      x: new Date("1/5/2025"),
      y: 180,
    },
    {
      x: new Date("1/6/2025"),
      y: 186,
    },
    {
      x: new Date("1/7/2025"),
      y: 200,
    },
    {
      x: new Date("1/8/2025"),
      y: 175,
    },
    {
      x: new Date("1/9/2025"),
      y: 188,
    },
    {
      x: new Date("1/10/2025"),
      y: 195,
    },
    {
      x: new Date("1/11/2025"),
      y: 185,
    },
  ]

  const dataC = [
    {
      x: new Date("1/4/2025"),
      y: 120,
    },
    {
      x: new Date("1/5/2025"),
      y: 135,
    },
    {
      x: new Date("1/6/2025"),
      y: 115,
    },
    {
      x: new Date("1/7/2025"),
      y: 125,
    },
    {
      x: new Date("1/8/2025"),
      y: 130,
    },
  ]

  const options = {
    theme: { mode: getTheme() },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "area",
      height: 380,
      stacked: false,
      toolbar: {
        show: true,
        tools: {
          download: true,
          zoom: false,
          zoomin: false,
          zoomout: false,
          pan: false,
          reset: false,
        },
      },
      background: "transparent",
    },
    xaxis: {
      type: "datetime",
      labels: {
        datetimeUTC: false,
      },
    },
    yaxis: {
      min: 30,
    },
    tooltip: {
      x: {
        format: "dd MMM yyyy",
      },
      y: {
        formatter: (value) => value + " points",
      },
    },
    colors: ["#3e5eff", "#FFC700", "#FFAD84"],
    fill: {
      type: "gradient",
      gradient: {
        shade: getTheme(),
        shadeIntensity: 1,
        opacityFrom: 0.8,
        opacityTo: 0.05,
        stops: [0, 100],
      },
    },
    stroke: {
      curve: "smooth",
      width: 2,
    },
    dataLabels: {
      enabled: false,
    },
    legend: {
      show: true,
      position: "bottom",
      offsetY: 6,
    },
    annotations: {
      yaxis: [
        {
          y: 50,
          borderColor: "#82A0D8",
          label: {
            text: "Support",
            style: {
              color: "#fff",
              background: "#5356FF",
            },
          },
        },
      ],
      xaxis: [
        {
          borderColor: "#82A0D8",
          label: {
            text: "Rally",
            style: {
              color: "#fff",
              background: "#5356FF",
            },
          },
        },
      ],
    },
    series: [
      {
        name: "Product A",
        data: dataA,
      },
      {
        name: "Product B",
        data: dataB,
      },
      {
        name: "Product C",
        data: dataC,
      },
    ],
  }

  chartIrregularTimeSeriesArea = new ApexCharts(
    document.querySelector("#chart_irregular_time_series_area"),
    options
  )

  chartIrregularTimeSeriesArea.render()
}

const initSelectionAreaChart = () => {
  if (!window.ApexCharts) return

  const generateDataSeriesBetweenTwoDates = () => {
    const startingDate = new Date()
    startingDate.setMonth(startingDate.getMonth() - 5)
    let currentIndex = 0
    const data = []
    while (startingDate <= new Date()) {
      data.push({
        x: startingDate.getTime(),
        y: Math.floor(Math.random() * 100),
      })
      startingDate.setDate(startingDate.getDate() + 2)
      currentIndex++
    }

    return data
  }

  const resultOption = {
    theme: {
      mode: getTheme(),
    },
    series: [
      {
        name: "Visitors",
        data: generateDataSeriesBetweenTwoDates(),
      },
    ],
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "area",
      height: 190,
      id: "chart_selection_result_area",
      background: "transparent",
      toolbar: {
        show: true,
        tools: {
          download: true,
          zoom: false,
          zoomin: false,
          zoomout: false,
          pan: false,
          reset: false,
        },
      },
    },
    colors: ["#FDA403"],
    stroke: {
      width: 2,
      curve: "smooth",
    },
    dataLabels: {
      enabled: false,
    },
    fill: {
      opacity: 0.6,
      type: "solid",
    },
    xaxis: {
      type: "datetime",
    },
  }

  const targetOption = {
    series: [
      {
        name: "Visitors",
        data: generateDataSeriesBetweenTwoDates(),
      },
    ],
    theme: {
      mode: getTheme(),
    },
    chart: {
      id: "chart_selection_target_area",
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "area",
      height: 190,
      background: "transparent",
      toolbar: {
        show: true,
        tools: {
          download: true,
          selection: true,
          zoom: false,
          zoomin: false,
          zoomout: false,
          pan: false,
          reset: false,
        },
        autoSelected: "selection",
      },
      brush: {
        enabled: true,
        target: "chart_selection_result_area",
      },
      selection: {
        enabled: true,
        fill: {
          color: "#FDA403",
          opacity: 0.3,
        },
        stroke: {
          width: 2,
          color: "#FDA403",
          opacity: 0.8,
          dashArray: 3,
        },
      },
    },
    colors: ["#3e5eff"],
    dataLabels: {
      enabled: false,
    },
    stroke: {
      width: 2,
      curve: "smooth",
    },
    fill: {
      opacity: 0.6,
      type: "solid",
    },
    xaxis: {
      type: "datetime",
    },
    yaxis: {
      title: { text: "Website Traffic", style: { fontWeight: "500" } },
    },
  }

  chartSelectionResultArea = new ApexCharts(
    document.querySelector("#chart_selection_result_area"),
    resultOption
  )

  chartSelectionTargetArea = new ApexCharts(
    document.querySelector("#chart_selection_target_area"),
    targetOption
  )

  chartSelectionResultArea.render()

  chartSelectionTargetArea.render()
}

const initCharts = () => {
  initSplineChart()
  initNegativeValueChart()
  initIrregularTimeSeriesChart()
  initSelectionAreaChart()
}

document.addEventListener("custom.layout-changed", () => {
  chartSplineArea?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })

  chartNegativeValueArea?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })

  chartIrregularTimeSeriesArea?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })

  chartSelectionResultArea?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })

  chartSelectionTargetArea?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
})

document.addEventListener("DOMContentLoaded", function () {
  initCharts()
})
