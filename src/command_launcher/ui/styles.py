"""Application stylesheet."""

LIGHT_STYLESHEET = """
QMainWindow {
  background: #f6f7f9;
}
QListWidget, QFrame, QGroupBox {
  background: #ffffff;
  border: 1px solid #d9dde4;
  border-radius: 8px;
}
QPushButton {
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  font-weight: 600;
}
QPushButton:disabled {
  background: #cbd5e1;
  color: #64748b;
}
QPushButton:hover {
  background: #1d4ed8;
}
QLineEdit {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 8px;
}
QLabel {
  color: #111827;
}
"""
