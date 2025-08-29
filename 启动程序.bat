@echo off
title 贷款分期金融计算器
echo 正在启动贷款分期金融计算器...
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

:: 运行程序
python loan_calculator.py

pause