# Chapter 2: Installation and Setup

Before you can start building simulations, you need to install the `chs-sdk` and its dependencies. This chapter will guide you through the process.

## Prerequisites

*   **Python 3.8 or higher**: The SDK is built on Python. If you don't have Python installed, you can download it from [python.org](https://www.python.org/downloads/).
*   **pip**: The Python package installer. It usually comes with Python. You can check if it's installed by running `pip --version`.

## Installation

We recommend installing the `chs-sdk` in a virtual environment to avoid conflicts with other Python projects.

### 1. Create a Virtual Environment

Open your terminal or command prompt and navigate to your projects directory. Then, run the following commands:

```bash
# Create a new directory for your project
mkdir my-chs-project
cd my-chs-project

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS and Linux:
source venv/bin/activate
```

You will know the virtual environment is active when you see `(venv)` at the beginning of your command prompt.

### 2. Install the SDK from Source

Since you are working with the source code directly, you can install the SDK and its dependencies using `pip`'s "editable" mode. This is useful for development as any changes you make to the source code will be immediately available without needing to reinstall.

Navigate to the `water_system_sdk` directory (the one containing the `pyproject.toml` file) and run:

```bash
pip install -e .
```

This command will read the `pyproject.toml` file, find all the dependencies (like `numpy`, `pandas`, `scipy`, etc.), and install them into your virtual environment, along with the `chs_sdk` itself.

## Verifying the Installation

To make sure everything is installed correctly, you can try to import the SDK in a Python interpreter.

```bash
python
```

Then, in the Python prompt, type:

```python
import chs_sdk
print("CHS-SDK installed successfully!")
```

If you don't see any errors, you are all set!

## Next Steps

Now that you have the SDK installed, you are ready to build your first simulation. In the next chapter, we will walk through the process of creating a simple model of a reservoir.
