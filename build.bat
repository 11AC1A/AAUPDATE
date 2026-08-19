@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   通用固件升级程序 - 一键打包脚本
echo ========================================
echo.

:: 检查虚拟环境是否存在
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 未找到虚拟环境 .venv，正在创建...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败！
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
echo [1/4] 激活虚拟环境...
call .venv\Scripts\activate.bat

:: 安装依赖
echo [2/4] 安装依赖...
pip install -r requirements.txt pyinstaller --quiet
if errorlevel 1 (
    echo [错误] 安装依赖失败！
    pause
    exit /b 1
)

:: 清理旧的构建文件
echo [3/4] 清理旧构建...
if exist "build\esp32_flasher" rmdir /s /q "build\esp32_flasher"
if exist "dist\AAHUB_Firmware_Flasher.exe" del /q "dist\AAHUB_Firmware_Flasher.exe"

:: 打包
echo [4/4] 正在打包，请稍候...
pyinstaller esp32_flasher.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo   输出文件: dist\AAHUB_Firmware_Flasher.exe
echo ========================================
echo.
pause
