const getTheme = () => window.themeConfig.theme

let charStackedColumn = null
let chartDumbbellColumn = null
let chartRangeColumn = null
let chartDynamicLoadingColumn = null
let chartDynamicLoadingTargetColumn = null

const initChartStackedColumn = () => {
  if (!window.ApexCharts) return
  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
      title: {
        text: "Monthly Cart Abandoned Count",
        style: { fontWeight: "500" },
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
    colors: ["#3e5eff", "#A25772", "#FB6D48", "#FDA403", "#8E7AB5"],
    fill: {
      type: "solid",
    },
    tooltip: {
      shared: true,
      intersect: false,
      inverseOrder: true,
    },
    plotOptions: {
      bar: {
        columnWidth: 40,
        borderRadius: 8,
        dataLabels: {
          total: {
            enabled: true,
            offsetY: -8,
            style: {
              color: "#FFA299",
            },
          },
        },
      },
    },
    series: [
      {
        name: "Cart",
        data: [847, 723, 848, 573, 842, 973, 874, 942],
      },
      {
        name: "Checkout",
        data: [984, 697, 473, 784, 993, 824, 914, 973],
      },
      {
        name: "Shipping",
        data: [423, 673, 324, 473, 424, 347, 384, 442],
      },
      {
        name: "Payment",
        data: [384, 297, 362, 392, 427, 534, 377, 442],
      },
      {
        name: "Review",
        data: [642, 417, 304, 617, 439, 527, 689, 773],
      },
    ],
  }

  charStackedColumn = new ApexCharts(document.querySelector("#chart_stacked_column"), options)

  charStackedColumn.render()
}

const initChartDumbbellColumn = () => {
  if (!window.ApexCharts) return
  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      tickPlacement: "on",
      title: {
        text: "Average Delivery Time (Days)",
        style: { fontWeight: "500" },
      },
    },
    yaxis: {
      min: 0,
      max: 10,
    },
    grid: {
      xaxis: {
        lines: {
          show: true,
        },
      },
      yaxis: {
        lines: {
          show: false,
        },
      },
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
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
      type: "rangeBar",
    },
    fill: {
      type: "gradient",
      gradient: {
        type: "vertical",
        gradientToColors: ["#FB6D48"],
        inverseColors: true,
        stops: [0, 100],
      },
    },
    plotOptions: {
      bar: {
        columnWidth: 3,
        isDumbbell: true,
        dumbbellColors: [["#3e5eff", "#FB6D48"]],
      },
    },
    labels: ["Min Delivery Days", "Max Delivery Days"],
    legend: {
      show: true,
      showForSingleSeries: true,
      position: "bottom",
      horizontalAlign: "center",
      customLegendItems: ["Min Delivery Days", "Max Delivery Days"],
      markers: {
        fillColors: ["#3e5eff", "#FB6D48"],
      },
    },
    series: [
      {
        data: [
          {
            x: "California",
            y: [2, 4],
          },
          {
            x: "Nevada",
            y: [2, 5],
          },
          {
            x: "New York",
            y: [1, 2],
          },
          {
            x: "Arizona",
            y: [1, 4],
          },
          {
            x: "Vermont",
            y: [2, 9],
          },
          {
            x: "Texas",
            y: [3, 6],
          },
          {
            x: "Ohio",
            y: [4, 7],
          },
          {
            x: "Tennessee",
            y: [2, 8],
          },
        ],
      },
    ],
  }

  chartDumbbellColumn = new ApexCharts(document.querySelector("#chart_dumbbell_column"), options)

  chartDumbbellColumn.render()
}

const initChartRangeColumn = () => {
  if (!window.ApexCharts) return
  const xAxisLabel = ["Jan", "Feb", "Mar", "Apr", "May"]
  const yAxisUsers = [
    [3, 5],
    [2, 6],
    [4, 6],
    [3, 7],
    [2, 7],
  ]
  const yAxisPremiumSubscriber = [
    [2, 3],
    [2, 4],
    [2, 4],
    [1, 5],
    [1, 3],
  ]

  const options = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      title: {
        text: "Customer Churn Rate (%)",
        style: { fontWeight: "500" },
      },
    },
    yaxis: {
      min: 0,
    },
    tooltip: {
      y: {
        formatter: (val) => val + "%",
      },
    },
    legend: {
      position: "top",
    },
    grid: {
      show: false,
    },
    stroke: {
      show: true,
      width: 1,
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      height: 380,
      toolbar: {
        show: true,
      },
      type: "rangeBar",
      background: "transparent",
    },
    colors: ["#3e5eff", "#FDA403"],
    fill: {
      type: "solid",
    },
    plotOptions: {
      bar: {
        columnWidth: 40,
      },
    },
    dataLabels: {
      enabled: true,
      formatter: (val, opts) => {
        const dataValue = opts.w.config.series[opts.seriesIndex].data[opts.dataPointIndex].y
        return dataValue[1] - dataValue[0] + "%"
      },
    },
    series: [
      {
        name: "User",
        data: xAxisLabel.map((label, index) => ({
          x: label,
          y: yAxisUsers[index],
        })),
      },
      {
        name: "Premium Subscriber",
        data: xAxisLabel.map((label, index) => ({
          x: label,
          y: yAxisPremiumSubscriber[index],
        })),
      },
    ],
  }

  chartRangeColumn = new ApexCharts(document.querySelector("#chart_range_column"), options)

  chartRangeColumn.render()
}

const initChartDynamicLoadingColumn = () => {
  if (!window.ApexCharts) return
  let selectedLoadingSeriesIndexes = []

  const seriesOptions = {
    labels: Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i),
    colors: ["#3e5eff", "#A25772", "#FB6D48", "#FDA403", "#8E7AB5"],
    data: [
      [987, 1155, 892, 1038],
      [812, 907, 835, 1018],
      [685, 793, 715, 878],
      [603, 689, 648, 821],
      [529, 658, 574, 703],
    ],
  }

  const dynamicLoadingOptions = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: seriesOptions.labels,
      title: {
        text: "Yearly Production",
        style: { fontWeight: "500" },
        offsetY: 15,
      },
    },
    yaxis: {
      labels: {
        show: false,
      },
    },
    legend: {
      show: false,
    },
    dataLabels: {
      enabled: true,
      offsetX: 10,
      formatter: (val, opts) => {
        return opts.w.globals.labels[opts.dataPointIndex]
      },
    },
    states: {
      normal: {
        filter: {
          type: "desaturate",
        },
      },
    },
    tooltip: {
      x: {
        show: false,
      },
      y: {
        title: {
          formatter: () => "",
        },
        formatter: (val) => {
          return val.toString() + " Units"
        },
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
    chart: {
      type: "bar",
      height: 380,
      toolbar: {
        show: true,
      },
      background: "transparent",
      stacked: true,
      events: {
        mounted: (c) => c.windowResizeHandler(),
        dataPointSelection: (e, chart, options) => {
          if (selectedLoadingSeriesIndexes.includes(options.dataPointIndex)) {
            selectedLoadingSeriesIndexes = selectedLoadingSeriesIndexes.filter(
              (arr) => arr !== options.dataPointIndex
            )
          } else {
            selectedLoadingSeriesIndexes = [...selectedLoadingSeriesIndexes, options.dataPointIndex]
          }

          if (selectedLoadingSeriesIndexes.length === 0) {
            document
              .getElementById("container_chart_dynamic_loading_target_column")
              .classList.add("hidden")
          } else {
            document
              .getElementById("container_chart_dynamic_loading_target_column")
              .classList.remove("hidden")
          }

          chartDynamicLoadingTargetColumn?.updateOptions({
            series: selectedLoadingSeriesIndexes.map((value) => {
              return {
                name: seriesOptions.labels[value].toString(),
                color: seriesOptions.colors[value],
                data: seriesOptions.data[value],
              }
            }),
          })

          chart.windowResizeHandler()
        },
      },
    },
    colors: seriesOptions.colors,
    fill: {
      type: "solid",
    },
    plotOptions: {
      bar: {
        distributed: true,
        horizontal: true,
        dataLabels: {
          position: "bottom",
        },
      },
    },
    series: [
      {
        data: [4072, 3572, 3071, 2761, 2464],
      },
    ],
  }

  const dynamicLoadingTargetOptions = {
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: ["Q1", "Q2", "Q3", "Q4"],
      title: {
        text: "Quarterly Production",
        style: { fontWeight: "500" },
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
    yaxis: {
      max: (max) => Math.ceil((max + Math.ceil(max / 10)) / 500) * 500,
    },
    fill: {
      type: "solid",
    },
    plotOptions: {
      bar: {
        columnWidth: 30,
        borderRadius: 6,
        dataLabels: {
          total: {
            enabled: true,
            offsetY: -1,
            style: {
              color: "#FFA299",
            },
          },
        },
      },
    },
    tooltip: {
      y: {
        formatter: (val) => val + " Units",
      },
    },
    legend: {
      show: false,
    },
    series: [],
  }

  chartDynamicLoadingTargetColumn = new ApexCharts(
    document.querySelector("#chart_dynamic_loading_target_column"),
    dynamicLoadingTargetOptions
  )

  chartDynamicLoadingTargetColumn.render()

  chartDynamicLoadingColumn = new ApexCharts(
    document.querySelector("#chart_dynamic_loading_column"),
    dynamicLoadingOptions
  )

  chartDynamicLoadingColumn.render()
}

const initCharts = () => {
  initChartStackedColumn()
  initChartDumbbellColumn()
  initChartRangeColumn()
  initChartDynamicLoadingColumn()
}

document.addEventListener("custom.layout-changed", () => {
  charStackedColumn?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
  })
  chartDumbbellColumn?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  chartRangeColumn?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
  })
  chartDynamicLoadingColumn?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    stroke: {
      colors: [getTheme() === "light" ? "#fff" : "#000"],
    },
  })
  chartDynamicLoadingTargetColumn?.updateOptions({
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
