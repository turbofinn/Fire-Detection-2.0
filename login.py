from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QMessageBox,
    QGridLayout, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QImage, QRegularExpressionValidator
from PyQt5.QtCore import Qt, QTimer, QRegularExpression, QSize, QEvent, QDateTime, QThread, pyqtSignal, pyqtSlot
import json
import traceback
import sys
import os
import time
import subprocess # Still needed for launching external processes if any, but not for homepage now
import multiprocessing as mp

# Import the FireDetectionApp from the new separate module
# Assuming 'TEST2.py' is the file name for the new module
from dashboard import FireDetectionApp 


# --- Mock API Service (remains the same) ---
class EnvConfig:
    def __init__(self):
        self.BASE_URL = "http://mock-api.example.com/" # Replace with actual API base URL

class ApiService:
    def __init__(self, env_config):
        self.env_config = env_config
        print(f"Mock ApiService initialized with base URL: {self.env_config.BASE_URL}")

    def forgotPassword(self, url, payload):
        print(f"Mock API Call: forgotPassword to {url} with payload {payload}")
        data = json.loads(payload)
        username = data.get("username")
        if username == "admin@algoflow":
            return json.dumps({"status": {"code": 1001, "message": "Password reset link sent to your email (mock)."}})
        else:
            return json.dumps({"status": {"code": 1002, "message": "Username not found (mock)."}})

    def login(self, url, payload):
        print(f"Mock API Call: login to {url} with payload {payload}")
        data = json.loads(payload)
        username = data.get("username")
        password = data.get("password")
        
        if username == "admin@algoflow" and password == "1234":
            return json.dumps({"status": {"code": 1001, "message": "Login successful (mock)"}})
        else:
            return json.dumps({"status": {"code": 1002, "message": "Invalid username or password (mock)"}})


# ============================= VIDEO PROCESSING FUNCTION (Adapted for PyQt context) =============================
# This function is now part of the separate homepage module, so it's removed from here.


# ============================= FIRE DETECTION APP (PyQt5 Homepage) =============================
# This class is now part of the separate homepage module, so it's removed from here.


# ============================= LOGIN UI CLASS (remains the same) =============================
def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class FireDetectionUI(QWidget):
    def __init__(self):
        super().__init__()
        # Basic window setup
        self.setWindowTitle("Fire Detection System Login") # Updated title for login window
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry.width() // 4, screen_geometry.height() // 4, 1000, 700)
        
        # Set window icon
        # Ensure 'logo.png' is in the same directory as the script, or provide a full path.
        # For 'parkkey.ico' used in __main__, ensure it's in an 'assets' folder relative to the script.
        icon_path = resource_path("logo.png") 
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Window icon not found at {icon_path}")

        # Initialize API service
        env_config = EnvConfig()
        self.api_service = ApiService(env_config)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel - White background with logo and tagline
        self.left_panel = QFrame() # Make left_panel an instance variable for resizeEvent
        self.left_panel.setStyleSheet("background-color: white; border-top-left-radius: 20px; border-bottom-left-radius: 20px;")
                                 
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setAlignment(Qt.AlignCenter)
        left_layout.setContentsMargins(50, 50, 50, 50)
                                
        # --- AlgoFlow AI Logo (Image in place of text) ---
        self.logo_label = QLabel()
        logo_image_path = resource_path("logo.png") 
        if os.path.exists(logo_image_path):
            self.original_logo_pixmap = QPixmap(logo_image_path)
            # Initial scale for logo - will be adjusted by resizeEvent later
            scaled_pixmap = self.original_logo_pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            print(f"Warning: Logo file not found at {logo_image_path}. Using text fallback.")
            self.logo_label.setText("AlgoFlow AI Logo Missing") # Fallback text
            self.logo_label.setFont(QFont("Arial", 20, QFont.Bold))
            self.logo_label.setStyleSheet("color: #153e62;") # Styling for fallback text
        
        self.logo_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)

        # --- AlgoFlow AI Tagline ---
        self.tagline_label = QLabel("Reliable Detection. Unwavering Security")
        # Enhanced font and size for tagline - Changed SemiBold to DemiBold
        self.tagline_label.setFont(QFont("Segoe UI", 16, QFont.DemiBold)) 
        self.tagline_label.setStyleSheet("color: #333333; margin-top: 10px;") # Added margin for spacing
        self.tagline_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.tagline_label, alignment=Qt.AlignCenter)

        left_layout.addStretch()
        left_layout.addStretch()

        # Right panel - Deep blue background with form
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            background-color: #153e62;
            border-top-right-radius: 20px;
            border-bottom-right-radius: 20px;
        """)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.setSpacing(0)

        # Create a centered container for the login form
        login_container = QWidget()
        login_layout = QVBoxLayout(login_container)
        login_layout.setContentsMargins(30, 30, 30, 30)
        login_layout.setAlignment(Qt.AlignCenter)
        login_layout.setSpacing(10)

        # Login Dashboard header
        self.login_header = QLabel("Login Dashboard") # Made self.login_header to access in resizeEvent
        self.login_header.setObjectName("login_dashboard_header") # Set object name for findChild
        self.login_header.setFont(QFont("Arial", 28, QFont.Bold))
        self.login_header.setAlignment(Qt.AlignLeft)
        self.login_header.setStyleSheet("color: white; margin-bottom: 20px;")
        login_layout.addWidget(self.login_header, alignment=Qt.AlignCenter)
        login_layout.addSpacing(20)

        # Username Input Field
        self.username_input = QLineEdit()
        # Removed initial setFixedSize, will be set by resizeEvent
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFont(QFont("Arial", 12))
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #D0D0D0;
                border-radius: 25px;
                padding: 10px 20px;
                color: #333333;
                selection-background-color: #153e62;
                selection-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #153e62;
                outline: none;
            }
        """)
        login_layout.addWidget(self.username_input, alignment=Qt.AlignCenter)
        login_layout.addSpacing(20)

        # Password Input Field
        self.password_input = QLineEdit()
        # Removed initial setFixedSize, will be set by resizeEvent
        self.password_input.setPlaceholderText("Password")
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #D0D0D0;
                border-radius: 25px;
                padding: 10px 20px;
                color: #333333;
                selection-background-color: #153e62;
                selection-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #153e62;
                outline: none;
            }
        """)
        login_layout.addWidget(self.password_input, alignment=Qt.AlignCenter)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(30)
        login_layout.addWidget(self.status_label)

        # Login Button
        self.login_button = QPushButton("Login")
        self.login_button.setFixedSize(180, 60)
        self.login_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #3082BE;
                color: white;
                border-radius: 30px;
                padding: 10px 20px;
                outline: none;
                border: 1px solid #153e62;
            }}
            QPushButton:hover {{
                background-color: #2a73a8;
            }}
            QPushButton:pressed {{
                background-color: #256491;
            }}
            QPushButton:disabled {{
                background-color: #99BBDD;
                color: #e0e0e0;
                border: 1px solid #AABBCC;
            }}
            QPushButton:focus {{
                outline: none;
                border: 1px solid #153e62;
            }}
        """)
        self.login_button.setFocusPolicy(Qt.NoFocus)
        self.login_button.clicked.connect(self.validate_credentials)
        login_layout.addWidget(self.login_button, alignment=Qt.AlignCenter)
        login_layout.addSpacing(20)

        # Horizontal line
        self.line_frame = QFrame() # Made self.line_frame to access in resizeEvent
        self.line_frame.setObjectName("login_separator_line") # Set object name for findChild
        self.line_frame.setFrameShape(QFrame.HLine)
        self.line_frame.setFrameShadow(QFrame.Sunken)
        self.line_frame.setStyleSheet("background-color: #CCCCCC;")
        self.line_frame.setFixedHeight(2)
        self.line_frame.setFixedWidth(350)
        login_layout.addWidget(self.line_frame, alignment=Qt.AlignCenter)
        login_layout.addSpacing(10)

        # "Forgot Password?" Link
        self.forgot_password_label = QLabel("Forgot Password?")
        self.forgot_password_label.setFont(QFont("Arial", 12))
        self.forgot_password_label.setStyleSheet("color: white; text-decoration: none;")
        self.forgot_password_label.setCursor(Qt.PointingHandCursor)
        self.forgot_password_label.setAlignment(Qt.AlignCenter)
        self.forgot_password_label.mousePressEvent = self.forgot_password_clicked
        login_layout.addWidget(self.forgot_password_label, alignment=Qt.AlignCenter)
        login_layout.addSpacing(20)

        # Add login container to right panel
        right_layout.addWidget(login_container, alignment=Qt.AlignCenter)

        # Add panels to main layout
        main_layout.addWidget(self.left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # Set the final layout
        container = QWidget()
        container.setLayout(main_layout)
        container.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border-radius: 20px;
            }}
        """)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.addWidget(container)
        self.setStyleSheet("background-color: #E6F2F7;")
        
        self.username_input.setFocus()
        
    def _apply_initial_style_fix(self):
        """Forces layout update and style re-application for correct initial rendering."""
        # Force a geometry update to ensure widgets have their final sizes
        self.updateGeometry() 
        # Re-apply the style to ensure all CSS properties are correctly rendered
        QApplication.instance().style().polish(self)
        # Also force a repaint as a last resort
        self.repaint()

    def showEvent(self, event: QEvent):
        """Override showEvent to trigger a repaint after the window is shown."""
        super().showEvent(event)
        # No explicit call to repaint here, as it's now handled by QTimer.singleShot in __main__


    def resizeEvent(self, event: QEvent):
        """Handle window resize events to proportionally scale the logo and adjust layout."""
        super().resizeEvent(event)
        
        if hasattr(self, 'original_logo_pixmap') and self.left_panel.width() > 0 and self.left_panel.height() > 0:
            # Calculate the available space for the logo within the left panel's content margins
            panel_width = self.left_panel.width() - (self.left_panel.layout().contentsMargins().left() + self.left_panel.layout().contentsMargins().right())
            panel_height = self.left_panel.height() - (self.left_panel.layout().contentsMargins().top() + self.left_panel.layout().contentsMargins().bottom())
            
            if panel_width > 0 and panel_height > 0:
                # Target the logo to fit within 70% of the panel's smaller dimension for better responsiveness
                # This ensures there's always some padding and the logo doesn't become too large or too small.
                target_size = min(panel_width, panel_height) * 0.7 
                
                scaled_pixmap = self.original_logo_pixmap.scaled(
                    int(target_size), 
                    int(target_size),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.logo_label.setPixmap(scaled_pixmap)
                self.logo_label.setAlignment(Qt.AlignCenter)

        # Adjust font sizes for responsiveness based on window height
        current_height = self.height()
        
        # Scale header font size
        header_font_size = max(18, min(28, int(current_height / 25))) # Min 18, Max 28
        self.login_header.setFont(QFont("Arial", header_font_size, QFont.Bold))

        # Scale input field font size
        input_font_size = max(10, min(14, int(current_height / 50))) # Min 10, Max 14
        self.username_input.setFont(QFont("Arial", input_font_size))
        self.password_input.setFont(QFont("Arial", input_font_size))

        # Scale status label font size
        status_font_size = max(9, min(12, int(current_height / 60))) # Min 9, Max 12
        self.status_label.setFont(QFont("Arial", status_font_size))

        # Scale button font size
        button_font_size = max(12, min(16, int(current_height / 40))) # Min 12, Max 16
        self.login_button.setFont(QFont("Arial", button_font_size, QFont.Bold))

        # Scale forgot password link font size
        forgot_password_font_size = max(9, min(12, int(current_height / 60))) # Min 9, Max 12
        self.forgot_password_label.setFont(QFont("Arial", forgot_password_font_size))

        # Adjust input field fixed sizes based on window width
        current_width = self.width()
        input_width = max(250, min(400, int(current_width * 0.35))) # Adjust width based on overall window width
        input_height = max(40, min(60, int(current_height * 0.07))) # Adjust height based on overall window height
        self.username_input.setFixedSize(input_width, input_height)
        self.password_input.setFixedSize(input_width, input_height)
        self.line_frame.setFixedWidth(input_width) # Adjust line width

        # Adjust button fixed size
        button_width = max(150, min(200, int(current_width * 0.2)))
        button_height = max(50, min(70, int(current_height * 0.1)))
        self.login_button.setFixedSize(button_width, button_height)


    def forgot_password_clicked(self, event):
        """Handle Forgot Password link click - now performs an API call for password reset"""
        username = self.username_input.text().strip()
        if not username or username == self.username_input.placeholderText():
            self.status_label.setText("Please enter your username to reset password.")
            self.status_label.setStyleSheet("color: #FF6666;")
            return

        self.status_label.setText("Sending password reset link...")
        self.status_label.setStyleSheet("color: white;")
        
        QTimer.singleShot(1000, lambda: self._complete_forgot_password(username))

    def _complete_forgot_password(self, username):
        try:
            url = "login-service/forgot-password"
            payload = json.dumps({"username": username})
            response = self.api_service.forgotPassword(url, payload)

            if response:
                response_data = json.loads(response)
                if response_data.get("status", {}).get("code") == 1001:
                    self.status_label.setText(response_data.get("status", {}).get("message", "Password reset link sent!"))
                    self.status_label.setStyleSheet("color: white;")
                else:
                    self.status_label.setText(response_data.get("status", {}).get("message", "Failed to send reset link."))
                    self.status_label.setStyleSheet("color: #FF6666;")
            else:
                self.status_label.setText("Failed to process request. Please try again.")
                self.status_label.setStyleSheet("color: #FF6666;")
        except Exception as e:
            self.status_label.setText("Error processing request.")
            self.status_label.setStyleSheet("color: #FF6666;")
            print(f"Forgot password error: {str(e)}")


    def validate_credentials(self):
        """Validate username/password and login the user"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username:
            self.status_label.setText("Please enter your username.")
            self.status_label.setStyleSheet("color: #FF6666;")
            return

        if not password:
            self.status_label.setText("Please enter your password.")
            self.status_label.setStyleSheet("color: #FF6666;")
            return

        # Show login in progress
        original_text = self.login_button.text()
        self.login_button.setText("Logging in...")
        self.login_button.setEnabled(False)
        
        QTimer.singleShot(1000, lambda: self.complete_validation(username, password, original_text))

    def complete_validation(self, username, password, original_button_text):
        """Complete the validation process after API call"""
        try:
            # Reset button
            self.login_button.setText(original_button_text)
            self.login_button.setEnabled(True)
            
            url = "login-service/authenticate"
            payload = json.dumps({"username": username, "password": password})
            response = self.api_service.login(url, payload)

            if response:
                try:
                    response_data = json.loads(response)
                    if response_data.get("status", {}).get("code") == 1001:
                        self.status_label.setText("Login successful! Redirecting Please Wait.....")
                        self.status_label.setStyleSheet("color: white;")
                        
                        QTimer.singleShot(1000, self.open_main_window)
                    else:
                        error_message = response_data.get("status", {}).get("message", "Invalid username or password.")
                        self.status_label.setText(error_message)
                        self.status_label.setStyleSheet("color: #FF6666;")
                except json.JSONDecodeError:
                    self.status_label.setText("Invalid response from server.")
                    self.status_label.setStyleSheet("color: #FF6666;")
            else:
                self.status_label.setText("Login failed. Please try again.")
                self.status_label.setStyleSheet("color: #FF6666;")
                
        except Exception as e:
            self.status_label.setText("An error occurred. Please try again.")
            self.status_label.setStyleSheet("color: #FF6666;")
            print(f"Login error: {str(e)}")
            print(traceback.format_exc())

    def open_main_window(self):
        """Open the main application window (now the PyQt5 FireDetectionApp)"""
        try:
            self.main_app_window = FireDetectionApp() # Instantiate the PyQt5 homepage
            if self.isMaximized():
                self.main_app_window.showMaximized()
            else:
                self.main_app_window.show()
            self.close() # Close the login window
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading main application: {str(e)}")
            print(f"Error opening main window: {str(e)}")
            print(traceback.format_exc())

def exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler to prevent application termination"""
    print("An error occurred:", exc_value)
    traceback.print_exc(exc_type, exc_value, exc_traceback)

if __name__ == "__main__":
    # It is crucial to set the start method for multiprocessing BEFORE QApplication is created
    # and before any multiprocessing.Process objects are created.
    # 'spawn' is generally safer for PyQt applications, especially on Windows.
    mp.set_start_method('spawn', force=True)
    
    sys.excepthook = exception_hook
    
    app = QApplication([])
    
    icon_path = resource_path("assets/parkkey.ico") # Assuming 'assets' folder for app icon
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"Warning: Application icon not found at {icon_path}")

    window = FireDetectionUI()
    window.show()
    # Schedule a call to a custom function that forces layout update and style polish
    QTimer.singleShot(0, lambda: window._apply_initial_style_fix())
    sys.exit(app.exec_())
