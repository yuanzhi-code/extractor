# 使用 uv 创建可复现的 Python 虚拟环境

`uv` 是一个现代、高效的 Python 包管理工具，以其快速和可靠的特性广受好评。它非常适合创建和管理可复现的开发环境。本文将详细介绍如何使用 `uv` 创建虚拟环境，并确保团队成员在拉取仓库后能够快速复现相同的开发环境。

## 核心理念：可复现性

可复现性（Reproducibility）是软件开发中的关键原则，旨在确保无论何时何地，任何人都能获得与你完全相同的开发环境。通过以下方式实现：

- **虚拟环境隔离**：将项目依赖与系统全局 Python 环境隔离。
- **精确依赖锁定**：记录所有直接和间接依赖的精确版本。
- **版本控制**：将依赖配置文件纳入版本控制，方便团队共享。

## 步骤 1：安装 uv

首先，确保系统中已安装 `uv`。推荐使用 `pipx` 安装 `uv`，因为 `pipx` 会将其安装到隔离环境中，避免与其他 Python 包冲突。

```bash
# 安装 pipx（如果尚未安装）
pip install pipx
pipx ensurepath

# 安装 uv
pipx install uv
```

或者，可以直接使用 `pip` 或其他包管理器安装：

```bash
# 使用 pip 安装
pip install uv

# 使用 Conda/Mamba 安装（如果适用）
conda install -c conda-forge uv
```

安装完成后，运行以下命令验证是否成功：

```bash
uv --version
```

## 步骤 2：创建虚拟环境

进入项目根目录，使用 `uv venv` 命令创建虚拟环境。默认情况下，`uv` 会在当前目录下创建名为 `.venv` 的文件夹。

```bash
# 进入项目目录
cd my_awesome_project

# 创建虚拟环境
uv venv
```

这会在项目目录下生成一个 `.venv` 文件夹，用于存储虚拟环境。

## 步骤 3：激活虚拟环境

在安装项目依赖之前，需要激活虚拟环境。激活后，通过 `uv pip install` 安装的包将仅存在于虚拟环境中，不会影响全局 Python 环境。

根据操作系统，激活命令如下：

- **Linux / macOS**：

```bash
source .venv/bin/activate
```

- **Windows (命令提示符 CMD)**：

```bash
.venv\Scripts\activate.bat
```

- **Windows (PowerShell)**：

```bash
.venv\Scripts\Activate.ps1
```

激活成功后，命令行提示符通常会显示虚拟环境名称（例如 `(.venv)`），表示当前处于虚拟环境中。

## 步骤 4：安装项目依赖

在虚拟环境中，使用 `uv pip install` 安装项目所需依赖。例如，安装 `requests` 和 `Flask`：

```bash
uv pip install requests Flask
```

如果项目已有 `requirements.txt` 或 `pyproject.toml` 文件，可以直接安装：

```bash
# 安装 requirements.txt 中的依赖
uv pip install -r requirements.txt

# 安装 pyproject.toml 中的依赖（uv 会自动检测）
uv pip install
```

`uv` 的依赖解析器速度极快，能快速完成依赖安装。

## 步骤 5：导出依赖以实现复现

为确保团队成员能够复现相同的环境，需要锁定依赖并生成配置文件。`uv` 提供了以下两种方式：

### 选项 A：使用 `requirements.txt`（推荐，通用性强）

`requirements.txt` 是 Python 社区广泛使用的依赖管理文件，记录所有直接和间接依赖的精确版本。

```bash
uv pip freeze > requirements.txt
```

此命令将当前虚拟环境中所有包及其版本写入 `requirements.txt`。

### 选项 B：使用 `uv.lock`（更精确）

`uv.lock` 文件记录所有依赖（包括间接依赖）的哈希值，确保在不同机器上字节级一致。运行以下命令，`uv` 会自动生成或更新 `uv.lock`：

```bash
uv pip install
```

如果使用 `pyproject.toml` 管理依赖，可在项目根目录创建以下内容：

```toml
[project]
name = "my-project"
version = "0.1.0"
dependencies = [
    "requests",
    "Flask",
]
```

然后运行：

```bash
uv pip install
```

`uv` 会解析依赖并生成 `uv.lock`。

**选择建议**：

- **使用 `requirements.txt`**：适合大多数项目，兼容传统 Python 工具链（如 `pip`），简单易用。
- **使用 `uv.lock`**：适合复杂项目或需要绝对精确复现的场景，提供更强的版本冲突保障。

## 步骤 6：添加到版本控制

将 `requirements.txt` 或 `uv.lock` 添加到版本控制系统（如 Git）：

```bash
git add requirements.txt  # 或 git add uv.lock
git commit -m "Add project dependencies"
git push
```

**重要**：将 `.venv/` 目录添加到 `.gitignore` 文件中，虚拟环境不应该纳入版本控制。在 `.gitignore` 中添加：

```gitignore
.venv/
```

## 总结

通过以上步骤，你可以使用 `uv` 创建一个隔离、可复现的 Python 虚拟环境，并确保团队成员能够快速复现相同的开发环境。推荐优先使用 `requirements.txt` 确保兼容性，或使用 `uv.lock` 追求更高精度的依赖管理。
