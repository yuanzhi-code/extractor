# extractor

## 项目介绍

AI信息聚合器, 基于RSS做信息提取, 并产出每日报告。

## 启动项目

```sh
git clone git@github.com:yuanzhi-code/extractor.git
cd extractor
```

###  安装 uv (如果尚未安装):

推荐使用官方渠道进行安装

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

或者，你更习惯使用pip
```sh
pipx install uv # 或 pip install uv
```

对于 MacOS, 也推荐使用 homebrew 安装

```sh
brew install uv
```

### 创建虚拟环境:

```sh
uv venv
```

### 激活虚拟环境:

```sh
Linux / macOS: source .venv/bin/activate
Windows (CMD): .venv\Scripts\activate.bat
Windows (PowerShell): .venv\Scripts\Activate.ps1
```

### 安装依赖:
```sh
uv sync # or uv pip install -r requirements.txt
```
