@echo off
REM 启动前端 Vite 开发服务器（端口 5173）
chcp 65001 >nul
cd /d "%~dp0\frontend"

if not exist "node_modules" (
    echo [1/2] 首次启动，安装前端依赖（约 1-3 分钟）...
    call npm install
)

echo [2/2] 启动 Vite 开发服务器（http://localhost:5173）...
call npm run dev
