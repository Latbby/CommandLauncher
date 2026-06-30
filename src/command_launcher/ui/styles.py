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
  width: 14px;
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

/* ── Tab：下划线指示器 ── */
QTabWidget::pane {
  border: none;
  background: transparent;
  padding: 12px 0px 0px 0px;
}

QTabBar::tab {
  background: transparent;
  color: #8b8896;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 8px 16px;
  margin-right: 8px;
  font-weight: 500;
}

QTabBar::tab:selected {
  color: #4a4ecf;
  border-bottom: 2px solid #5b5fe3;
}

QTabBar::tab:hover:!selected {
  color: #4a4a55;
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
