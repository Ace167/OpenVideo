"""Theme definitions and modern Windows 11 styling stylesheets."""

import sys

from PySide6.QtGui import QGuiApplication, QPalette


def detect_system_dark_mode() -> bool:
    """Detect whether Windows or the operating system is currently set to dark theme."""
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return bool(value == 0)
        except Exception:
            pass

    # Fallback using Qt's application palette luminance
    app = QGuiApplication.instance()
    if isinstance(app, QGuiApplication):
        palette = app.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        # Luminance heuristic: if background is dark, use dark theme
        return bool(window_color.value() < 128)

    return False


LIGHT_STYLESHEET = """
/* Light Theme - Modern Windows 11 Clean Styling */
QMainWindow, QDialog {
    background-color: #f8f9fa;
}

QWidget {
    color: #1a1a1a;
}

QLabel {
    background: transparent;
}

/* Sidebar / Navigation Rail */
#navRail {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

#navHeaderTitle {
    font-size: 15px;
    font-weight: 700;
    color: #111827;
}

#navHeaderSubtitle {
    font-size: 11px;
    color: #6b7280;
}

QPushButton.navBtn {
    text-align: left;
    padding: 10px 14px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #374151;
    background-color: transparent;
}

QPushButton.navBtn:hover {
    background-color: #f3f4f6;
    color: #111827;
}

QPushButton.navBtn:checked, QPushButton.navBtn.active {
    background-color: #e0f2fe;
    color: #0369a1;
    font-weight: 600;
}

/* Card Containers */
QFrame.card, QFrame[class="card"] {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
}

/* Input Fields */
QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    color: #111827;
    selection-background-color: #0284c7;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #0284c7;
}

/* Primary Action Buttons */
QPushButton.btnPrimary {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    padding: 9px 18px;
    border: none;
    border-radius: 6px;
}

QPushButton.btnPrimary:hover {
    background-color: #0369a1;
}

QPushButton.btnPrimary:pressed {
    background-color: #075985;
}

QPushButton.btnPrimary:disabled {
    background-color: #94a3b8;
    color: #e2e8f0;
}

/* Secondary Buttons */
QPushButton.btnSecondary {
    background-color: #ffffff;
    color: #374151;
    font-weight: 500;
    padding: 8px 14px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
}

QPushButton.btnSecondary:hover {
    background-color: #f9fafb;
    border-color: #9ca3af;
}

QPushButton.btnSecondary:pressed {
    background-color: #f3f4f6;
}

/* Status Bar */
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #e5e7eb;
    color: #6b7280;
    font-size: 11px;
    padding: 4px 10px;
}

/* Headings and labels */
QLabel.pageTitle {
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
}

QLabel.pageSubtitle {
    font-size: 13px;
    color: #64748b;
}

QLabel.emptyStateTitle {
    font-size: 16px;
    font-weight: 600;
    color: #334155;
}

QLabel.emptyStateText {
    font-size: 13px;
    color: #64748b;
}

/* Form section labels */
QLabel.sectionHeader {
    font-size: 14px;
    font-weight: 600;
    color: #0f172a;
}

QCheckBox {
    spacing: 8px;
    color: #1f2937;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #9ca3af;
    background-color: #ffffff;
}

/* Scroll Area & Scrollbars */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0px;
    border: none;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    width: 0px;
    border: none;
}

/* Tooltips */
QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 5px 9px;
    font-size: 11px;
}

/* Nav Rail Toggle & Compact Mode */
QPushButton#navToggleBtn {
    border: none;
    background-color: transparent;
    border-radius: 5px;
    padding: 4px;
    color: #4b5563;
}

QPushButton#navToggleBtn:hover {
    background-color: #f3f4f6;
    color: #111827;
}

QPushButton.navBtnCompact {
    text-align: center;
    padding: 9px 0px;
    border: none;
    border-radius: 6px;
    background-color: transparent;
}

QPushButton.navBtnCompact:hover {
    background-color: #f3f4f6;
}

QPushButton.navBtnCompact:checked {
    background-color: #e0f2fe;
}

/* Typography & Utility Classes */
QLabel[class="cardTitle"], .cardTitle {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}

QLabel[class="metaLabel"], .metaLabel {
    color: #475569;
    font-size: 12px;
}

QLabel[class="dimText"], .dimText {
    color: #64748b;
    font-size: 11px;
}

QLabel[class="diagLabel"], .diagLabel {
    color: #64748b;
    font-weight: 500;
}

QLabel[class="diagValue"], .diagValue {
    color: #1e293b;
    font-weight: 600;
}

QLabel[class="infoNotice"], .infoNotice {
    background-color: rgba(2, 132, 199, 0.08);
    border: 1px solid rgba(2, 132, 199, 0.25);
    border-radius: 6px;
    padding: 10px;
    font-size: 12px;
    color: #334155;
}

QLabel[class="errorBanner"], .errorBanner {
    color: #b91c1c;
    background-color: #fef2f2;
    border: 1px solid #fee2e2;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""

DARK_STYLESHEET = """
/* Dark Theme - Modern Windows 11 Sleek Dark Styling */
QMainWindow, QDialog {
    background-color: #18181b;
}

QWidget {
    color: #f4f4f5;
}

QLabel {
    background: transparent;
}

/* Sidebar / Navigation Rail */
#navRail {
    background-color: #202023;
    border-right: 1px solid #2e2e33;
}

#navHeaderTitle {
    font-size: 15px;
    font-weight: 700;
    color: #fafafa;
}

#navHeaderSubtitle {
    font-size: 11px;
    color: #a1a1aa;
}

QPushButton.navBtn {
    text-align: left;
    padding: 10px 14px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #d4d4d8;
    background-color: transparent;
}

QPushButton.navBtn:hover {
    background-color: #27272a;
    color: #ffffff;
}

QPushButton.navBtn:checked, QPushButton.navBtn.active {
    background-color: #0c4a6e;
    color: #38bdf8;
    font-weight: 600;
}

/* Card Containers */
QFrame.card, QFrame[class="card"] {
    background-color: #242427;
    border: 1px solid #323238;
    border-radius: 8px;
    padding: 16px;
}

/* Input Fields */
QLineEdit, QComboBox, QSpinBox {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f4f4f5;
    selection-background-color: #38bdf8;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #38bdf8;
}

/* Primary Action Buttons */
QPushButton.btnPrimary {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    padding: 9px 18px;
    border: none;
    border-radius: 6px;
}

QPushButton.btnPrimary:hover {
    background-color: #38bdf8;
    color: #09090b;
}

QPushButton.btnPrimary:pressed {
    background-color: #0ea5e9;
    color: #09090b;
}

QPushButton.btnPrimary:disabled {
    background-color: #3f3f46;
    color: #71717a;
}

/* Secondary Buttons */
QPushButton.btnSecondary {
    background-color: #27272a;
    color: #e4e4e7;
    font-weight: 500;
    padding: 8px 14px;
    border: 1px solid #3f3f46;
    border-radius: 6px;
}

QPushButton.btnSecondary:hover {
    background-color: #323236;
    border-color: #52525b;
}

QPushButton.btnSecondary:pressed {
    background-color: #3f3f46;
}

/* Status Bar */
QStatusBar {
    background-color: #1e1e21;
    border-top: 1px solid #2e2e33;
    color: #a1a1aa;
    font-size: 11px;
    padding: 4px 10px;
}

/* Headings and labels */
QLabel.pageTitle {
    font-size: 20px;
    font-weight: 700;
    color: #f8fafc;
}

QLabel.pageSubtitle {
    font-size: 13px;
    color: #94a3b8;
}

QLabel.emptyStateTitle {
    font-size: 16px;
    font-weight: 600;
    color: #e2e8f0;
}

QLabel.emptyStateText {
    font-size: 13px;
    color: #94a3b8;
}

/* Form section labels */
QLabel.sectionHeader {
    font-size: 14px;
    font-weight: 600;
    color: #f8fafc;
}

QCheckBox {
    spacing: 8px;
    color: #e4e4e7;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #52525b;
    background-color: #27272a;
}

QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}

/* Scroll Area & Scrollbars */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #3f3f46;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #52525b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0px;
    border: none;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #3f3f46;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #52525b;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    width: 0px;
    border: none;
}

/* Tooltips */
QToolTip {
    background-color: #27272a;
    color: #f4f4f5;
    border: 1px solid #3f3f46;
    border-radius: 5px;
    padding: 5px 9px;
    font-size: 11px;
}

/* Nav Rail Toggle & Compact Mode */
QPushButton#navToggleBtn {
    border: none;
    background-color: transparent;
    border-radius: 5px;
    padding: 4px;
    color: #a1a1aa;
}

QPushButton#navToggleBtn:hover {
    background-color: #27272a;
    color: #ffffff;
}

QPushButton.navBtnCompact {
    text-align: center;
    padding: 9px 0px;
    border: none;
    border-radius: 6px;
    background-color: transparent;
}

QPushButton.navBtnCompact:hover {
    background-color: #27272a;
}

QPushButton.navBtnCompact:checked {
    background-color: #0c4a6e;
}

/* Typography & Utility Classes */
QLabel[class="cardTitle"], .cardTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f4f4f5;
}

QLabel[class="metaLabel"], .metaLabel {
    color: #94a3b8;
    font-size: 12px;
}

QLabel[class="dimText"], .dimText {
    color: #64748b;
    font-size: 11px;
}

QLabel[class="diagLabel"], .diagLabel {
    color: #94a3b8;
    font-weight: 500;
}

QLabel[class="diagValue"], .diagValue {
    color: #f8fafc;
    font-weight: 600;
}

QLabel[class="infoNotice"], .infoNotice {
    background-color: rgba(2, 132, 199, 0.15);
    border: 1px solid rgba(2, 132, 199, 0.35);
    border-radius: 6px;
    padding: 10px;
    font-size: 12px;
    color: #e0f2fe;
}

QLabel[class="errorBanner"], .errorBanner {
    color: #fca5a5;
    background-color: #2d1215;
    border: 1px solid #4c1d24;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""


def get_theme_stylesheet(theme_name: str) -> str:
    """Return the complete Qt style sheet for the requested theme ('system', 'dark', 'light')."""
    theme_clean = theme_name.lower().strip()
    if theme_clean == "system":
        is_dark = detect_system_dark_mode()
        return DARK_STYLESHEET if is_dark else LIGHT_STYLESHEET
    if theme_clean == "dark":
        return DARK_STYLESHEET
    return LIGHT_STYLESHEET
