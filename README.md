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

构建 Windows 单目录包：

```bash
python -m PyInstaller --windowed --onedir --name CommandLauncher src/command_launcher/main.py --noconfirm
```

`--windowed` 用来避免双击 exe 时出现额外命令行窗口。

需要单文件 exe 时使用：

```bash
python -m PyInstaller --windowed --onefile --name CommandLauncher src/command_launcher/main.py --noconfirm
```
