# chs-scada-dispatch - 云端指挥中心

*   **角色**: 业务运行的“云端大脑”。负责接收所有边缘节点的数据，进行集中式的分析决策，并将指令下发给边缘节点执行。

## 详细目录结构与代码解析

```
chs-scada-dispatch/
├── .env
├── .env.example
├── README.md
├── app.py
├── requirements.txt
├── test_publisher.py
├── alarm_engine/
├── api/
├── audit_log/
├── data_ingestion/
├── data_processing/
├── dispatch_engine/
└── tests/
```

### 代码现状分析

*   这是一个功能丰富的、模块化的后端服务应用。
*   **app.py**: Web 应用主入口。使用 Flask 或 FastAPI 框架，负责初始化和启动整个后端服务。
*   **api/**: API 接口层。包含所有对外暴露的 REST API 端点定义。
*   **data_ingestion/**: 数据接收模块。负责处理最原始的数据流入。
*   **data_processing/**: 数据处理与分析模块。进行数据清洗、转换、计算等操作。
*   **dispatch_engine/**: 核心调度引擎。负责执行核心的决策逻辑，加载 .agent 模型进行推理计算。
*   **alarm_engine/**: 报警引擎。持续监控系统状态数据，根据预设规则判断是否触发报警。
*   **audit_log/**: 审计日志模块。负责记录系统中的关键操作和事件。
*   **test_publisher.py**: 测试工具。用于模拟 chs-edge 节点发布测试数据。
*   **tests/**: 单元测试与集成测试。
*   **.env / .env.example**: 环境变量配置。
