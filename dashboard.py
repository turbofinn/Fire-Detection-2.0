# ============================= IMPORTING LIBRARIES =============================
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QMainWindow, QMessageBox,
    QSizePolicy, QStackedWidget, QStackedLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QPixmap, QImage, QIcon, QColor
from PyQt5.QtCore import Qt, QTimer, QDateTime, QEvent, QUrl, QSize, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtMultimedia import QSoundEffect

import cv2
import torch
import multiprocessing as mp
from queue import Empty
import supervision as sv
from ultralytics import YOLO
from PIL import Image
import time
import sys
import os
import traceback
import qtawesome as qta

# Import your registration window from registration.py
from registration import FinalRegistrationForm


# ============================= VIDEO PROCESSING FUNCTION (UNCHANGED) =============================
def process_video_feed(cam_index, queue, model_path):
    # This function is unchanged
    try:
        model = YOLO(model_path)
        box_annotator = sv.BoxAnnotator(thickness=2)
        if cam_index == 1: cap = cv2.VideoCapture("rtsp://admin:admin@192.168.1.17:1935", cv2.CAP_FFMPEG)
        else: cap = cv2.VideoCapture(cam_index)
        if not cap.isOpened():
            queue.put((None, False, f"Error: Camera {cam_index+1} not available")); return
        cap.set(cv2.CAP_PROP_FPS, 30); cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        while True:
            ret, frame = cap.read()
            if not ret:
                queue.put((None, False, f"Error: Camera {cam_index+1} disconnected"))
                cap.release(); time.sleep(2)
                if cam_index == 1: cap = cv2.VideoCapture("rtsp://admin:admin@192.168.1.17:1935", cv2.CAP_FFMPEG)
                else: cap = cv2.VideoCapture(cam_index)
                if not cap.isOpened(): break 
                continue
            resized = cv2.resize(frame, (640, 480))
            results = model(resized, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            fire_detected = False; grid_message = ""
            if hasattr(detections, "class_id") and len(detections.class_id) > 0:
                for i in range(len(detections)):
                    if detections.class_id[i] < len(model.names):
                        class_name = model.names[detections.class_id[i]]
                        if class_name.lower() in ['fire', 'smoke', 'bothfireandsmoke']:
                            fire_detected = True
                            x1, y1, x2, y2 = detections.xyxy[i]
                            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                            grid_number = (cy // (480 // 5)) * 5 + (cx // (640 // 5)) + 1
                            grid_message = f"🔥 Zone {cam_index+1}: Fire/Smoke in Grid {grid_number}"
                            break
            annotated_frame = box_annotator.annotate(scene=resized.copy(), detections=detections)
            rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            if queue.qsize() < 2:
                queue.put((rgb_frame, fire_detected, grid_message))
    except Exception as e:
        queue.put((None, False, f"Process error for Camera {cam_index+1}"))
    finally:
        if 'cap' in locals() and cap.isOpened(): cap.release()


# ============================= FIRE DETECTION APPLICATION (MAIN WINDOW) =============================
class FireDetectionApp(QMainWindow):
    CAM_VIEW_WIDTH = 800; CAM_VIEW_HEIGHT = 600
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Detection System Dashboard")
        self.container = QWidget(); self.setCentralWidget(self.container)
        self.container_layout = QVBoxLayout(self.container); self.container_layout.setContentsMargins(0, 0, 0, 0); self.container_layout.setSpacing(0)
        self.container.setStyleSheet("background-color: #E6F2F7;")
        self.model_path = "best_m.pt"
        self.alarm_style_active = "QPushButton { background-color: #228B22 ; color: white; border: none; border-radius: 5px; padding: 10px 20px; font-weight: bold; } QPushButton:hover { background-color: #D22B2B; }"
        self.alarm_style_muted = "QPushButton { background-color: #C04040; color: white; border: none; border-radius: 5px; padding: 10px 20px; font-weight: bold; } QPushButton:hover { background-color: #2E8B57; }"
        self.alarm_sound = QSoundEffect()
        self.alarm_sound.setSource(QUrl.fromLocalFile("alarm.wav"))
        self.sprinkler_countdown = [-1, -1]; self.sprinkler_timers = [QTimer(self), QTimer(self)]; self.sprinkler_timers[0].timeout.connect(lambda: self.update_sprinkler_countdown(0)); self.sprinkler_timers[1].timeout.connect(lambda: self.update_sprinkler_countdown(1))
        self.active_sprinkler_zone = -1
        self.video_labels, self.status_messages, self.no_camera_labels, self.stacked_layouts, self.latest_frame_data = [], ["", ""], [], [], [None, None]
        self.overlay_window, self.mute_button, self.sidebar_is_expanded = None, None, False
        self.setup_header(); self.setup_dashboard_page(); self.setup_footer(); self.setup_sidebar()
        self.clock_timer = QTimer(self); self.clock_timer.timeout.connect(self.update_clock); self.clock_timer.start(1000)
        self.frame_queues = [mp.Queue(maxsize=2) for _ in range(2)]; self.processes = [mp.Process(target=process_video_feed, args=(i, self.frame_queues[i], self.model_path)) for i in range(2)]
        for p in self.processes: p.start()
        self.gui_update_timer = QTimer(self); self.gui_update_timer.timeout.connect(self.update_gui_frames); self.gui_update_timer.start(30)
        self.user_menu_is_expanded = False
        
        # --- FIX: The line that caused maximization has been REMOVED ---
        
        self.show()

    def closeEvent(self, event):
        for p in self.processes:
            if p.is_alive(): p.terminate(); p.join(1)
        super().closeEvent(event)

    def open_registration_window(self):
        """Creates and shows the registration form in a new window."""
        self.registration_window = FinalRegistrationForm()
        self.registration_window.show()

    def setup_header(self):
        header = QFrame(self); header.setStyleSheet("background-color: #153e62;"); header.setFixedHeight(60)
        header_layout = QHBoxLayout(header); header_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("🔥 Fire Detection System"); title.setFont(QFont('Segoe UI', 20, QFont.Bold)); title.setStyleSheet("color: white;")
        self.time_label = QLabel(""); self.time_label.setFont(QFont('Segoe UI', 12)); self.time_label.setStyleSheet("color: white;")
        header_layout.addWidget(title, alignment=Qt.AlignLeft); header_layout.addStretch()
        header_layout.addWidget(self.time_label, alignment=Qt.AlignRight)
        self.container_layout.addWidget(header)

    def setup_dashboard_page(self):
        dashboard_page = QWidget()
        dashboard_layout = QGridLayout(dashboard_page)
        dashboard_layout.setContentsMargins(0,0,0,0); dashboard_layout.setSpacing(0)
        
        self.main_area = QFrame(self)
        self.main_area.setStyleSheet("background-color: white;")
        self.setup_main_area_content(self.main_area)
        
        dashboard_layout.addWidget(self.main_area, 0, 0)
        dashboard_layout.setRowStretch(0, 1)
        
        self.container_layout.addWidget(dashboard_page, 1)

    def setup_main_area_content(self, parent_widget):
        main_area_layout = QGridLayout(parent_widget); main_area_layout.setContentsMargins(20, 20, 20, 20); main_area_layout.setSpacing(5)
        for i in range(2):
            frame_container = QFrame(parent_widget); frame_container.setObjectName(f"frame_container_{i}")
            frame_container.setStyleSheet("background-color: #111; border: 4px solid black; border-radius: 5px;"); frame_container.setFixedSize(self.CAM_VIEW_WIDTH + 10, self.CAM_VIEW_HEIGHT + 50)
            container_vlayout = QVBoxLayout(frame_container); container_vlayout.setContentsMargins(0, 0, 0, 0); container_vlayout.setSpacing(0)
            label_title = QLabel(f"Zone {i+1}"); label_title.setStyleSheet("color: white; background-color: #111; padding: 5px; font-weight: bold;"); label_title.setAlignment(Qt.AlignCenter); label_title.setFont(QFont('Segoe UI', 12))
            container_vlayout.addWidget(label_title, alignment=Qt.AlignTop)
            video_display_widget = QWidget(frame_container)
            video_display_stacked_layout = QStackedLayout(video_display_widget)
            video_label = QLabel(video_display_widget); video_label.setStyleSheet("background-color: black;"); video_label.setAlignment(Qt.AlignCenter); video_label.setScaledContents(True); video_label.setFixedSize(self.CAM_VIEW_WIDTH, self.CAM_VIEW_HEIGHT); video_label.mousePressEvent = lambda event, idx=i: self.video_label_clicked(event, idx)
            video_display_stacked_layout.addWidget(video_label); self.video_labels.append(video_label)
            error_label = QLabel("No Camera Detected"); error_label.setStyleSheet("color: white; background-color: black; font-weight: bold;"); error_label.setFont(QFont('Segoe UI', 24, QFont.Bold)); error_label.setAlignment(Qt.AlignCenter); error_label.setFixedSize(self.CAM_VIEW_WIDTH, self.CAM_VIEW_HEIGHT)
            video_display_stacked_layout.addWidget(error_label); self.no_camera_labels.append(error_label)
            self.stacked_layouts.append(video_display_stacked_layout)
            container_vlayout.addWidget(video_display_widget)
            main_area_layout.addWidget(frame_container, 0, i, alignment=Qt.AlignCenter)

    def setup_footer(self):
        self.footer = QFrame(self); self.footer.setStyleSheet("background-color: #153e62;"); self.footer.setFixedHeight(120)
        footer_container_layout = QHBoxLayout(self.footer); footer_container_layout.setContentsMargins(20, 10, 20, 10)
        content_box = QFrame(self.footer); content_box.setObjectName("footerContentBox"); content_box.setStyleSheet("#footerContentBox { background-color: #1E4D75; border: 1px solid #3082BE; border-radius: 8px; } #footerContentBox QLabel { color: white; font-size: 11pt; }")
        footer_container_layout.addWidget(content_box)
        content_layout = QHBoxLayout(content_box); content_layout.setContentsMargins(20, 10, 20, 10); content_layout.setSpacing(20)
        status_frame = QFrame(content_box); status_frame_layout = QVBoxLayout(status_frame); status_frame_layout.setContentsMargins(0, 0, 0, 0); status_frame_layout.setSpacing(5)
        status_title = QLabel("Zone Status"); status_title.setFont(QFont('Segoe UI', 12, QFont.Bold)); status_frame_layout.addWidget(status_title)
        alert_line_widget = QWidget(); alert_line_layout = QHBoxLayout(alert_line_widget); alert_line_layout.setContentsMargins(0, 0, 0, 0); alert_line_layout.setSpacing(15)
        self.status_summary = QLabel("No Fire or Smoke Detected"); self.status_summary.setFont(QFont('Segoe UI', 11)); self.status_summary.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred); alert_line_layout.addWidget(self.status_summary)
        self.deactivate_button = QPushButton("Deactivate Sprinkler"); self.deactivate_button.setFont(QFont('Segoe UI', 10, QFont.Bold)); self.deactivate_button.setMinimumHeight(35); self.deactivate_button.setStyleSheet("QPushButton { background-color: #C04040; color: white; border-radius: 5px; padding: 8px 20px; } QPushButton:hover { background-color: #D22B2B; }"); self.deactivate_button.clicked.connect(self.deactivate_sprinkler)
        alert_line_layout.addWidget(self.deactivate_button); alert_line_layout.addStretch(); self.deactivate_button.hide(); status_frame_layout.addWidget(alert_line_widget)
        self.sprinkler_timer_label = QLabel(""); self.sprinkler_timer_label.setFont(QFont('Segoe UI', 11, QFont.Bold)); status_frame_layout.addWidget(self.sprinkler_timer_label); self.sprinkler_timer_label.hide(); status_frame_layout.addStretch()
        control_frame = QFrame(content_box); control_frame_layout = QVBoxLayout(control_frame); control_frame_layout.setContentsMargins(0,0,0,0); control_frame_layout.setSpacing(10)
        self.mute_button = QPushButton("Mute Alarm"); self.mute_button.setFont(QFont('Segoe UI', 10, QFont.Bold)); self.mute_button.setStyleSheet(self.alarm_style_muted); self.mute_button.clicked.connect(self.toggle_alarm_sound)
        control_frame_layout.addWidget(self.mute_button, 0, Qt.AlignHCenter)
        system_status_label = QLabel("✅ All Systems Operational"); system_status_label.setFont(QFont('Segoe UI', 11)); system_status_label.setStyleSheet("color: #77DD77;"); control_frame_layout.addWidget(system_status_label, 0, Qt.AlignHCenter); control_frame_layout.addStretch()
        dev_frame = QFrame(content_box); dev_frame_layout = QGridLayout(dev_frame); dev_frame_layout.setSpacing(5)
        fps_title = QLabel("FPS:"); fps_title.setFont(QFont('Segoe UI', 11, QFont.Bold)); fps_value = QLabel("30"); dev_frame_layout.addWidget(fps_title, 0, 0, alignment=Qt.AlignRight); dev_frame_layout.addWidget(fps_value, 0, 1, alignment=Qt.AlignLeft)
        conf_title = QLabel("Confidence:"); conf_title.setFont(QFont('Segoe UI', 11, QFont.Bold)); confidence_label = QLabel("94%"); dev_frame_layout.addWidget(conf_title, 1, 0, alignment=Qt.AlignRight); dev_frame_layout.addWidget(confidence_label, 1, 1, alignment=Qt.AlignLeft)
        content_layout.addWidget(status_frame, 1); content_layout.addWidget(control_frame, 1); content_layout.addWidget(dev_frame, 1)
        self.container_layout.addWidget(self.footer)

    def setup_sidebar(self):
        self.sidebar_width = 240; self.sidebar = QFrame(self); self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("""
            #sidebar { background-color: #153e62; }
            QPushButton { background-color: transparent; color: white; text-align: left; padding: 12px 20px; border: none; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #1E4D75; }
        """)
        self.sidebar_layout = QVBoxLayout(self.sidebar); self.sidebar_layout.setContentsMargins(0, 20, 0, 0); self.sidebar_layout.setSpacing(5); self.sidebar_layout.setAlignment(Qt.AlignTop)
        
        self.sidebar_layout.addWidget(self.create_sidebar_button('fa5s.tachometer-alt', "Dashboard"))
        self.sidebar_layout.addWidget(self.create_sidebar_button('fa5s.user-plus', "Register User"))
        self.sidebar_layout.addStretch()
        self.sidebar_layout.addWidget(self.create_sidebar_button('fa5s.sign-out-alt', "Logout"))
        
        self.sidebar.setGeometry(-self.sidebar_width, 0, self.sidebar_width, self.height())
        self.menu_button = QPushButton(qta.icon('fa5s.bars', color='#153e62'), "", self); self.menu_button.setFixedSize(40, 40); self.menu_button.setCursor(Qt.PointingHandCursor); self.menu_button.setStyleSheet("QPushButton { border: none; background-color: #E6F2F7; border-radius: 20px; }"); self.menu_button.clicked.connect(self.toggle_sidebar)

    def create_sidebar_button(self, icon_name, text):
        button = QPushButton(qta.icon(icon_name, color='white'), f"  {text}")
        button.setCursor(Qt.PointingHandCursor)
        if text == "Register User":
            button.clicked.connect(self.open_registration_window)
        return button

    def toggle_sidebar(self):
        self.animation = QPropertyAnimation(self.sidebar, b"geometry"); self.animation.setDuration(300); self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        start_x = self.sidebar.x(); end_x = 0 if not self.sidebar_is_expanded else -self.sidebar_width
        self.animation.setStartValue(QRect(start_x, 0, self.sidebar_width, self.height())); self.animation.setEndValue(QRect(end_x, 0, self.sidebar_width, self.height()))
        if not self.sidebar_is_expanded: self.sidebar.raise_()
        self.animation.start(); self.sidebar_is_expanded = not self.sidebar_is_expanded

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.menu_button.move(5, self.height() // 2 - self.menu_button.height() // 2)
        if self.sidebar_is_expanded: self.sidebar.setGeometry(0, 0, self.sidebar_width, self.height())
        else: self.sidebar.setGeometry(-self.sidebar_width, 0, self.sidebar_width, self.height())
        
    def update_clock(self): self.time_label.setText(QDateTime.currentDateTime().toString("dd MMMM yyyy | HH:mm:ss"))
    def toggle_alarm_sound(self):
        if self.alarm_sound.isPlaying(): self.alarm_sound.stop()
        elif any(self.status_messages): self.alarm_sound.play()
        self.update_footer_status()
    def update_sprinkler_countdown(self, zone_index):
        if self.sprinkler_countdown[zone_index] > 0: self.sprinkler_countdown[zone_index] -= 1
        if self.sprinkler_countdown[zone_index] == 0: self.sprinkler_timers[zone_index].stop()
        self.update_footer_status()
    def deactivate_sprinkler(self):
        if self.active_sprinkler_zone != -1:
            zone = self.active_sprinkler_zone; self.sprinkler_timers[zone].stop(); self.sprinkler_countdown[zone] = -1; self.status_messages[zone] = ""; self.active_sprinkler_zone = -1
            if self.alarm_sound.isPlaying(): self.alarm_sound.stop()
            self.update_footer_status()
    def update_footer_status(self):
        self.active_sprinkler_zone = next((i for i, c in enumerate(self.sprinkler_countdown) if c >= 0), -1)
        summary = next((msg for msg in self.status_messages if msg), "No Fire or Smoke Detected")
        if self.active_sprinkler_zone != -1:
            zone = self.active_sprinkler_zone; countdown = self.sprinkler_countdown[zone]; self.status_summary.setText(summary); self.status_summary.setStyleSheet("color: red; font-weight: bold;")
            if countdown > 0: self.sprinkler_timer_label.setText(f"Activating Sprinkler in {countdown} sec..."); self.sprinkler_timer_label.setStyleSheet("color: #FFD700;"); self.sprinkler_timer_label.show(); self.deactivate_button.hide()
            else: self.sprinkler_timer_label.hide(); self.status_summary.setText(f"✅ Sprinkler {zone + 1} Activated"); self.status_summary.setStyleSheet("color: lime; font-weight: bold;"); self.deactivate_button.show()
        else: self.status_summary.setText("No Fire or Smoke Detected"); self.status_summary.setStyleSheet("color: lime; font-weight: normal;"); self.sprinkler_timer_label.hide(); self.deactivate_button.hide()
        if self.alarm_sound.isPlaying(): self.mute_button.setText("Mute Alarm"); self.mute_button.setStyleSheet(self.alarm_style_active)
        else: self.mute_button.setText("Alarm"); self.mute_button.setStyleSheet(self.alarm_style_muted)
        if not any(self.status_messages) and self.alarm_sound.isPlaying(): self.alarm_sound.stop()
    def update_gui_frames(self):
        for i, q in enumerate(self.frame_queues):
            try:
                frame_data = q.get(timeout=0.01); self.latest_frame_data[i] = frame_data; frame, fire_detected, grid_message = frame_data
                frame_container = self.main_area.findChild(QFrame, f"frame_container_{i}")
                if frame is None:
                    self.status_messages[i] = grid_message; self.stacked_layouts[i].setCurrentIndex(1)
                    if frame_container: frame_container.setStyleSheet("background-color: #111; border: 4px solid black; border-radius: 5px;")
                    continue
                self.stacked_layouts[i].setCurrentIndex(0); h, w, ch = frame.shape; q_image = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888); self.video_labels[i].setPixmap(QPixmap.fromImage(q_image))
                if frame_container: frame_container.setStyleSheet(f"background-color: #111; border: 4px solid {'red' if fire_detected else 'black'}; border-radius: 5px;")
                if fire_detected:
                    self.status_messages[i] = grid_message
                    if self.sprinkler_countdown[i] == -1: self.sprinkler_countdown[i] = 10; self.sprinkler_timers[i].start(1000); 
                    if not self.alarm_sound.isPlaying(): self.alarm_sound.play()
                else:
                    if self.sprinkler_countdown[i] > 0: self.sprinkler_timers[i].stop(); self.sprinkler_countdown[i] = -1; self.status_messages[i] = ""
                    elif self.sprinkler_countdown[i] == -1: self.status_messages[i] = ""
            except Empty: pass
            except Exception as e: print(f"Error updating GUI frame for camera {i+1}: {e}"); traceback.print_exc()
        self.update_footer_status()
    def video_label_clicked(self, event: QEvent, cam_index: int):
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'overlay_window') and self.overlay_window and self.overlay_window.isVisible(): self.overlay_window.close()
            self.overlay_window = QMainWindow(self); self.overlay_window.setWindowTitle(f"Zone {cam_index + 1} - Enlarged View"); self.overlay_window.setWindowModality(Qt.ApplicationModal)
            central_widget = QWidget(self.overlay_window); self.overlay_window.setCentralWidget(central_widget); overlay_layout = QVBoxLayout(central_widget); overlay_layout.setContentsMargins(0, 0, 0, 0)
            self.overlay_video_label = QLabel(central_widget); self.overlay_video_label.setStyleSheet("background-color: black;"); self.overlay_video_label.setAlignment(Qt.AlignCenter); self.overlay_video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding); self.overlay_video_label.setScaledContents(True); overlay_layout.addWidget(self.overlay_video_label)
            self.overlay_window.showMaximized(); self.overlay_update_timer = QTimer(self.overlay_window); self.overlay_update_timer.timeout.connect(lambda: self.update_overlay_frame(cam_index)); self.overlay_update_timer.start(30); self.overlay_window.destroyed.connect(self.overlay_update_timer.stop)
    def update_overlay_frame(self, cam_index: int):
        if not hasattr(self, 'overlay_video_label') or not self.overlay_window.isVisible(): return
        try:
            frame_data = self.latest_frame_data[cam_index]; 
            if frame_data is None: return
            frame, fire_detected, _ = frame_data
            if frame is None: self.overlay_video_label.setText("No Feed Available"); self.overlay_video_label.setStyleSheet("background-color: black; color: white; font-size: 24px;")
            else: self.overlay_video_label.setText(""); h, w, ch = frame.shape; q_image = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888); self.overlay_video_label.setPixmap(QPixmap.fromImage(q_image))
            self.overlay_window.setWindowTitle(f"Zone {cam_index + 1} - Enlarged View - {'🔥 FIRE DETECTED' if fire_detected else 'Normal'}")
        except Exception as e: print(f"Error updating overlay frame: {e}")

    # Add this line to your FireDetectionApp's __init__ method
    

    def open_registration_window(self):
        """Creates and shows the registration form in a new window."""
        # We store the window in 'self' to prevent it from disappearing.
        self.registration_window = FinalRegistrationForm()
        self.registration_window.show()
        if self.sidebar_is_expanded:
            self.toggle_sidebar()

    def setup_sidebar(self):
        self.sidebar_width = 240
        self.sidebar = QFrame(self)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("""
            #sidebar { background-color: #153e62; }
            QPushButton { 
                background-color: transparent; color: white; text-align: left; 
                padding: 12px 20px; border: none; font-size: 14px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #1E4D75; }
            QPushButton#submenu {
                font-size: 13px; font-weight: normal; padding-left: 40px;
                background-color: #1E4D75;
            }
            QPushButton#submenu:hover { background-color: #2c3e50; }
        """)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 20, 0, 0)
        self.sidebar_layout.setSpacing(5)
        self.sidebar_layout.setAlignment(Qt.AlignTop)

        # --- Sidebar Buttons ---
        dashboard_button = QPushButton(qta.icon('fa5s.tachometer-alt', color='white'), "  Dashboard")
        dashboard_button.setCursor(Qt.PointingHandCursor)
        self.sidebar_layout.addWidget(dashboard_button)
        
        user_mgmt_button = QPushButton(qta.icon('fa5s.users', color='white'), "  User Management")
        user_mgmt_button.setCursor(Qt.PointingHandCursor)
        user_mgmt_button.clicked.connect(self.toggle_user_menu)
        self.sidebar_layout.addWidget(user_mgmt_button)

        # User Management sub-menu buttons (initially hidden)
        self.register_user_button = QPushButton(qta.icon('fa5s.user-plus', color='white'), "  Register User")
        self.register_user_button.setObjectName("submenu")
        self.register_user_button.setCursor(Qt.PointingHandCursor)
        self.register_user_button.clicked.connect(self.open_registration_window)

        self.existing_users_button = QPushButton(qta.icon('fa5s.address-book', color='white'), "  Existing Users")
        self.existing_users_button.setObjectName("submenu")
        self.existing_users_button.setCursor(Qt.PointingHandCursor)
        # self.existing_users_button.clicked.connect(self.open_existing_users_window)

        self.sidebar_layout.addWidget(self.register_user_button)
        self.sidebar_layout.addWidget(self.existing_users_button)
        self.register_user_button.hide()
        self.existing_users_button.hide()

        self.sidebar_layout.addStretch()
        logout_button = QPushButton(qta.icon('fa5s.sign-out-alt', color='white'), "  Logout")
        logout_button.setCursor(Qt.PointingHandCursor)
        self.sidebar_layout.addWidget(logout_button)
        
        self.sidebar.setGeometry(-self.sidebar_width, 0, self.sidebar_width, self.height())
        self.menu_button = QPushButton(qta.icon('fa5s.bars', color='#153e62'), "", self)
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setCursor(Qt.PointingHandCursor)
        self.menu_button.setStyleSheet("QPushButton { border: none; background-color: #E6F2F7; border-radius: 20px; }")
        self.menu_button.clicked.connect(self.toggle_sidebar)

    def toggle_user_menu(self):
        """Shows or hides the user management sub-menu."""
        if self.user_menu_is_expanded:
            self.register_user_button.hide()
            self.existing_users_button.hide()
        else:
            self.register_user_button.show()
            self.existing_users_button.show()
        self.user_menu_is_expanded = not self.user_menu_is_expanded


# ============================= MAIN APPLICATION ENTRY POINT =============================
if __name__ == "__main__":
    try:
        mp.set_start_method('spawn', force=True)
    except RuntimeError: pass
    
    app = QApplication(sys.argv)
    window = FireDetectionApp()
    sys.exit(app.exec_())