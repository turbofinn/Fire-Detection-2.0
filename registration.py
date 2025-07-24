import sys
import qtawesome as qta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox, QGraphicsDropShadowEffect, 
)
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize

# --- MODIFIED: Import the database function ---
from database_utils import add_user_to_db


# Note: These attributes should ideally be set only once in your main application's entry point.
if not QApplication.instance():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class FinalRegistrationForm(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("User Registration")
        self.setMinimumSize(1000, 720)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. Left Panel (For Image) ---
        self.left_panel = QFrame()
        self.left_panel.setObjectName("imagePanel")
        self.left_panel.setStyleSheet("#imagePanel { background-color: #2c3e50; }")
        left_panel_layout = QVBoxLayout(self.left_panel)
        left_panel_layout.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel()
        image_path = "D:/tkinter/logo.png" # Make sure this path is correct
        self.image_pixmap = QPixmap(image_path)

        if self.image_pixmap.isNull():
            self.image_label.setText(f"Image not found:\n{image_path}")
            self.image_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.image_label.setStyleSheet("color: #ff4d4d;")
        else:
            self.image_label.setPixmap(self.image_pixmap)
        
        left_panel_layout.addWidget(self.image_label)

        # --- 2. Right Panel (For Form) ---
        self.right_panel = QFrame()
        self.right_panel.setObjectName("formPanel")
        self.right_panel.setStyleSheet("#formPanel { background-color: #f0f2f5; }")
        
        right_panel_layout = QHBoxLayout(self.right_panel)
        right_panel_layout.setAlignment(Qt.AlignCenter)
        right_panel_layout.setContentsMargins(20, 20, 20, 20)
        
        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setFixedWidth(700)
        self.card.setStyleSheet("#card { background-color: #ffffff; border-radius: 12px; }")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(20)

        icon_label = QLabel()
        icon = qta.icon('fa5s.user-plus', color='#005cbf')
        icon_label.setPixmap(icon.pixmap(QSize(64, 64)))
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Register New User")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        card_layout.addWidget(icon_label)
        card_layout.addWidget(title_label)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(18)
        
        self.username_field = self.create_input_field("fa5s.user", "Enter username")
        self.email_field = self.create_input_field("fa5s.envelope", "Enter email")
        self.password_field = self.create_input_field("fa5s.lock", "Enter password", True)
        self.confirm_password_field = self.create_input_field("fa5s.check-circle", "Confirm password", True)
        self.mobile_field = self.create_input_field("fa5s.phone", "Enter mobile number")
        self.designation_field = self.create_input_field("fa5s.id-badge", "e.g., Security Chief")
        self.department_field = self.create_input_field("fa5s.building", "e.g., Safety Dept.")
        self.location_field = self.create_input_field("fa5s.map-marker-alt", "e.g., Warehouse A")
        
        self.fields_data = {
            'left': [("Username", self.username_field), ("Email Address", self.email_field), ("Password", self.password_field), ("Confirm Password", self.confirm_password_field)],
            'right': [("Mobile Number", self.mobile_field), ("Designation", self.designation_field), ("Department", self.department_field), ("Place/Location", self.location_field)]
        }
        card_layout.addLayout(self.grid_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        self.cancel_button, self.register_button = QPushButton("Cancel"), QPushButton("Register")
        button_style = "QPushButton { font-size: 14px; font-weight: bold; padding: 14px 35px; border-radius: 8px; border: none; } QPushButton#cancel { background-color: #dc3545; color: white; } QPushButton#cancel:hover { background-color: #c82333; } QPushButton#register { background-color: #007bff; color: white; } QPushButton#register:hover { background-color: #0069d9; }"
        self.cancel_button.setObjectName("cancel"); self.register_button.setObjectName("register")
        self.cancel_button.setStyleSheet(button_style); self.register_button.setStyleSheet(button_style)
        button_layout.addStretch(); button_layout.addWidget(self.cancel_button); button_layout.addWidget(self.register_button)
        card_layout.addLayout(button_layout)
        
        right_panel_layout.addWidget(self.card)

        main_layout.addWidget(self.left_panel, 2)
        main_layout.addWidget(self.right_panel, 3)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.is_single_column = None
        self.update_layout(self.right_panel.width())

        self.cancel_button.clicked.connect(self.close)
        self.register_button.clicked.connect(self.register_user)

    def update_layout(self, width):
        threshold = 550
        new_layout_is_single = (width < threshold)
        if self.is_single_column == new_layout_is_single: return
        self.is_single_column = new_layout_is_single
        
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.setParent(None)
        
        if self.is_single_column:
            all_fields = self.fields_data['left'] + self.fields_data['right']
            for i, (labelText, fieldWidget) in enumerate(all_fields):
                label = self.create_label(labelText)
                self.grid_layout.addWidget(label, i * 2, 0, 1, 2)
                self.grid_layout.addWidget(fieldWidget, i * 2 + 1, 0, 1, 2)
        else:
            for i, (labelText, fieldWidget) in enumerate(self.fields_data['left']):
                label = self.create_label(labelText)
                self.grid_layout.addWidget(label, i * 2, 0)
                self.grid_layout.addWidget(fieldWidget, i * 2 + 1, 0)
            for i, (labelText, fieldWidget) in enumerate(self.fields_data['right']):
                label = self.create_label(labelText)
                self.grid_layout.addWidget(label, i * 2, 1)
                self.grid_layout.addWidget(fieldWidget, i * 2 + 1, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_layout(self.card.width())
        if not self.image_pixmap.isNull():
            self.image_label.setPixmap(self.image_pixmap.scaled(
                self.left_panel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def create_label(self, text):
        label = QLabel(text); label.setFont(QFont("Segoe UI", 10, QFont.Bold)); label.setStyleSheet("color: #555;")
        return label

    def create_input_field(self, icon_name, placeholder, is_password=False):
        field = QLineEdit(); field.setFont(QFont("Segoe UI", 11)); field.setPlaceholderText(placeholder)
        field.setMinimumHeight(40); field.setStyleSheet("QLineEdit { border: 1px solid #d0d0d0; border-radius: 8px; background-color: #fdfdfd; color: #333; padding-left: 40px; } QLineEdit:focus { border: 2px solid #007bff; }")
        if is_password: field.setEchoMode(QLineEdit.Password)
        icon = qta.icon(icon_name, color='#888'); field.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)
        return field
        
    # --- MODIFIED: This function now saves to the database ---
    def register_user(self):
        password = self.password_field.text()
        confirm_password = self.confirm_password_field.text()

        user_data = {
            "username": self.username_field.text(),
            "email": self.email_field.text(),
            "password": password,
            "phone_number": self.mobile_field.text(),
            "designation": self.designation_field.text(),
            "department": self.department_field.text(),
            "place": self.location_field.text(),
            "role": "Operator" 
        }
        
        if not all([user_data["username"], user_data["email"], user_data["password"]]):
            QMessageBox.warning(self, "Input Error", "Username, Email, and Password are required.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password Error", "The passwords do not match. Please try again.")
            return

        try:
            add_user_to_db(user_data)
            QMessageBox.information(self, "Success", f"User '{user_data['username']}' has been registered successfully!")
            
            # Clear all form fields
            self.username_field.clear()
            self.email_field.clear()
            self.password_field.clear()
            self.confirm_password_field.clear()
            self.mobile_field.clear()
            self.designation_field.clear()
            self.department_field.clear()
            self.location_field.clear()

        except ValueError as e:
            QMessageBox.critical(self, "Registration Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinalRegistrationForm()
    window.show()
    sys.exit(app.exec_())