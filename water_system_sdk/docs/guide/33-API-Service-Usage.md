# 教程 33: 使用 API 服务进行仿真

本教程将指导您如何使用 `CHS-SDK` 内置的 Web API 服务来运行仿真。这对于将仿真能力集成到其他应用程序或工作流中非常有用。

## 1. 先决条件

确保您已经按照 `README.md` 中的说明，安装了带有 `service` 选项的 SDK。
```bash
# 在 water_system_sdk 目录下
pip install .[service]
```

## 2. 启动 API 服务

在 `water_system_sdk` 目录下，使用 `uvicorn` 启动服务：

```bash
uvicorn chs_sdk.service.main:app --host 0.0.0.0 --port 8000
```
如果一切正常，您应该会看到类似以下的输出，表明服务正在运行：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

现在，您可以在浏览器中打开 `http://127.0.0.1:8000/docs`，您会看到 FastAPI 提供的交互式 API 文档页面。

## 3. 准备仿真配置文件

API 的 `/run_simulation/` 端点接受一个 JSON 对象作为输入，该对象的结构与 `SimulationManager` 所需的配置字典完全相同。

我们已经为您准备好了一个示例配置文件，位于 `source/api_config.json`。该文件描述了一个简单的水库水位 PID 控制仿真。

## 4. 调用 API 运行仿真

您可以使用任何支持 HTTP 请求的工具来调用 API。这里我们以 `curl` 为例。

打开一个新的终端（不要关闭正在运行 `uvicorn` 的终端），并执行以下命令。请确保您位于 `water_system_sdk/docs/guide/` 目录下，以便正确引用 `source/api_config.json` 文件。

```bash
curl -X POST "http://127.0.0.1:8000/run_simulation/" \
-H "Content-Type: application/json" \
-d @source/api_config.json
```

*   `-X POST`: 指定请求方法为 POST。
*   `-H "Content-Type: application/json"`: 告诉服务器我们发送的是 JSON 数据。
*   `-d @source/api_config.json`: 读取 `source/api_config.json` 文件的内容，并将其作为请求体发送。

## 5. 分析返回结果

如果请求成功，API 会返回一个 JSON 对象，其中包含 `status: "success"` 和一个 `data` 字段。`data` 字段是一个数组，包含了仿真过程中每个时间步记录的日志数据。

返回结果类似如下（为简洁起见，此处仅展示部分数据）：
```json
{
  "status": "success",
  "data": [
    {
      "time": 0.0,
      "main_reservoir.state.level": 5.0,
      "level_controller.state.output": 0.0,
      "level_controller.set_point": 10.0
    },
    {
      "time": 1.0,
      "main_reservoir.state.level": 5.0,
      "level_controller.state.output": 0.1,
      "level_controller.set_point": 10.0
    },
    // ... more data points
  ]
}
```

您可以将这些数据保存下来，用于后续的分析或可视化。

## 总结

通过本教程，您学会了如何：
- 启动 `CHS-SDK` 的 API 服务。
- 使用 `curl` 等工具通过 HTTP 请求调用仿真服务。
- 理解 API 的输入（JSON 配置）和输出（仿真结果）。

这种服务化的方式极大地增强了 SDK 的灵活性和集成能力。
