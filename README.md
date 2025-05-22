# extractor

## 项目介绍
AI信息聚合器, 基于RSS做信息提取, 并产出每日报告。

## 启动项目

```
git clone git@github.com:yuanzhi-code/extractor.git
cd extractor
```

安装 uv (如果尚未安装):

```
pipx install uv # 或 pip install uv
```

创建虚拟环境:
```
uv venv
```
激活虚拟环境:
Linux / macOS: 
```
source .venv/bin/activate
```
Windows (CMD): 
```
.venv\Scripts\activate.bat
```
Windows (PowerShell):
```
.venv\Scripts\Activate.ps1
````
安装依赖:
```
uv pip install -r requirements.txt
```