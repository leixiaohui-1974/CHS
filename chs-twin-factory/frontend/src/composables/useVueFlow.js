import { ref, reactive } from 'vue';

// --- Shared State ---
export const elements = ref([]);
export const selectedNode = ref(null);

export const availableNodes = reactive([
  { group: '数据源', type: 'Constant', label: '常量', description: '输出一个恒定的值' },
  { group: '数据源', type: 'SignalGenerator', label: '信号发生器', description: '生成正弦/方波等信号' },
  { group: '数据源', type: 'DataLoader', label: '数据加载器', description: '从外部加载历史数据' },
  
  { group: '物理模型', type: 'Reservoir', label: '水库', description: '一阶惯性环节模拟' },
  { group: '物理模型', type: 'Pipe', label: '管道', description: '模拟延迟和损耗' },
  
  { group: '运算与逻辑', type: 'Sum', label: '加/减法器', description: '将多个输入进行运算' },
  
  { group: '控制与调度', type: 'PIDController', label: 'PID 控制器', description: '经典的闭环反馈控制器' },
  { group: '控制与调度', type: 'Dispatcher', label: '调度器', description: '根据规则或优化进行调度' },
  { group: '控制与调度', type: 'AIAgent', label: 'AI 智能体', description: '加载训练好的模型进行控制' },

  { group: '分析与测试', type: 'Scope', label: '示波器', description: '可视化一个或多个信号' },
  { group: '分析与测试', type: 'Predictor', label: '预测器', description: '预测未来需水量等' },
  { group: '分析与测试', type: 'Identifier', label: '辨识器', description: '在线或离线参数辨识' },
]);

// --- Helper Functions ---
export const getNodeDefaultParams = (type) => {
  switch (type) {
    case 'Constant': return { value: 1 };
    case 'SignalGenerator': return { amplitude: 1, frequency: 0.5 };
    case 'Reservoir': return { capacity: 1000, initial: 500, k: 0.1 };
    case 'PIDController': return { Kp: 1, Ki: 0.1, Kd: 0.05, setpoint: 0 };
    case 'Dispatcher': return { threshold_high: 800, threshold_low: 200 };
    case 'Predictor': return { horizon: 24 };
    case 'AIAgent': return { model_id: 'agent-001' };
    default: return {};
  }
};

export const getNodeHandles = (type) => {
    switch (type) {
        case 'Constant':
        case 'SignalGenerator':
        case 'DataLoader':
            return { sourcePosition: 'right' };
        case 'Scope':
            return { targetPosition: 'left' };
        default:
            return { targetPosition: 'left', sourcePosition: 'right' };
    }
};

// --- Main Composable ---
export default function useVueFlowManager() {
  const onNodeSelected = (node) => {
    selectedNode.value = node;
    elements.value.forEach(el => {
      if (el.id === node?.id) el.selected = true;
      else el.selected = false;
    });
  };

  const onConnect = (params) => {
    const newEdge = { ...params, type: 'smoothstep' };
    elements.value.push(newEdge);
  };

  const onEdgesChange = (changes) => {
    changes.forEach(change => {
      if (change.type === 'remove') {
        const index = elements.value.findIndex(el => el.id === change.id);
        if (index !== -1) {
          elements.value.splice(index, 1);
        }
      }
    });
  };

  const updateElements = (newElements) => {
    elements.value = newElements;
  };

  return {
    elements,
    selectedNode,
    onNodeSelected,
    updateElements,
    onConnect,
    onEdgesChange,
  };
}