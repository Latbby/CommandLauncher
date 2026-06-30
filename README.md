# 命令启动器

使用 Python 和 PySide6 开发的 Windows 命令启动器。

## 开发

```bash
python -m pip install -e ".[dev]"
python -m pytest
command-launcher
```

## 功能

- 保存项目目录。
- 从选中的项目目录打开 `cmd`、PowerShell 和资源管理器。
- 添加所有项目通用的全局命令。
- 添加当前项目独有的项目命令。
- 配置保存到 `%APPDATA%\CommandLauncher\config.json`。

## 打包

推荐在 Windows 中双击运行：

```text
build_windows.bat
```

脚本会自动安装依赖并生成：

```text
dist\CommandLauncher\CommandLauncher.exe
```

构建 Windows 单目录包：

```bash
python -m PyInstaller --clean --noconfirm CommandLauncher.spec
```

`--clean` 用来清理 PyInstaller 旧缓存，避免 exe 继续沿用旧图标。
`CommandLauncher.spec` 固定窗口模式、单目录包、exe 资源管理器图标和运行时窗口图标。
