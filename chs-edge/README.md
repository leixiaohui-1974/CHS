# chs-edge - 边缘计算节点

*   **角色**: 连接数字与物理世界的“神经末梢”。部署在现场，负责实时数据采集、本地指令执行，并将数据上传至云端。

## 详细目录结构与代码解析

```
chs-edge/
├── README.md
├── config.env
├── create_sample_agent.py
├── main.py
├── model.agent
├── requirements.txt
├── chs_sdk/
├── drivers/
├── engine/
└── services/
```

### 代码现状分析

*   这是一个功能完备的、模块化的边缘计算应用。
*   **main.py**: 应用主入口。
*   **engine/**: 核心业务逻辑引擎。
*   **drivers/**: 硬件驱动与连接器。
*   **services/**: 应用服务模块。
*   **chs_sdk/**: 本地化的 SDK。
*   **model.agent**: 示例 Agent 模型。
*   **create_sample_agent.py**: 辅助工具脚本。
*   **config.env**: 配置文件。
*   **requirements.txt**: 依赖项列表。
