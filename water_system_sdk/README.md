# CHS-SDK - 代码及功能说明

## 产品说明：核心版与智能体版的关系

CHS-SDK 的架构设计体现了清晰的层次关系，可以理解为包含一个 “核心版 (Core Version)” 和一个在其之上构建的 “智能体版 (Agent Version)”。

### 核心版 (Core Version)

*   **核心目录**: `modules/`
*   **定位**: 科学计算内核与数字孪生基础。`modules` 目录是整个 SDK 的技术基石，它提供了一套专业、完整的水文水动力学仿真模型。这一版本专注于精确地模拟物理世界，回答“如果……会发生什么？”的问题。

### 智能体版 (Agent Version)

*   **核心目录**: `agents/`, `factory/`, `workflows/`, `interfaces/` 等，它们围绕并消费 `modules/` 的能力。
*   **定位**: 智能决策与自动化控制解决方案。智能体版在核心版提供的数字孪生环境之上，构建了一整套用于研发、训练、评估和部署“智能大脑”（Agent）的工具链。它专注于解决“接下来该怎么做？”的问题。

## 完整目录结构与文件功能详解

```
chs_sdk/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── pid.py
│   ├── mpc.py
│   └── rl/
│       ├── __init__.py
│       ├── ppo_agent.py
│       └── sac_agent.py
├── components/
│   ├── __init__.py
│   ├── logger.py
│   └── config_loader.py
├── core/
│   ├── __init__.py
│   ├── simulator.py
│   ├── state_manager.py
│   └── event_bus.py
├── factory/
│   ├── __init__.py
│   ├── trainer.py
│   ├── evaluator.py
│   └── model_registry.py
├── interfaces/
│   ├── __init__.py
│   ├── env_interface.py
│   └── module_interface.py
├── modules/
│   ├── __init__.py
│   ├── hydrology/
│   │   ├── xinanjiang.py
│   │   └── swat.py
│   ├── hydrodynamics/
│   │   ├── saint_venant_solver.py
│   │   └── network_builder.py
│   ├── hydrodynamics_2d/
│   │   ├── shallow_water_solver.py
│   │   └── wet_dry_handler.py
│   ├── hydro_distributed/
│   │   └── grid_model.py
│   ├── meshing/
│   │   ├── tri_generator.py
│   │   └── grid_generator.py
│   ├── modeling/
│   │   ├── coupler.py
│   │   └── model_builder.py
│   ├── identification/
│   │   ├── objective_functions.py
│   │   └── optimizers.py
│   ├── data_processing/
│   ├── basic_tools/
│   ├── control/
│   └── disturbances/
├── preprocessing/
│   ├── __init__.py
│   ├── timeseries.py
│   └── feature_engineering.py
├── tools/
│   ├── __init__.py
│   └── epanet_adapter.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── workflows/
    ├── __init__.py
    ├── training_workflow.py
    └── simulation_workflow.py
```

*   **agents/**: 系统的大脑。定义了所有用于控制系统的决策逻辑。
*   **components/**: 提供了可在项目中多处复用的、具有特定功能的高级组件。
*   **core/**: SDK 的心脏，负责驱动整个仿真流程。
*   **factory/**: 智能体的“兵工厂”，负责 Agent 的训练、评估和打包。
*   **interfaces/**: 模块间的“法律合同”，定义了各模块交互的标准。
*   **modules/**: 数字孪生的科学计算核心，一个专业级的科学计算引擎。
*   **preprocessing/**: 数据的“清洗工”，负责处理输入到 SDK 的原始数据。
*   **tools/**: 与行业标准软件进行交互的适配器。
*   **utils/**: 提供了被广泛使用的通用、低级别的辅助函数。
*   **workflows/**: 任务的“总导演”，将 SDK 的各种能力串联成端到端的任务流。
