@echo off
REM 启动后端 Flask 服务（端口 5000）
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv" (
    echo [1/3] 创建 Python 虚拟环境 .venv ...
    python -m venv .venv
)

echo [2/3] 激活虚拟环境并安装依赖 ...
call .venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt

if not exist ".env" (
    echo [警告] 未发现 .env 文件，正在从 .env.example 复制。请在 .env 中填入真实 DEEPSEEK_API_KEY。
    copy /Y .env.example .env >nul
)

echo [3/3] 启动 Flask 后端（http://localhost:5000）...
python -m backend.app
