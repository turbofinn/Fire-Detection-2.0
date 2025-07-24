import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QMessageBox, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize

class UserManagementWindow(QMainWindow):
    """
    A window to display and manage users with a fully responsive table.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Management")
        self.setGeometry(100, 100, 1300, 750)

        # --- Main Background Widget ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)

        # --- Card Widget with Shadow ---
        card_widget = QFrame()
        card_widget.setObjectName("card")
        main_layout.addWidget(card_widget)
        main_layout.setContentsMargins(80, 50, 80, 50)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card_widget.setGraphicsEffect(shadow)

        # --- Layout for Card Content ---
        card_layout = QVBoxLayout(card_widget)
        card_layout.setContentsMargins(30, 30, 30, 30)

        # --- Title Label ---
        title_label = QLabel("👥 User Database")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)

        # --- Table Widget ---
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Username", "Email", "Phone", "Designation",
            "Department", "Place", "Role", "Action"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        # **** FINAL RESPONSIVE SOLUTION ****
        header = self.table.horizontalHeader()
        # 1. Set the default mode to Stretch. This makes the table responsive
        #    and ensures it fills the width of the card.
        header.setSectionResizeMode(QHeaderView.Stretch)

        # 2. Set a global minimum size for all sections. This acts as a safety
        #    net to prevent any column from becoming too small when resizing.
        header.setMinimumSectionSize(100)

        # 3. Override specific columns to be compact, ensuring they take up
        #    just the space they need and are always protected.
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents) # Action

        card_layout.addWidget(self.table)

        # --- Load Data and Apply Styles ---
        self.load_data_from_db()
        self.apply_stylesheet()

    def load_data_from_db(self):
        """Fetches user records and populates the table."""
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, phone_number, designation, department, place, role
                FROM users ORDER BY id
            """)
            users = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(users))
            for row_index, user_record in enumerate(users):
                self.table.setRowHeight(row_index, 50)
                for col_index, data in enumerate(user_record):
                    display_text = str(data) if data is not None else "N/A"
                    item = QTableWidgetItem(display_text)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_index, col_index, item)

                user_id = user_record[0]
                self.add_delete_button(row_index, user_id)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Could not load data: {e}")

    def add_delete_button(self, row_index, user_id):
        """Adds a clearly visible delete button to a row."""
        delete_button = QPushButton("Delete")
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.setMinimumSize(90, 32)
        delete_button.clicked.connect(lambda: self.delete_user(row_index, user_id))

        cell_widget = QWidget()
        cell_layout = QVBoxLayout(cell_widget)
        cell_layout.addWidget(delete_button)
        cell_layout.setAlignment(Qt.AlignCenter)
        cell_layout.setContentsMargins(0, 0, 0, 0)

        self.table.setCellWidget(row_index, 8, cell_widget)


    def delete_user(self, row_index, user_id):
        """Deletes a user from the database and the table view."""
        username = self.table.item(row_index, 1).text()
        reply = QMessageBox.warning(
            self, 'Confirm Deletion',
            f"Are you sure you want to permanently delete '{username}' (ID: {user_id})?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                conn.close()
                self.table.removeRow(row_index)
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Could not delete user: {e}")

    def apply_stylesheet(self):
        """Applies the refined light theme stylesheet."""
        self.setStyleSheet("""
            /* Main Window background */
            QMainWindow {
                background-color: #F4F6F8;
                font-family: 'Times New Roman';
            }
            /* The Card containing the table */
            QFrame#card {
                background-color: #FFFFFF;
                border-radius: 10px;
            }
            /* Title Label */
            QLabel#title {
                font-size: 28px;
                font-weight: bold;
                color: #2962FF; /* Vibrant Blue */
                padding-bottom: 20px;
            }
            /* Table Styles */
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                font-size: 16px;
                color: #333333;
            }
            /* Table Header */
            QHeaderView::section {
                background-color: #2962FF;
                padding: 14px;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
            /* Table Rows */
            QTableWidget::item {
                padding-left: 12px;
                border-bottom: 1px solid #EEF0F2;
            }
            QTableWidget::item:selected {
                background-color: #D4E3FF;
                color: #0043A5;
            }
            /* Delete Button - HIGH CONTRAST STYLE */
            QPushButton {
                background-color: #D32F2F; /* Strong Red */
                color: white; /* White Text */
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                border: 1px solid #B21B1B; /* Darker red border */
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #B71C1C;
                border: 1px solid #A01818;
            }
            QPushButton:pressed {
                background-color: #A01818;
            }
            /* ScrollBar */
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: #F4F6F8;
                width: 10px; /* Vertical scrollbar width */
                height: 10px; /* Horizontal scrollbar height */
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #D0D0D0;
                min-height: 20px; /* Vertical handle */
                min-width: 20px; /* Horizontal handle */
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #B0B0B0;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = UserManagementWindow()
    window.show()
    sys.exit(app.exec_())