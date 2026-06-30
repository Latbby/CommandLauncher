@echo off
chcp 65001 >nul
setlocal

pushd "%~dp0"

set "BUILD_TMP=%~dp0.build_tmp"
if not exist "%BUILD_TMP%\temp" mkdir "%BUILD_TMP%\temp"
if not exist "%BUILD_TMP%\pip-cache" mkdir "%BUILD_TMP%\pip-cache"
set "TEMP=%BUILD_TMP%\temp"
set "TMP=%BUILD_TMP%\temp"
set "PIP_CACHE_DIR=%BUILD_TMP%\pip-cache"
set "_PYI_ARCHIVE_FILE="
set "_PYI_APPLICATION_HOME_DIR="
set "_PYI_PARENT_PROCESS_LEVEL="
set "PYINSTALLER_RESET_ENVIRONMENT=1"

echo ========================================
echo 命令启动器 Windows 打包
echo ========================================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"
set "BOOTSTRAP_PYTHON=python"

echo [1/4] 更新 master 分支...
where git >nul 2>nul
if errorlevel 1 goto git_missing

git checkout master
if errorlevel 1 goto git_update_failed

git pull --ff-only origin master
if errorlevel 1 goto git_update_failed

echo.
if exist "%VENV_PYTHON%" goto use_venv

echo 未找到当前项目虚拟环境，正在创建 .venv...
where python >nul 2>nul
if not errorlevel 1 goto create_venv

where py >nul 2>nul
if errorlevel 1 goto python_missing
set "BOOTSTRAP_PYTHON=py"

:create_venv
rem 使用系统 Python 只负责创建当前项目的虚拟环境。
%BOOTSTRAP_PYTHON% -m venv .venv
if errorlevel 1 goto venv_failed

:use_venv
set "PYTHON_CMD=%VENV_PYTHON%"

echo [2/4] 使用 Python:
%PYTHON_CMD% --version
if errorlevel 1 goto python_failed

echo.
echo [3/4] 安装或更新项目依赖...
%PYTHON_CMD% -m pip install -e ".[dev]"
if errorlevel 1 goto install_failed

echo.
echo [4/4] 打包 Windows exe...
tasklist /FI "IMAGENAME eq CommandLauncher.exe" 2>nul | find /I "CommandLauncher.exe" >nul
if not errorlevel 1 goto app_running

%PYTHON_CMD% -m PyInstaller --clean --noconfirm CommandLauncher.spec
if errorlevel 1 goto build_failed

echo.
echo 打包完成:
echo dist\CommandLauncher\CommandLauncher.exe
echo.
pause
popd
endlocal
exit /b 0

:python_missing
echo 未找到 Python。请先安装 Python，并勾选 Add Python to PATH。
goto fail

:git_missing
echo 未找到 Git。请先安装 Git，并确保 git 命令可用。
goto fail

:git_update_failed
echo 更新 master 分支失败。请确认当前工作区没有未提交改动，并检查网络或远端仓库配置。
goto fail

:venv_failed
echo 虚拟环境创建失败。
goto fail

:python_failed
echo Python 启动失败。
goto fail

:install_failed
echo 依赖安装失败。
goto fail

:build_failed
echo 打包失败。
goto fail

:app_running
echo 请先关闭正在运行的 CommandLauncher.exe，然后重新打包。
goto fail

:fail
echo.
pause
popd
endlocal
exit /b 1
