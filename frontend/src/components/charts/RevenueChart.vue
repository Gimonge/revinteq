<template>
  <div>
    <VueApexCharts
      type="bar"
      :height="height"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const props = defineProps({
  labels:   { type: Array, default: () => [] },
  values:   { type: Array, default: () => [] },
  currency: { type: String, default: 'KES' },
  color:    { type: String, default: '#1F7A4C' },
  height:   { type: Number, default: 220 },
})

const series = computed(() => [{
  name: 'Revenue',
  data: props.values,
}])

const chartOptions = computed(() => ({
  chart: {
    toolbar:    { show: false },
    animations: { enabled: true, speed: 600 },
    fontFamily: 'Nunito, sans-serif',
  },
  plotOptions: {
    bar: {
      borderRadius: 4,
      columnWidth:  '60%',
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: props.labels,
    labels: {
      style: { fontSize: '11px', colors: '#94A3B8' }
    },
    axisBorder: { show: false },
    axisTicks:  { show: false },
  },
  yaxis: {
    labels: {
      style: { fontSize: '11px', colors: '#94A3B8' },
      formatter: (v) => v >= 1000
        ? `${props.currency} ${(v / 1000).toFixed(0)}K`
        : `${props.currency} ${v}`,
    }
  },
  colors: [props.color],
  fill:   { opacity: 0.9 },
  grid: {
    borderColor:    '#E2E8F0',
    strokeDashArray: 4,
    yaxis: { lines: { show: true } },
    xaxis: { lines: { show: false } },
  },
  tooltip: {
    y: {
      formatter: (v) => `${props.currency} ${Number(v).toLocaleString('en-KE')}`
    }
  }
}))
</script>
