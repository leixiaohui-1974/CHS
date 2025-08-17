# 第二章：安装与设置

在开始构建仿真之前，您需要安装 `chs-sdk` 及其依赖项。本章将指导您完成整个安装过程。

## 系统要求

*   **Python 3.8 或更高版本**: SDK 基于 Python 构建。如果您尚未安装 Python，可以从 [python.org](https://www.python.org/downloads/) 下载。
*   **pip**: Python 包安装器。通常随 Python 一同安装。您可以通过运行 `pip --version` 来检查是否已安装。

## 安装步骤

我们强烈建议在虚拟环境中安装 `chs-sdk`，以避免与其他 Python 项目产生冲突。

### 1. 创建虚拟环境

打开您的终端或命令提示符，导航到您的项目目录。然后，运行以下命令：

```bash
# 为您的项目创建一个新目录
mkdir my-chs-project
cd my-chs-project

# 创建一个虚拟环境
python -m venv venv

# 激活虚拟环境
# 在 Windows 上:
venv\Scripts\activate
# 在 macOS 和 Linux 上:
source venv/bin/activate
```

当您看到命令提示符的开头出现 `(venv)` 时，表示虚拟环境已成功激活。

### 2. 从源代码安装 SDK

由于您直接使用源代码，可以使用 `pip` 的“可编辑”模式来安装 SDK 及其依赖项。这种方式对于开发非常有用，因为您对源代码所做的任何更改都会立即生效，无需重新安装。

导航到 `water_system_sdk` 目录（即包含 `pyproject.toml` 文件的目录），然后运行：

```bash
pip install -e .
```

此命令将读取 `pyproject.toml` 文件，找到所有依赖项（如 `numpy`, `pandas`, `scipy` 等），并将它们与 `chs_sdk` 一同安装到您的虚拟环境中。

## 验证安装

为了确保一切安装正确，您可以在 Python 解释器中尝试导入 SDK。

```bash
python
```

然后，在 Python 提示符中输入：

```python
import chs_sdk
print("CHS-SDK 安装成功！")
```

如果您没有看到任何错误信息，那么一切就绪！

## 下一步

现在您已经成功安装了 SDK，可以开始构建您的第一个仿真了。在下一章中，我们将逐步介绍如何创建一个简单的水库模型。
