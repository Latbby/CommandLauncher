# Project Launcher 设计文档

## 背景

Project Launcher 是一个 Windows 桌面小工具，用来保存项目目录，并从选中的项目目录快速打开外部窗口或程序。

第一版聚焦“快速启动”，不做内置终端、不捕获命令输出，也不管理命令运行后的进程。

应用使用 Python + PySide6 开发，并打包成 Windows `.exe`。界面走浅色、现代、偏效率工具的风格。

## 目标

- 保存一个或多个本地项目目录。
- 从左侧固定项目列表选择项目。
- 在选中项目目录中打开 `cmd`、PowerShell 和资源管理器。
- 支持所有项目通用的全局自定义启动命令。
- 支持当前项目独有的项目自定义启动命令。
- 本地持久化配置，并在重启后恢复上次选中的项目。
- 打包为 Windows `.exe`。

## 非目标

- 第一版不做内置终端。
- 第一版不捕获命令输出。
- 第一版不管理自定义命令启动后的进程。
- 第一版不做项目分组、托盘常驻、全局快捷键或命令搜索。
- 第一版不支持跨平台。

## 技术选型

使用 Python + PySide6。

这个选择适合第一版，因为当前需求是 Windows-only 的桌面工具，核心能力是本地配置读写和外部程序启动。PySide6 比 Tkinter 更适合做稍现代的桌面界面，同时开发速度比原生 .NET 更适合快速迭代。Windows 打包使用 PyInstaller。

## 界面设计

主窗口使用固定双栏布局。

左侧面板：

- 项目列表。
- 添加项目按钮。
- 删除选中项目操作。

右侧面板：

- 当前项目名称。
- 当前项目路径。
- 内置启动按钮：`cmd`、`PowerShell`、`Explorer`。
- 全局自定义命令列表。
- 项目自定义命令列表。
- 添加、编辑、删除命令操作。

视觉风格是浅色、现代、克制的效率工具界面，强调清晰间距和可扫描的信息密度。第一版不做主题切换。

## 数据模型

配置使用 JSON 文件保存，路径为：

```text
%APPDATA%\CommandLauncher\config.json
```

配置结构为：

```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "command-launcher",
      "path": "D:\\work\\command-launcher",
      "commands": [
        {
          "id": "uuid",
          "name": "VS Code",
          "command": "code ."
        }
      ]
    }
  ],
  "globalCommands": [
    {
      "id": "uuid",
      "name": "VS Code",
      "command": "code ."
    }
  ],
  "lastSelectedProjectId": "uuid"
}
```

规则：

- 添加项目时，默认使用目录名作为项目名。
- 重复添加相同路径时，不创建重复项目，只选中已有项目。
- 删除项目只删除本地配置项，不删除真实磁盘目录。
- 第一版的命令只包含显示名称和命令文本。
- 命令名称或命令文本为空时，不允许保存。

## 命令启动规则

所有启动命令都以当前选中项目目录作为工作目录。

内置命令使用明确的可执行文件和参数启动：

- `cmd`：`cmd.exe /K cd /d "<项目路径>"`
- `PowerShell`：`powershell.exe -NoExit -Command Set-Location -LiteralPath '<项目路径>'`
- `Explorer`：`explorer.exe "<项目路径>"`

自定义命令使用 Windows shell 方式启动，并把工作目录设置为当前项目目录。这样用户可以直接填写 `code .`、`wt -d .` 或其他可从系统环境变量中找到的命令。

## 异常处理

- 如果项目路径不存在，项目仍保留在列表中，但启动操作禁用或显示明确的路径无效提示。
- 如果命令为空，编辑弹窗阻止保存。
- 如果命令启动失败，应用弹窗显示失败命令和异常原因。
- 如果配置文件不存在，应用使用空配置启动。
- 如果配置文件格式损坏，应用将原文件备份为 `config.broken.<timestamp>.json`，再创建新的空配置。
- 如果外部程序不存在，应用只提示启动失败，不尝试安装或修复。

## 项目结构

```text
command-launcher/
  pyproject.toml
  README.md
  src/
    command_launcher/
      __init__.py
      main.py
      app.py
      models.py
      config_store.py
      command_runner.py
      ui/
        main_window.py
        project_panel.py
        command_panel.py
        dialogs.py
        styles.py
  tests/
    test_config_store.py
    test_command_runner.py
```

模块职责：

- `main.py`：程序入口。
- `app.py`：Qt 应用初始化。
- `models.py`：项目、命令和配置的数据结构。
- `config_store.py`：读取、保存、校验和恢复本地配置。
- `command_runner.py`：构造并启动内置命令和自定义命令。
- `ui/`：PySide6 主窗口、面板、弹窗和样式。
- `tests/`：配置和命令构造相关的单元测试。

## 测试与验证

自动化测试使用 `pytest`。

主要单元测试：

- 配置文件不存在时加载为空配置。
- 保存并重新读取项目和命令。
- 重复项目路径不会创建重复项目。
- 配置文件损坏时会备份并恢复为空配置。
- 内置命令参数构造正确。
- 模型或 UI 校验层拒绝空自定义命令。

手工验证：

- 添加真实项目目录。
- 重复添加同一项目目录，确认不会重复。
- 从项目目录打开 `cmd`、PowerShell 和资源管理器。
- 添加、编辑、删除全局命令。
- 添加、编辑、删除项目命令。
- 重启应用，确认配置仍然保留。
- 重命名或删除项目目录，确认路径无效处理正确。
- 手动破坏 JSON 配置，确认备份和恢复行为正确。

## 打包方案

使用 PyInstaller 做 Windows 打包。

第一版先使用 `--onedir`，因为它更容易调试，对 PySide6 也更稳。应用稳定后，可以再评估 `--onefile`。应用图标和版本信息属于后续打磨项，除非第一版可用构建明确需要。
