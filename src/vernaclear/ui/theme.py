APP_STYLE = r"""
* {
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #E8EBF2;
}
QMainWindow, QDialog, QWidget#Root {
    background: #0E1118;
}
QFrame#Header, QFrame#Panel, QFrame#StatusCard {
    background: #171B25;
    border: 1px solid #262C3A;
    border-radius: 16px;
}
QLabel#Brand {
    font-size: 24px;
    font-weight: 700;
    color: #FFFFFF;
}
QLabel#Subtitle, QLabel#Muted, QLabel#ProviderLabel {
    color: #929BAC;
}
QLabel#SectionTitle {
    font-size: 16px;
    font-weight: 650;
    color: #FFFFFF;
}
QPushButton {
    background: #232938;
    border: 1px solid #333B4D;
    border-radius: 9px;
    padding: 8px 14px;
    min-height: 20px;
}
QPushButton:hover { background: #2C3446; border-color: #48536A; }
QPushButton:pressed { background: #1D2230; }
QPushButton:disabled { color: #687083; background: #1B202B; }
QPushButton#Primary {
    background: #7167F5;
    border-color: #8B83FF;
    color: white;
    font-weight: 650;
    padding-left: 24px;
    padding-right: 24px;
}
QPushButton#Primary:hover { background: #8077FA; }
QPushButton#Danger { color: #FF9DAB; }
QTextEdit, QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #10141D;
    border: 1px solid #303748;
    border-radius: 9px;
    padding: 8px;
    selection-background-color: #6259DB;
}
QTextEdit:focus, QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border-color: #766DF5;
}
QComboBox { min-width: 120px; }
QComboBox::drop-down { border: 0; width: 24px; }
QComboBox QAbstractItemView {
    background: #171B25;
    border: 1px solid #303748;
    selection-background-color: #6259DB;
}
QListWidget, QTableWidget {
    background: #10141D;
    border: 1px solid #303748;
    border-radius: 9px;
    alternate-background-color: #151A24;
    gridline-color: #272E3D;
}
QListWidget::item { padding: 8px; border-bottom: 1px solid #232938; }
QHeaderView::section {
    background: #202635;
    border: 0;
    border-right: 1px solid #303748;
    padding: 8px;
    font-weight: 600;
}
QTabWidget::pane { border: 1px solid #303748; border-radius: 8px; }
QTabBar::tab { background: #171B25; padding: 9px 16px; }
QTabBar::tab:selected { background: #6259DB; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #3B4355; border-radius: 5px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QStatusBar { color: #929BAC; background: #0E1118; }
QToolTip { background: #252C3B; color: white; border: 1px solid #4A546A; padding: 5px; }
"""

