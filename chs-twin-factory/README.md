# chs-twin-factory - AI Agent 研发中心

*   **角色**: 智能体的“兵工厂”。这是一个服务化的 AI Agent 研发平台，负责消费 CHS-SDK 的能力，提供从环境封装、算法训练、实验管理到模型打包的完整 MLOps 工具链。

## 详细目录结构与代码解析

```
chs-twin-factory/
├── README.md
└── backend/
    ├── migrations/
    │   ├── README
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    ├── app.py
    ├── debug_agent.py
    ├── gym_wrapper.py
    ├── requirements.txt
    ├── rule_based_agent.py
    └── test_app.py
```

### 代码现状分析

*   **app.py**: Web 应用的核心入口。
*   **gym_wrapper.py**: 关键的适配器，将 CHS-SDK 封装成标准的 Gymnasium 环境接口。
*   **rule_based_agent.py**: 基准控制器。
*   **debug_agent.py**: 调试工具。
*   **migrations/**: 数据库版本管理 (Alembic)。
*   **test_app.py**: 应用测试代码。
*   **requirements.txt**: 依赖项列表。
