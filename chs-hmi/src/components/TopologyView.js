import React, { useState, useEffect, useRef } from 'react';
import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { getSystemTopology } from '../services/apiService';

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend);

// Custom plugin to draw lines between points
const edgeDrawerPlugin = {
  id: 'edgeDrawer',
  afterDraw: (chart, args, options) => {
    const { ctx } = chart;
    const { edges, nodeMap } = options;

    if (!edges || !nodeMap) return;

    ctx.save();
    ctx.strokeStyle = '#aaa';
    ctx.lineWidth = 2;

    edges.forEach(edge => {
      const fromNode = nodeMap[edge.from];
      const toNode = nodeMap[edge.to];

      if (fromNode && toNode) {
        const fromPoint = chart.getDatasetMeta(0).data[fromNode.index];
        const toPoint = chart.getDatasetMeta(0).data[toNode.index];

        if(fromPoint && toPoint) {
            ctx.beginPath();
            ctx.moveTo(fromPoint.x, fromPoint.y);
            ctx.lineTo(toPoint.x, toPoint.y);
            ctx.stroke();
        }
      }
    });
    ctx.restore();
  }
};

const TopologyView = () => {
  const [topology, setTopology] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const data = await getSystemTopology();
        setTopology(data);
      } catch (err) {
        setError('Failed to load system topology.');
        console.error(err);
      }
    };
    fetchTopology();
  }, []);

  if (error) {
    return <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>;
  }

  if (topology.nodes.length === 0) {
    return <p style={{ textAlign: 'center' }}>Loading topology...</p>;
  }

  const nodeMap = topology.nodes.reduce((acc, node, index) => {
    acc[node.id] = { ...node, index };
    return acc;
  }, {});

  const data = {
    datasets: [
      {
        label: 'System Components',
        data: topology.nodes.map(node => ({
          x: node.position.x,
          y: node.position.y,
          label: node.label,
          type: node.type,
          status: node.status,
        })),
        pointBackgroundColor: (context) => {
          const { raw } = context;
          if (raw.type === 'PumpStation') {
            return raw.status.pump_status === 1 ? 'green' : 'red';
          }
          if (raw.type === 'Reservoir') {
            return '#007bff';
          }
          return '#6c757d';
        },
        pointRadius: 15,
        pointHoverRadius: 20,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        display: false,
        min: 0,
        max: 800,
      },
      y: {
        display: false,
        min: 0,
        max: 400,
      }
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const { raw } = context;
            let label = raw.label || '';
            if (label) {
              label += ` (${raw.type})`;
            }
            if (raw.status) {
                Object.entries(raw.status).forEach(([key, value]) => {
                    label += `\n${key}: ${value}`;
                });
            }
            return label.split('\n');
          }
        }
      },
      edgeDrawer: {
        edges: topology.edges,
        nodeMap: nodeMap
      }
    }
  };

  return (
    <div style={{ padding: '20px', height: '600px' }}>
      <h2 style={{ textAlign: 'center' }}>系统拓扑视图</h2>
      <Scatter data={data} options={options} plugins={[edgeDrawerPlugin]} />
    </div>
  );
};

export default TopologyView;
