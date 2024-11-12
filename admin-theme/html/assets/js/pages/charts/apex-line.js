const getTheme = () => window.themeConfig.theme

let chartLabelLine = null
let chartStepLine = null
let chartOrderSyncingLine = null
let chartOrderRevenueSyncingLine = null
let chartOrderAverageSyncingLine = null
let chartAnnotationLine = null

const monthNames = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
]

const initChartLabelLine = () => {
  if (!window.ApexCharts) return

  const options = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "line",
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
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: ["Jan", "Feb", "Mar", "Apr", "May"],
      title: {
        text: "Monthly Revenue by Platform",
        style: { fontWeight: "500" },
      },
    },
    yaxis: {
      labels: {
        formatter: (value) => (value / 100).toFixed(0) + "K",
        offsetX: -5,
      },
      min: 3000,
    },
    stroke: {
      curve: "smooth",
      width: 2,
    },
    dataLabels: {
      enabled: true,
      formatter: (value) => (Number(value) / 100).toFixed(0),
      background: {
        borderColor: getTheme() === "light" ? "#fff" : "#000",
      },
    },
    tooltip: {
      y: {
        formatter: (value) => "$" + (Number(value) / 100).toFixed(2) + "K",
      },
    },
    colors: ["#3e5eff", "#A25772", "#FB6D48", "#FDA403"],
    series: [
      {
        name: "eBay",
        data: [12105, 11562, 10697, 12126, 12817, 12070, 12403, 12758],
      },
      {
        name: "Walmart",
        data: [8866, 9566, 8821, 8799, 9272, 9109, 9272, 8601],
      },
      {
        name: "Amazon",
        data: [7680, 7685, 7293, 6952, 6568, 7572, 6538, 6498],
      },
      {
        name: "Best Buy",
        data: [4537, 5892, 4271, 4923, 5186, 4419, 5548, 4720],
      },
    ],
  }

  chartLabelLine = new ApexCharts(document.querySelector("#chart_label_line"), options)

  chartLabelLine.render()
}

const initChartStepLine = () => {
  if (!window.ApexCharts) return

  const generateStepLineData = () => {
    let currentMonth = new Date().getMonth()
    const pastMonthWithQuarter = []
    while (pastMonthWithQuarter.length < 10) {
      if (pastMonthWithQuarter.length === 0 && new Date().getDate() > 15) {
        pastMonthWithQuarter.push(monthNames[currentMonth] + "-1")
      } else if (currentMonth !== new Date().getMonth()) {
        pastMonthWithQuarter.push(monthNames[currentMonth] + "-2")
        if (pastMonthWithQuarter.length !== 10) {
          pastMonthWithQuarter.push(monthNames[currentMonth] + "-1")
        }
      }
      currentMonth -= 1
      if (currentMonth === -1) {
        currentMonth = 11
      }
    }

    return pastMonthWithQuarter.reverse()
  }

  const stepLineXAxisLabels = generateStepLineData()

  const options = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "line",
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
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: stepLineXAxisLabels,
      title: {
        text: "Customer Support Ticket Volume",
        style: { fontWeight: "500" },
      },
    },
    tooltip: {
      y: {
        formatter: (val) => val + " Tickets",
      },
    },
    stroke: {
      curve: "stepline",
      width: 2,
    },
    colors: ["#3e5eff"],
    series: [
      {
        name: "Volume",
        data: [144, 154, 121, 112, 143, 233, 223, 166, 166, 158],
      },
    ],
  }

  chartStepLine = new ApexCharts(document.querySelector("#chart_step_line"), options)

  chartStepLine.render()
}

const initChartSyncingLine = () => {
  if (!window.ApexCharts) return

  const syncingLineXAxisOption = {
    type: "datetime",
    categories: [
      new Date("1/1/2025").getTime(),
      new Date("1/2/2025").getTime(),
      new Date("1/3/2025").getTime(),
      new Date("1/4/2025").getTime(),
      new Date("1/5/2025").getTime(),
      new Date("1/6/2025").getTime(),
      new Date("1/7/2025").getTime(),
      new Date("1/8/2025").getTime(),
      new Date("1/9/2025").getTime(),
      new Date("1/10/2025").getTime(),
      new Date("1/11/2025").getTime(),
      new Date("1/12/2025").getTime(),
      new Date("1/13/2025").getTime(),
      new Date("1/14/2025").getTime(),
      new Date("1/15/2025").getTime(),
    ],
    max: new Date("1/15/2025").getTime(),
  }

  const syncingLineTotalOrders = [
    112, 108, 137, 172, 184, 190, 198, 192, 145, 130, 121, 145, 134, 128, 80,
  ]

  const syncingLineAverageOrderValue = [
    101.13, 112.24, 156.29, 167.57, 99.01, 96.48, 91.5, 98.74, 101.28, 150.04, 160.25, 172.14,
    143.24, 140.72, 99.85,
  ]

  const orderOptions = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "line",
      height: 120,
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
      id: "order-placed",
      group: "order",
    },
    theme: {
      mode: getTheme(),
    },
    xaxis: syncingLineXAxisOption,
    stroke: {
      width: 2,
    },
    series: [
      {
        color: "#3e5eff",
        name: "Orders",
        data: syncingLineTotalOrders,
      },
    ],
  }

  chartOrderSyncingLine = new ApexCharts(
    document.querySelector("#chart_order_syncing_line"),
    orderOptions
  )

  chartOrderSyncingLine.render()

  const orderRevenueOptions = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "line",
      height: 120,
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
      id: "order-revenue",
      group: "order",
    },
    theme: {
      mode: getTheme(),
    },
    xaxis: syncingLineXAxisOption,
    yaxis: {
      labels: {
        formatter: (val) => (val / 1000).toFixed(0) + "K",
      },
    },
    tooltip: {
      y: {
        formatter: (val) => "$" + (val / 1000).toFixed(2) + "K",
      },
    },
    stroke: {
      width: 2,
    },
    series: [
      {
        color: "#FFC700",
        name: "Revenue",
        data: syncingLineTotalOrders.map((cur, index) =>
          Number((cur * syncingLineAverageOrderValue[index]).toFixed(2))
        ),
      },
    ],
  }

  chartOrderRevenueSyncingLine = new ApexCharts(
    document.querySelector("#chart_order_revenue_syncing_line"),
    orderRevenueOptions
  )

  chartOrderRevenueSyncingLine.render()

  const orderAverageOptions = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "line",
      height: 120,
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
      id: "order-average",
      group: "order",
    },
    theme: {
      mode: getTheme(),
    },
    xaxis: syncingLineXAxisOption,
    yaxis: {
      labels: {
        formatter: (val) => val.toFixed(0),
      },
    },
    tooltip: {
      y: {
        formatter: (val) => "$" + val,
      },
    },
    stroke: {
      width: 2,
    },
    series: [
      {
        color: "#FFAD84",
        name: "Average",
        data: syncingLineAverageOrderValue,
      },
    ],
  }

  chartOrderAverageSyncingLine = new ApexCharts(
    document.querySelector("#chart_order_average_syncing_line"),
    orderAverageOptions
  )

  chartOrderAverageSyncingLine.render()
}

const initChartAnnotationLine = () => {
  if (!window.ApexCharts) return

  const generateAnnotationData = () => {
    let currentMonth = new Date().getMonth()
    let currentYear = new Date().getFullYear()
    const pastMonthWithQuarter = []
    const totalLabelCount = 8
    while (pastMonthWithQuarter.length < totalLabelCount) {
      if (pastMonthWithQuarter.length === 0 && new Date().getDate() > totalLabelCount) {
        pastMonthWithQuarter.push(monthNames[currentMonth] + " 1-10")
        if (pastMonthWithQuarter.length === 0 && new Date().getDate() > 20) {
          pastMonthWithQuarter.push(monthNames[currentMonth] + " 11-20")
        }
      } else if (currentMonth !== new Date().getMonth()) {
        pastMonthWithQuarter.push(
          monthNames[currentMonth] + ` 21-${new Date(currentYear, currentMonth + 1, 0).getDate()}`
        )
        if (pastMonthWithQuarter.length !== totalLabelCount) {
          pastMonthWithQuarter.push(monthNames[currentMonth] + " 11-20")
        }
        if (pastMonthWithQuarter.length !== totalLabelCount) {
          pastMonthWithQuarter.push(monthNames[currentMonth] + " 1-10")
        }
      }
      currentMonth -= 1
      if (currentMonth === -1) {
        currentMonth = 11
        currentYear -= 1
      }
    }
    return pastMonthWithQuarter.reverse()
  }
  const annotationXAxisLabels = generateAnnotationData()

  const options = {
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      type: "line",
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
    theme: {
      mode: getTheme(),
    },
    xaxis: {
      categories: annotationXAxisLabels,
      title: {
        text: "Sales",
        style: { fontWeight: "500" },
      },
    },
    yaxis: {
      labels: {
        formatter: (val) => val.toFixed(0) + "K",
      },
    },
    tooltip: {
      y: {
        formatter: (val) => "$" + val + "K",
      },
    },
    annotations: {
      yaxis: [
        {
          y: 202,
          strokeDashArray: 0,
          borderColor: "#FDA403",
          label: {
            style: {
              color: "#fff",
              background: "#FDA403",
            },
            text: "Target",
            borderWidth: 0,
          },
        },
      ],
      xaxis: [
        {
          x: annotationXAxisLabels[2],
          strokeDashArray: 0,
          borderColor: "#A25772",
          label: {
            style: {
              color: "#fff",
              background: "#A25772",
            },
            text: "Start Of Sale",
            borderWidth: 0,
          },
        },
        {
          x: annotationXAxisLabels[4],
          x2: annotationXAxisLabels[5],
          strokeDashArray: 0,
          borderColor: "#8E7AB5",
          label: {
            style: {
              color: "#fff",
              background: "#8E7AB5",
            },
            text: "Festive Season",
            borderWidth: 0,
          },
        },
      ],
      points: [
        {
          x: annotationXAxisLabels[6],
          y: 196.78,
          marker: {
            size: 6,
            fillColor: "#FF4560",
            strokeColor: "FF4560",
            radius: 3,
          },
          label: {
            borderColor: "#FF4560",
            offsetY: 36,
            style: {
              color: "#fff",
              background: "#FF4560",
            },
            borderWidth: 0,
            text: "Production Down",
          },
        },
      ],
    },
    stroke: {
      curve: "smooth",
      width: 2,
    },
    colors: ["#3e5eff"],
    series: [
      {
        name: "Sales",
        data: [114.87, 105.88, 90.58, 135.43, 86.39, 212.99, 196.78, 143.76],
      },
    ],
  }

  chartAnnotationLine = new ApexCharts(document.querySelector("#chart_annotation_line"), options)

  chartAnnotationLine.render()
}

const initCharts = () => {
  initChartLabelLine()
  initChartStepLine()
  initChartSyncingLine()
  initChartAnnotationLine()
}

document.addEventListener("custom.layout-changed", () => {
  chartLabelLine?.updateOptions({
    theme: {
      mode: getTheme(),
    },
    dataLabels: {
      background: {
        borderColor: getTheme() === "light" ? "#fff" : "#000",
      },
    },
  })
  chartStepLine?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  chartOrderSyncingLine?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  chartOrderRevenueSyncingLine?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  chartOrderAverageSyncingLine?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  chartAnnotationLine?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
})

document.addEventListener("DOMContentLoaded", function () {
  initCharts()
})
