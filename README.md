# CommandLauncher

一个 Windows 项目命令启动器，用 Python 和 PySide6 编写。

## 功能

- 保存常用项目目录。
- 在选中项目目录中打开命令提示符、PowerShell 和资源管理器。
- 添加全局命令和项目命令。
- 支持浅色/深色主题。
- 支持最小化到系统托盘和开机自启。

## 开发运行

```bash
python -m pip install -e ".[dev]"
command-launcher
```

## 打包

Windows 下推荐双击运行：

```text
build_windows.bat
```

脚本会安装依赖并生成单文件程序：

```text
dist\命令启动器.exe
```

也可以手动执行：

```bash
python -m PyInstaller --clean --noconfirm CommandLauncher.spec
```

`CommandLauncher.spec` 用于固定窗口模式、单文件打包、exe 图标和运行时窗口图标。

## 配置

用户配置保存在：

```text
%APPDATA%\CommandLauncher\config.json
```
