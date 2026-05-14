@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Origin Pro 2024 MCP Server
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+.
    pause
    exit /b 1
)

:: 检查 uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] uv not found, fallback to pip.
    echo.
    echo Installing dependencies with pip...
    pip install -e "%~dp0." --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] pip install failed.
        pause
        exit /b 1
    )
    echo Starting MCP Server...
    python -m origin_pro_mcp.server
) else (
    echo Starting MCP Server with uv...
    uv run --directory "%~dp0." origin-pro-mcp
)

pause
