import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register the necessary components for Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

/**
 * A component to display historical data in a line chart.
 * @param {object} props - The component's props.
 * @param {object} props.chartData - The data for the chart.
 * @param {Array<string>} props.chartData.timestamps - The labels for the X-axis.
 * @param {Array<number>} props.chartData.values - The data points for the Y-axis.
 * @param {string} props.title - The title of the chart.
 */
const HistoricalChart = ({ chartData, title }) => {
  const data = {
    labels: chartData.timestamps.map(t => new Date(t).toLocaleTimeString()),
    datasets: [
      {
        label: title || '历史数据',
        data: chartData.values,
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: title || '历史数据趋势',
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: '时间',
        },
      },
      y: {
        title: {
          display: true,
          text: '数值',
        },
      },
    },
  };

  return <Line data={data} options={options} />;
};

export default HistoricalChart;
