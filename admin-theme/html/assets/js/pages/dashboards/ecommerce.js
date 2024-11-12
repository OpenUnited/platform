let revenueStatisticsChart = null
let customerAcquisitionChart = null
let topCountriesChart = null

const getTheme = () => window.themeConfig.theme

const initRevenueStatisticsChart = () => {
  if (!window.ApexCharts) return
  const orders = [10, 12, 14, 16, 18, 20, 14, 16, 18, 12]
  const revenues = [15, 24, 21, 28, 30, 40, 22, 32, 34, 20]
  const dates = [
    new Date("1/1/2016"),
    new Date("1/1/2017"),
    new Date("1/1/2018"),
    new Date("1/1/2019"),
    new Date("1/1/2020"),
    new Date("1/1/2021"),
    new Date("1/1/2022"),
    new Date("1/1/2023"),
    new Date("1/1/2024"),
    new Date("1/1/2025"),
  ]

  var options = {
    theme: {
      mode: getTheme(),
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      height: 280,
      type: "bar",
      stacked: true,
      background: "transparent",
      toolbar: {
        show: false,
      },
    },
    plotOptions: {
      bar: {
        borderRadius: 8,
        borderRadiusApplication: "end",
        borderRadiusWhenStacked: "last",
        colors: {
          backgroundBarColors: ["rgba(127,127,127,0.06)"],
          backgroundBarRadius: 4,
        },
        columnWidth: "50%",
        barHeight: "100%",
      },
    },
    dataLabels: {
      enabled: false,
    },
    colors: ["#3e60d5", "#3ed5b9"],
    legend: {
      show: true,
      horizontalAlign: "center",
      offsetX: 0,
      offsetY: 6,
    },
    series: [
      {
        name: "Orders",
        data: orders,
      },
      {
        name: "Revenue",
        data: revenues,
      },
    ],
    xaxis: {
      categories: dates,
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false,
      },
      labels: {
        formatter: (val) => {
          return val.toLocaleDateString("en-US", { year: "numeric" })
        },
      },
    },
    yaxis: {
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false,
      },
      labels: {
        show: false,
        formatter: function (val, e) {
          if (e) {
            if (e.seriesIndex === 0) {
              return val.toString()
            }
            return "$" + val + "K"
          }
          return val.toString()
        },
      },
    },
    tooltip: {
      enabled: true,
      shared: true,
      intersect: false,
    },
    grid: {
      show: false,
    },
  }

  revenueStatisticsChart = new ApexCharts(
    document.querySelector("#revenue_statistics_chart"),
    options
  )

  revenueStatisticsChart.render()
}

const initCustomerAcquisitionChart = () => {
  if (!window.ApexCharts) return
  var options = {
    theme: {
      mode: getTheme(),
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      height: 210,
      fontFamily: "DM Sans",
      type: "area",
      background: "transparent",
      sparkline: {
        enabled: true,
      },
      toolbar: {
        show: false,
      },
    },
    dataLabels: {
      enabled: false,
    },
    grid: {
      show: false,
    },

    stroke: {
      curve: ["smooth", "straight"],
      width: 2,
      dashArray: [0, 6],
    },
    series: [
      {
        name: "Sessions",
        type: "area",
        data: [10, 14, 16, 14, 12, 15, 18, 21, 24, 23, 21, 17, 19, 22],
      },
    ],
    legend: {
      show: false,
    },
    xaxis: {
      categories: [],
      tooltip: {
        enabled: false,
      },
      axisBorder: {
        show: false,
      },
      labels: {
        show: false,
        formatter: (val) => {
          return `Day ${val}`
        },
      },
      axisTicks: {
        show: false,
      },
    },
    yaxis: {
      labels: {
        show: false,
      },
    },

    fill: {
      type: "gradient",
      opacity: 1,
      gradient: {
        shadeIntensity: 1,

        type: "horizontal",
        colorStops: [
          {
            offset: 0,
            color: "rgba(75,134,255,0.1)",
            opacity: 1,
          },
          {
            offset: 30,
            color: "rgba(255,54,54,0.1)",
            opacity: 1,
          },
          {
            offset: 35,
            color: "rgba(255,54,138,0.08)",
            opacity: 1,
          },
          {
            offset: 50,
            color: "rgba(51,84,250,0.2)",
            opacity: 1,
          },
          {
            offset: 80,
            color: "rgba(64,96,255,0.16)",
            opacity: 1,
          },
          {
            offset: 100,
            color: "rgba(75,99,255,0.1)",
            opacity: 1,
          },
        ],
      },
    },
  }

  customerAcquisitionChart = new ApexCharts(
    document.querySelector("#customer_acquisition_chart"),
    options
  )

  customerAcquisitionChart.render()
}

const initTopCountriesChart = () => {
  if (!window.ApexCharts) return
  const topCountries = [
    {
      name: "Turkey",
      orders: 10,
    },
    {
      name: "Canada",
      orders: 15,
    },
    {
      name: "India",
      orders: 14,
    },
    {
      name: "Netherlands",
      orders: 18,
    },
    {
      name: "Italy",
      orders: 25,
    },
    {
      name: "France",
      orders: 16,
    },
  ]

  var options = {
    theme: {
      mode: getTheme(),
    },
    chart: {
      events: {
        mounted: (c) => c.windowResizeHandler(),
      },
      height: 290,
      fontFamily: "DM Sans",
      type: "bar",
      parentHeightOffset: 0,
      background: "transparent",
      toolbar: {
        show: false,
      },
    },
    plotOptions: {
      bar: {
        horizontal: true,
        borderRadius: 4,
        distributed: true,
        borderRadiusApplication: "end",
      },
    },
    dataLabels: {
      enabled: true,
      textAnchor: "start",
      style: {
        colors: ["#fff"],
      },
      formatter: function (val, opt) {
        return opt.w.globals.labels[opt.dataPointIndex] + ":  " + val
      },
      offsetX: -10,
      dropShadow: {
        enabled: false,
      },
    },
    series: [
      {
        data: topCountries.map((country) => country.orders),
      },
    ],
    legend: {
      show: false,
    },
    stroke: {
      width: 0,
      colors: ["#fff"],
    },
    xaxis: {
      categories: topCountries.map((country) => country.name),
    },
    yaxis: {
      labels: {
        show: false,
      },
    },
    grid: {
      borderColor: "transparent",
      padding: {
        top: -16,
      },
    },

    tooltip: {
      theme: "dark",
      x: {
        show: false,
      },
      y: {
        formatter: (val, opts) => `${val}%`,
        title: {
          formatter: () => "",
        },
      },
    },
    colors: [
      "#3e60d5",
      "#47ad77",
      "#fa5c7c",
      "#6c757d",
      "#39afd1",
      "#2b908f",
      "#ffbc00",
      "#90ee7e",
      "#f48024",
      "#212730",
    ],
  }

  topCountriesChart = new ApexCharts(document.querySelector("#top_countries_chart"), options)

  topCountriesChart.render()
}

document.addEventListener("custom.layout-changed", () => {
  revenueStatisticsChart?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  customerAcquisitionChart?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
  topCountriesChart?.updateOptions({
    theme: {
      mode: getTheme(),
    },
  })
})

document.addEventListener("DOMContentLoaded", function () {
  initRevenueStatisticsChart()
  initCustomerAcquisitionChart()
  initTopCountriesChart()
})
