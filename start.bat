@echo off
setlocal

echo ========================================
echo   Origin Pro 2024 MCP Server
echo ========================================
echo.

where uvx >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] uvx not found, trying pip...
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python not found. Please install Python 3.10+ and uv.
        goto :fail
    )
    pip install -e "%~dp0." --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] pip install failed.
        goto :fail
    )
    echo [INFO] Starting MCP Server...
    python -m origin_pro_mcp.server
    goto :done
)

echo [INFO] Starting MCP Server with uvx...
uvx origin-pro-mcp
goto :done

:fail
echo.
echo Start failed.
pause
exit /b 1

:done
pause
exit /b 0
