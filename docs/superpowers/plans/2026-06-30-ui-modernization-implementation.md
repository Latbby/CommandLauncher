# UI Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不更换 PySide6 技术栈的前提下，把命令启动器改成更现代、紧凑、清晰的轻量 Windows 工具界面。

**Architecture:** 保留现有业务逻辑和公开控件属性名，重组 `MainWindow` 的布局结构，引入 `QSplitter`、`QTabWidget` 和 `QStatusBar`。样式继续集中在 `styles.py`，通过 QSS 类名和对象名区分主按钮、次级按钮、危险按钮、面板、路径文本和列表状态。

**Tech Stack:** Python 3.11、PySide6 Qt Widgets、Qt Style Sheets、pytest、Qt offscreen 测试。

---

## 文件结构

- 修改：`src/command_launcher/ui/main_window.py`
  - 负责创建新的左右分栏布局、命令 Tab、状态栏和按钮层级。
  - 保持现有按钮属性名不变，避免破坏已有测试和逻辑。
- 修改：`src/command_launcher/ui/styles.py`
  - 负责现代化 QSS 样式。
  - 为面板、列表、主按钮、次级按钮、危险按钮、Tab 和状态栏提供统一视觉规则。
- 修改：`tests/test_ui_imports.py`
  - 增加轻量 UI 结构测试，验证新组件存在、按钮文案保持兼容、路径不存在时状态栏提示可见。

## 任务拆分

### Task 1: 用测试锁定现代化布局骨架

**Files:**
- Modify: `tests/test_ui_imports.py`

- [ ] **Step 1: 编写失败测试，验证新增布局组件和对象名**

在 `tests/test_ui_imports.py` 追加以下测试。测试数据使用临时配置文件，不伪造项目目录，验证空配置下窗口仍能创建现代化布局骨架。

```python
def test_main_window_uses_modern_layout_components(tmp_path, monkeypatch):
    """验证主窗口暴露现代化布局组件。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 提供的环境变量修改工具。
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QSplitter, QTabWidget

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    # 主布局使用可拖动分栏，命令区域使用 Tab 降低纵向堆叠。
    assert isinstance(window.main_splitter, QSplitter)
    assert isinstance(window.command_tabs, QTabWidget)
    assert window.command_tabs.count() == 2
    assert window.command_tabs.tabText(0) == "全局命令"
    assert window.command_tabs.tabText(1) == "项目命令"

    # 样式对象名用于 QSS 精准命中，避免影响对话框内部控件。
    assert window.project_name.objectName() == "projectTitle"
    assert window.project_path.objectName() == "projectPath"
    assert window.remove_project_button.property("variant") == "danger"
    assert window.add_global_button.property("variant") == "secondary"

    window.close()
    app.processEvents()
```

- [ ] **Step 2: 编写失败测试，验证路径不存在时状态栏提示**

在同一个文件追加以下测试。测试构造一个不存在路径的真实输入，符合当前业务逻辑，不依赖命令执行。

```python
def test_main_window_status_bar_warns_when_project_path_missing(tmp_path, monkeypatch):
    """验证项目路径不存在时状态栏显示轻量提示。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 提供的环境变量修改工具。
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, Project
    from command_launcher.ui.main_window import MainWindow

    missing_path = tmp_path / "missing-project"
    config_path = tmp_path / "config.json"
    store = ConfigStore(config_path)
    project = Project(name="缺失项目", path=str(missing_path))
    store.save(AppConfig(projects=[project], last_selected_project_id=project.id))

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=store)

    # 不存在的项目路径会禁用启动按钮，并通过状态栏提供轻量反馈。
    assert window.cmd_button.isEnabled() is False
    assert window.powershell_button.isEnabled() is False
    assert window.explorer_button.isEnabled() is False
    assert window.statusBar().currentMessage() == "项目路径不存在，启动操作已禁用。"

    window.close()
    app.processEvents()
```

- [ ] **Step 3: 运行新增测试，确认失败来自未实现组件**

Run:

```bash
python -m pytest tests/test_ui_imports.py::test_main_window_uses_modern_layout_components tests/test_ui_imports.py::test_main_window_status_bar_warns_when_project_path_missing -v
```

Expected:

```text
FAILED tests/test_ui_imports.py::test_main_window_uses_modern_layout_components
FAILED tests/test_ui_imports.py::test_main_window_status_bar_warns_when_project_path_missing
```

失败原因应包含 `AttributeError: 'MainWindow' object has no attribute 'main_splitter'` 或状态栏消息不匹配。

- [ ] **Step 4: 提交测试**

```bash
git add tests/test_ui_imports.py
git commit -m "test: 添加界面现代化布局测试"
```

### Task 2: 重组主窗口布局并保持既有交互

**Files:**
- Modify: `src/command_launcher/ui/main_window.py`
- Test: `tests/test_ui_imports.py`

- [ ] **Step 1: 调整导入**

在 `main_window.py` 的 `PySide6.QtWidgets` 导入中加入 `QSplitter`、`QTabWidget`，保持其它导入不变。

```python
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
```

- [ ] **Step 2: 在 `__init__` 中保留原有属性并增加布局属性**

在 `self.project_commands = QListWidget()` 后追加以下属性。方法注释沿用现有风格，新增内部注释使用中文。

```python
        self.main_splitter = QSplitter()
        self.command_tabs = QTabWidget()
```

- [ ] **Step 3: 替换 `_build_layout` 为现代化布局**

用以下完整方法替换现有 `_build_layout`。该实现保留所有现有按钮属性名，避免破坏 `_connect_signals` 和已有测试。

```python
    def _build_layout(self) -> None:
        """构建左右分栏的现代化主界面布局。"""
        root = QHBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)

        sidebar = self._build_sidebar()
        content = self._build_content_panel()
        self.main_splitter.addWidget(sidebar)
        self.main_splitter.addWidget(content)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setSizes([260, 720])

        root.addWidget(self.main_splitter)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.statusBar().setObjectName("statusBar")
```

- [ ] **Step 4: 新增 `_build_sidebar` 方法**

将该方法放在 `_build_layout` 后面。它只负责左侧项目栏，边界清晰。

```python
    def _build_sidebar(self) -> QFrame:
        """构建左侧项目列表面板。

        Returns:
            已配置布局和样式标记的项目面板。
        """
        sidebar = QFrame()
        sidebar.setObjectName("sidebarPanel")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(10)

        title = QLabel("项目")
        title.setObjectName("sectionTitle")
        self.project_list.setObjectName("projectList")

        self.add_project_button = QPushButton("添加")
        self.remove_project_button = QPushButton("移除")
        self.add_project_button.setProperty("variant", "secondary")
        self.remove_project_button.setProperty("variant", "danger")

        project_actions = QHBoxLayout()
        project_actions.setSpacing(8)
        project_actions.addWidget(self.add_project_button)
        project_actions.addWidget(self.remove_project_button)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.project_list, 1)
        sidebar_layout.addLayout(project_actions)
        return sidebar
```

- [ ] **Step 5: 新增 `_build_content_panel` 方法**

将该方法放在 `_build_sidebar` 后面。它只负责右侧内容区的主结构。

```python
    def _build_content_panel(self) -> QFrame:
        """构建右侧项目详情和命令面板。

        Returns:
            已配置布局和样式标记的内容面板。
        """
        content = QFrame()
        content.setObjectName("contentPanel")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        self.project_name.setObjectName("projectTitle")
        self.project_path.setObjectName("projectPath")
        self.project_path.setWordWrap(True)

        content_layout.addWidget(self.project_name)
        content_layout.addWidget(self.project_path)
        content_layout.addLayout(self._build_builtin_actions())
        content_layout.addWidget(self._build_command_tabs(), 1)
        return content
```

- [ ] **Step 6: 新增 `_build_builtin_actions` 方法**

将该方法放在 `_build_content_panel` 后面。它只负责三个主启动按钮。

```python
    def _build_builtin_actions(self) -> QHBoxLayout:
        """构建内置启动操作按钮组。

        Returns:
            包含 CMD、PowerShell 和资源管理器按钮的横向布局。
        """
        for button in (self.cmd_button, self.powershell_button, self.explorer_button):
            button.setProperty("variant", "primary")

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(self.cmd_button)
        actions.addWidget(self.powershell_button)
        actions.addWidget(self.explorer_button)
        actions.addStretch(1)
        return actions
```

- [ ] **Step 7: 新增 `_build_command_tabs` 和 `_build_command_tab` 方法**

将以下两个方法放在 `_build_builtin_actions` 后面。命令列表和按钮组被封装到同一个 Tab 内。

```python
    def _build_command_tabs(self) -> QTabWidget:
        """构建全局命令和项目命令 Tab。

        Returns:
            包含两个命令列表页面的 Tab 控件。
        """
        self.command_tabs.setObjectName("commandTabs")
        self.add_global_button = QPushButton("添加")
        self.edit_global_button = QPushButton("编辑")
        self.delete_global_button = QPushButton("删除")
        self.add_project_command_button = QPushButton("添加")
        self.edit_project_command_button = QPushButton("编辑")
        self.delete_project_command_button = QPushButton("删除")

        global_tab = self._build_command_tab(
            self.global_commands,
            self.add_global_button,
            self.edit_global_button,
            self.delete_global_button,
        )
        project_tab = self._build_command_tab(
            self.project_commands,
            self.add_project_command_button,
            self.edit_project_command_button,
            self.delete_project_command_button,
        )
        self.command_tabs.addTab(global_tab, "全局命令")
        self.command_tabs.addTab(project_tab, "项目命令")
        return self.command_tabs

    def _build_command_tab(
        self,
        command_list: QListWidget,
        add_button: QPushButton,
        edit_button: QPushButton,
        delete_button: QPushButton,
    ) -> QWidget:
        """构建单个命令 Tab 页面。

        Args:
            command_list: 用于展示命令的列表控件。
            add_button: 添加命令按钮。
            edit_button: 编辑命令按钮。
            delete_button: 删除命令按钮。

        Returns:
            包含命令列表和按钮组的 Tab 页面。
        """
        command_list.setObjectName("commandList")
        add_button.setProperty("variant", "secondary")
        edit_button.setProperty("variant", "secondary")
        delete_button.setProperty("variant", "danger")

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)
        actions.addStretch(1)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(command_list, 1)
        layout.addLayout(actions)
        return tab
```

- [ ] **Step 8: 更新 `_render_project` 状态栏逻辑**

在 `_render_project` 中设置按钮启用状态后，追加状态栏提示。保留原有命令列表刷新逻辑。

```python
        if not project:
            self.statusBar().showMessage("请选择或添加一个项目。")
        elif enabled:
            self.statusBar().showMessage("已选择项目。")
        else:
            self.statusBar().showMessage("项目路径不存在，启动操作已禁用。")
```

- [ ] **Step 9: 更新已有测试的按钮文案期望**

在 `tests/test_ui_imports.py` 的 `test_main_window_exposes_command_edit_actions` 中，将命令管理按钮文案断言改为新按钮短文案。

```python
    assert window.cmd_button.text() == "打开命令提示符"
    assert window.powershell_button.text() == "打开 PowerShell"
    assert window.explorer_button.text() == "打开资源管理器"
    assert window.edit_global_button.text() == "编辑"
    assert window.edit_project_command_button.text() == "编辑"
```

- [ ] **Step 10: 运行 UI 测试**

Run:

```bash
python -m pytest tests/test_ui_imports.py -v
```

Expected:

```text
5 passed
```

- [ ] **Step 11: 提交主窗口布局改造**

```bash
git add src/command_launcher/ui/main_window.py tests/test_ui_imports.py
git commit -m "feat: 重组主窗口现代化布局"
```

### Task 3: 更新 QSS 样式并做完整验证

**Files:**
- Modify: `src/command_launcher/ui/styles.py`
- Test: `tests/test_ui_imports.py`

- [ ] **Step 1: 替换 `LIGHT_STYLESHEET`**

用以下样式替换 `styles.py` 中的 `LIGHT_STYLESHEET`。样式只使用 Qt Widgets 支持的 QSS 选择器，避免引入第三方依赖。

```python
LIGHT_STYLESHEET = """
QMainWindow {
  background: #f3f4f6;
}

QFrame#sidebarPanel,
QFrame#contentPanel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

QSplitter#mainSplitter::handle {
  background: transparent;
  width: 12px;
}

QLabel {
  color: #111827;
}

QLabel#sectionTitle {
  color: #374151;
  font-size: 13px;
  font-weight: 700;
}

QLabel#projectTitle {
  color: #111827;
  font-size: 22px;
  font-weight: 700;
}

QLabel#projectPath {
  color: #6b7280;
  font-size: 12px;
}

QListWidget {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 7px;
  outline: none;
  padding: 4px;
}

QListWidget::item {
  color: #111827;
  min-height: 32px;
  padding: 6px 8px;
  border-radius: 5px;
}

QListWidget::item:hover {
  background: #f3f4f6;
}

QListWidget::item:selected {
  background: #dbeafe;
  color: #1d4ed8;
}

QPushButton {
  border-radius: 6px;
  padding: 8px 12px;
  font-weight: 600;
}

QPushButton[variant="primary"] {
  background: #2563eb;
  color: #ffffff;
  border: 1px solid #2563eb;
}

QPushButton[variant="primary"]:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

QPushButton[variant="secondary"] {
  background: #ffffff;
  color: #374151;
  border: 1px solid #d1d5db;
}

QPushButton[variant="secondary"]:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

QPushButton[variant="danger"] {
  background: #ffffff;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

QPushButton[variant="danger"]:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}

QPushButton:disabled {
  background: #e5e7eb;
  color: #9ca3af;
  border: 1px solid #e5e7eb;
}

QTabWidget::pane {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px;
  background: #ffffff;
}

QTabBar::tab {
  background: #f9fafb;
  color: #4b5563;
  border: 1px solid #e5e7eb;
  padding: 8px 14px;
  margin-right: 4px;
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

QTabBar::tab:selected {
  background: #ffffff;
  color: #1d4ed8;
  border-bottom-color: #ffffff;
}

QLineEdit {
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px;
  color: #111827;
}

QLineEdit:focus {
  border-color: #2563eb;
}

QStatusBar#statusBar {
  background: #f3f4f6;
  color: #6b7280;
}
"""
```

- [ ] **Step 2: 增加样式内容测试**

在 `tests/test_ui_imports.py` 追加以下测试，锁定关键 QSS 选择器，防止后续误删对象名相关样式。

```python
def test_light_stylesheet_contains_modern_selectors():
    """验证现代化界面依赖的关键样式选择器存在。"""
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QFrame#sidebarPanel" in LIGHT_STYLESHEET
    assert "QFrame#contentPanel" in LIGHT_STYLESHEET
    assert 'QPushButton[variant="primary"]' in LIGHT_STYLESHEET
    assert 'QPushButton[variant="secondary"]' in LIGHT_STYLESHEET
    assert 'QPushButton[variant="danger"]' in LIGHT_STYLESHEET
    assert "QTabWidget::pane" in LIGHT_STYLESHEET
```

- [ ] **Step 3: 运行样式测试**

Run:

```bash
python -m pytest tests/test_ui_imports.py::test_light_stylesheet_contains_modern_selectors -v
```

Expected:

```text
1 passed
```

- [ ] **Step 4: 运行完整测试**

Run:

```bash
python -m pytest -v
```

Expected:

```text
所有测试通过
```

测试总结需要记录：

- 入参：`tests/test_ui_imports.py::test_main_window_uses_modern_layout_components`。出参：主窗口包含 `QSplitter`、`QTabWidget` 和按钮样式属性。
- 入参：`tests/test_ui_imports.py::test_main_window_status_bar_warns_when_project_path_missing`。出参：缺失路径禁用启动按钮并显示状态栏提示。
- 入参：`tests/test_ui_imports.py::test_light_stylesheet_contains_modern_selectors`。出参：关键 QSS 选择器存在。
- 入参：`python -m pytest -v`。出参：全量测试通过。

- [ ] **Step 5: 可选手动启动应用检查视觉效果**

Run:

```bash
python -m command_launcher.main
```

Expected:

```text
应用窗口启动，左侧项目栏、右侧项目详情、命令 Tab 和按钮层级显示正常。
```

手动验证总结：

- 入参：启动应用。出参：窗口显示左右分栏，左右栏可拖动。
- 入参：选择项目。出参：右侧项目名称、路径和命令列表刷新。
- 入参：切换命令 Tab。出参：全局命令和项目命令区域正常切换。

- [ ] **Step 6: 提交样式优化**

```bash
git add src/command_launcher/ui/styles.py tests/test_ui_imports.py
git commit -m "style: 优化主窗口现代化样式"
```

## 自检结果

- 规格覆盖：计划覆盖了布局重组、QSS 统一样式、状态栏提示、既有功能兼容和测试验证。
- 红旗词扫描：计划中没有未完成标记或“之后补充”式未完成内容。
- 类型一致性：计划中新增属性名为 `main_splitter`、`command_tabs`，测试和实现步骤一致；按钮属性 `variant` 的取值为 `primary`、`secondary`、`danger`，测试和样式一致。
