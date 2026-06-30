@echo off
chcp 65001 >nul
setlocal

pushd "%~dp0"

echo ========================================
echo 命令启动器 Windows 打包
echo ========================================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"
set "BOOTSTRAP_PYTHON=python"

if not exist "%VENV_PYTHON%" (
  echo 未找到当前项目虚拟环境，正在创建 .venv...
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
    set "BOOTSTRAP_PYTHON=py"
  )

  rem 使用系统 Python 只负责创建当前项目的虚拟环境。
  %BOOTSTRAP_PYTHON% -m venv .venv
  if errorlevel 1 (
    echo 虚拟环境创建失败。
    echo.
    pause
    popd
    exit /b 1
  )
)

set "PYTHON_CMD=%VENV_PYTHON%"

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
