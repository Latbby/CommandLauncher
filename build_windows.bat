@echo off
chcp 65001 >nul
setlocal

pushd "%~dp0"

echo ========================================
echo 命令启动器 Windows 打包
echo ========================================
echo.

set "PYTHON_CMD=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo 未找到 Python。请先安装 Python，并勾选 Add Python to PATH。
    echo.
    pause
    popd
    exit /b 1
  )
  set "PYTHON_CMD=py"
)

echo [1/3] 使用 Python:
%PYTHON_CMD% --version
if errorlevel 1 (
  echo Python 启动失败。
  echo.
  pause
  popd
  exit /b 1
)

echo.
echo [2/3] 安装或更新项目依赖...
%PYTHON_CMD% -m pip install -e ".[dev]"
if errorlevel 1 (
  echo 依赖安装失败。
  echo.
  pause
  popd
  exit /b 1
)

echo.
echo [3/3] 打包 Windows exe...
%PYTHON_CMD% -m PyInstaller --windowed --onedir --name CommandLauncher src\command_launcher\main.py --noconfirm
if errorlevel 1 (
  echo 打包失败。
  echo.
  pause
  popd
  exit /b 1
)

echo.
echo 打包完成:
echo dist\CommandLauncher\CommandLauncher.exe
echo.
pause

popd
endlocal
