"""Application stylesheet."""

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
