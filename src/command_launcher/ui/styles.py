"""Application stylesheet.

"A tool for developers should feel like it was made by one."
—— Console Craft, 命令启动器视觉系统
"""

LIGHT_STYLESHEET = """
QMainWindow {
  background: #eeede8;
}

/* ── 面板：无边框，纯白浮在暖纸底色上 ── */
QFrame#sidebarPanel,
QFrame#contentPanel {
  background: #ffffff;
  border: none;
  border-radius: 10px;
}

QSplitter#mainSplitter::handle {
  background: transparent;
}

/* ── 标签基础 ── */
QLabel {
  color: #1c1c22;
}

/* 区域标题：小而精准 */
QLabel#sectionTitle {
  color: #8b8896;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* 项目名：大号，稳重 */
QLabel#projectTitle {
  color: #1c1c22;
  font-size: 22px;
  font-weight: 700;
  font-family: "Segoe UI";
}

/* 项目路径：等宽字体 — 签名元素 */
QLabel#projectPath {
  color: #5b5fe3;
  font-size: 13px;
  font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
}

/* ── 列表：无边框，微暖底色 ── */
QListWidget {
  background: #f8f7f4;
  border: none;
  border-radius: 8px;
  outline: none;
  padding: 4px;
}

QListWidget::item {
  color: #1c1c22;
  min-height: 34px;
  padding: 6px 10px;
  margin: 1px 0px;
  border-radius: 5px;
}

QListWidget::item:hover {
  background: #eae9e5;
}

QListWidget::item:selected {
  background: #eceafe;
  color: #4a4ecf;
}

/* 命令列表 */
QTabWidget#commandTabs {
  background: transparent;
}

QTabWidget#commandTabs::pane {
  border: none;
  padding: 0px;
  margin: 0px;
}

QTabWidget#commandTabs QTabBar::tab {
  background: transparent;
  color: #8b8896;
  border: none;
  padding: 7px 12px;
  margin-right: 4px;
  font-size: 13px;
  font-weight: 600;
}

QTabWidget#commandTabs QTabBar::tab:selected {
  color: #4a4ecf;
  background: #eceafe;
  border-radius: 5px;
}

QListWidget#commandList {
  font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
  padding: 1px;
}

QListWidget#commandList::item {
  padding: 0px;
  border: none;
  border-radius: 5px;
  margin: 0px;
}

QListWidget#commandList::item:hover {
  background: transparent;
}

QListWidget#commandList::item:selected,
QListWidget#commandList::item:selected:active,
QListWidget#commandList::item:selected:!active {
  background: transparent;
  color: #1c1c22;
}

/* 命令名称 */
QLabel#commandName {
  color: #1c1c22;
  font-size: 18px;
}

/* ── 列表内操作按钮（编辑/删除，悬浮时出现） ── */
QPushButton#itemActionBtn {
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 500;
}

/* ── 按钮 ── */
QPushButton {
  border-radius: 6px;
  padding: 8px 14px;
  font-weight: 600;
  font-size: 13px;
}

/* 主按钮：靛蓝，无边框 */
QPushButton[variant="primary"] {
  background: #5b5fe3;
  color: #ffffff;
  border: none;
}

QPushButton[variant="primary"]:hover {
  background: #4a4ecf;
}

QPushButton[variant="primary"]:pressed {
  background: #3b3fb8;
}

/* 次级填充按钮：浅靛蓝底 */
QPushButton[variant="secondary-fill"] {
  background: #eef2ff;
  color: #4338ca;
  border: 1px solid #c7d2fe;
}

QPushButton[variant="secondary-fill"]:hover {
  background: #e0e7ff;
  border-color: #a5b4fc;
}

/* 次级按钮：透明底，细线 */
QPushButton[variant="secondary"] {
  background: transparent;
  color: #4a4a55;
  border: 1px solid #d4d2cc;
}

QPushButton[variant="secondary"]:hover {
  background: #f5f4f0;
  border-color: #b8b5ae;
}

/* 危险按钮 */
QPushButton[variant="danger"] {
  background: transparent;
  color: #d64545;
  border: 1px solid #f3cdcd;
}

QPushButton[variant="danger"]:hover {
  background: #fdf0f0;
  border-color: #e8afaf;
}

QPushButton:disabled {
  background: #f3f2ef;
  color: #c5c3be;
  border: none;
}

/* ── 输入框 ── */
QLineEdit {
  background: #ffffff;
  border: 1px solid #d4d2cc;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: #1c1c22;
}

QLineEdit:focus {
  border-color: #5b5fe3;
}

/* ── 状态栏 ── */
QStatusBar#statusBar {
  background: #eeede8;
  color: #8b8896;
  font-size: 12px;
}
"""

DARK_STYLESHEET = """
QMainWindow,
QDialog {
  background: #15161a;
}

/* ── 面板：深色模式下保持低对比容器层级 ── */
QFrame#sidebarPanel,
QFrame#contentPanel {
  background: #202127;
  border: none;
  border-radius: 10px;
}

QSplitter#mainSplitter::handle {
  background: transparent;
}

QLabel {
  color: #f3f4f8;
}

QLabel#sectionTitle {
  color: #a5a7b3;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

QLabel#projectTitle {
  color: #f3f4f8;
  font-size: 22px;
  font-weight: 700;
  font-family: "Segoe UI";
}

QLabel#projectPath {
  color: #7c83ff;
  font-size: 13px;
  font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
}

QListWidget {
  background: #262832;
  border: none;
  border-radius: 8px;
  outline: none;
  padding: 4px;
}

QListWidget::item {
  color: #f3f4f8;
  min-height: 34px;
  padding: 6px 10px;
  margin: 1px 0px;
  border-radius: 5px;
}

QListWidget::item:hover {
  background: #30323e;
}

QListWidget::item:selected {
  background: #343756;
  color: #f3f4f8;
}

QTabWidget#commandTabs {
  background: transparent;
}

QTabWidget#commandTabs::pane {
  border: none;
  padding: 0px;
  margin: 0px;
}

QTabWidget#commandTabs QTabBar::tab {
  background: transparent;
  color: #a5a7b3;
  border: none;
  padding: 7px 12px;
  margin-right: 4px;
  font-size: 13px;
  font-weight: 600;
}

QTabWidget#commandTabs QTabBar::tab:selected {
  color: #ffffff;
  background: #343756;
  border-radius: 5px;
}

QListWidget#commandList {
  font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
  padding: 1px;
}

QListWidget#commandList::item {
  padding: 0px;
  border: none;
  border-radius: 5px;
  margin: 0px;
}

QListWidget#commandList::item:hover {
  background: transparent;
}

QListWidget#commandList::item:selected,
QListWidget#commandList::item:selected:active,
QListWidget#commandList::item:selected:!active {
  background: transparent;
  color: #f3f4f8;
}

QLabel#commandName {
  color: #f3f4f8;
  font-size: 18px;
}

QPushButton#itemActionBtn {
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 500;
}

QPushButton {
  border-radius: 6px;
  padding: 8px 14px;
  font-weight: 600;
  font-size: 13px;
}

QPushButton[variant="primary"] {
  background: #7c83ff;
  color: #ffffff;
  border: none;
}

QPushButton[variant="primary"]:hover {
  background: #8f95ff;
}

QPushButton[variant="primary"]:pressed {
  background: #6c72e8;
}

QPushButton[variant="secondary-fill"] {
  background: #30334a;
  color: #f3f4f8;
  border: 1px solid #484c6b;
}

QPushButton[variant="secondary-fill"]:hover {
  background: #393d58;
  border-color: #5b6084;
}

QPushButton[variant="secondary"] {
  background: transparent;
  color: #f3f4f8;
  border: 1px solid #3b3d49;
}

QPushButton[variant="secondary"]:hover {
  background: #262832;
  border-color: #565966;
}

QPushButton[variant="danger"] {
  background: transparent;
  color: #ff8585;
  border: 1px solid #604040;
}

QPushButton[variant="danger"]:hover {
  background: #3a2428;
  border-color: #855258;
}

QPushButton:disabled {
  background: #24262e;
  color: #6d707c;
  border: none;
}

QLineEdit {
  background: #262832;
  border: 1px solid #3b3d49;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: #f3f4f8;
}

QLineEdit:focus {
  border-color: #7c83ff;
}

QSlider#themeSwitch {
  min-height: 20px;
}

QSlider#themeSwitch::groove:horizontal {
  background: #262832;
  border: 1px solid #3b3d49;
  border-radius: 8px;
  height: 16px;
}

QSlider#themeSwitch::handle:horizontal {
  background: #7c83ff;
  border: none;
  border-radius: 7px;
  width: 14px;
  margin: 1px;
}

QStatusBar#statusBar {
  background: #15161a;
  color: #a5a7b3;
  font-size: 12px;
}
"""
