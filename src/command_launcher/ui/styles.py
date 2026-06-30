"""Application stylesheet."""

LIGHT_STYLESHEET = """
QMainWindow {
  background: #f0f2f5;
}

/* 面板 — 无边框，靠背景色和圆角区分 */
QFrame#sidebarPanel,
QFrame#contentPanel {
  background: #ffffff;
  border: none;
  border-radius: 10px;
}

/* 终端面板容器 — 同样无边框风格 */
QFrame#terminalPanel {
  background: #ffffff;
  border: none;
  border-radius: 10px;
}

QSplitter#mainSplitter::handle {
  background: transparent;
  width: 12px;
}

QSplitter#contentSplitter::handle {
  background: transparent;
  height: 8px;
}

QLabel {
  color: #111827;
}

/* 区域标题 — 小号大写 */
QLabel#sectionTitle {
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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

/* 列表 — 无边框，柔和背景 */
QListWidget {
  background: #f9fafb;
  border: none;
  border-radius: 8px;
  outline: none;
  padding: 4px;
}

QListWidget::item {
  color: #111827;
  min-height: 32px;
  padding: 6px 10px;
  margin: 2px 0px;
  border-radius: 5px;
}

QListWidget::item:hover {
  background: #e5e7eb;
}

QListWidget::item:selected {
  background: #dbeafe;
  color: #1d4ed8;
}

/* 按钮基础 */
QPushButton {
  border-radius: 6px;
  padding: 8px 14px;
  font-weight: 600;
}

/* 主按钮 — 纯色填充，无边框 */
QPushButton[variant="primary"] {
  background: #2563eb;
  color: #ffffff;
  border: none;
}

QPushButton[variant="primary"]:hover {
  background: #1d4ed8;
}

QPushButton[variant="primary"]:pressed {
  background: #1e40af;
}

/* 次级按钮 — 透明背景，细边框 */
QPushButton[variant="secondary"] {
  background: transparent;
  color: #374151;
  border: 1px solid #d1d5db;
}

QPushButton[variant="secondary"]:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

/* 危险按钮 — 透明背景，红色文字 */
QPushButton[variant="danger"] {
  background: transparent;
  color: #dc2626;
  border: 1px solid #fecaca;
}

QPushButton[variant="danger"]:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}

QPushButton:disabled {
  background: #f3f4f6;
  color: #d1d5db;
  border: none;
}

/* Tab — 无边框，下划线指示器 */
QTabWidget::pane {
  border: none;
  background: transparent;
  padding: 10px 0px;
}

QTabBar::tab {
  background: transparent;
  color: #6b7280;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 8px 16px;
  margin-right: 6px;
  font-weight: 500;
}

QTabBar::tab:selected {
  color: #1d4ed8;
  border-bottom: 2px solid #2563eb;
}

QTabBar::tab:hover:!selected {
  color: #374151;
}

/* 输入框 */
QLineEdit {
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: #111827;
}

QLineEdit:focus {
  border-color: #2563eb;
}

/* 状态栏 */
QStatusBar#statusBar {
  background: #f0f2f5;
  color: #6b7280;
}

/* ===== 终端区域 — 暗色主题 ===== */

/* 终端 Tab 控件容器 */
QTabWidget#terminalTabs::pane {
  border: none;
  background: #1e1e1e;
  border-radius: 0px 0px 8px 8px;
}

QTabWidget#terminalTabs QTabBar::tab {
  background: #2d2d2d;
  color: #9ca3af;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 6px 14px;
  margin-right: 2px;
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
  font-size: 12px;
  font-weight: 400;
}

QTabWidget#terminalTabs QTabBar::tab:selected {
  color: #e5e7eb;
  background: #1e1e1e;
  border-bottom: 2px solid #2563eb;
}

QTabWidget#terminalTabs QTabBar::tab:hover:!selected {
  color: #d1d5db;
  background: #3a3a3a;
}

/* 终端输出区 */
QPlainTextEdit#terminalOutput {
  background: #1e1e1e;
  color: #d4d4d4;
  border: none;
  border-radius: 6px;
  selection-background: #264f78;
  font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
  font-size: 13px;
  padding: 8px;
}
"""
