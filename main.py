import argparse  # Added import for argparse
import asyncio
import sys
import cv2
import numpy as np
import os
import socket
import time
from collections import deque

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QGroupBox, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtGui, QtCore


def parse_args():
    parser = argparse.ArgumentParser(description="RTMP Stream Viewer")
    parser.add_argument('--port', type=int, default=1935,
                        help='Specify the RTMP server port (default: 1935)')
    parser.add_argument('--stream-path', type=str, default='/live/stream',
                        help='Specify the RTMP stream path (default: /live/stream)')
    parser.add_argument('--window-size', type=str, default='800x600',
                        help='Specify the window size in format WIDTHxHEIGHT (default: 800x600)')
    parser.add_argument('--no-dark-theme', action='store_true',
                        help='Disable the dark theme')
    parser.add_argument('--display-size', type=str, default='640x480',
                        help='Specify the display size for the video (default: 640x480)')
    parser.add_argument('--fps-history-length', type=int, default=120,
                        help='Specify the FPS history length (default: 120)')
    parser.add_argument('--fullscreen', action='store_true',
                        help='Run the application in fullscreen mode')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--ip', type=str, default='0.0.0.0',
                        help='Specify the IP address to bind to (default: 0.0.0.0)')
    parser.add_argument('--local-ip', type=str, default=None,
                        help='Specify the local IP address to display (default: auto-detect)')
    parser.add_argument('--stream-url', type=str, default=None,
                        help='Specify the RTMP stream URL to connect to (default: constructed from IP and port)')
    parser.add_argument('--version', action='version', version='RTMP Stream Viewer 1.0')
    return parser.parse_args()


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    stream_status_signal = pyqtSignal(bool)
    fps_signal = pyqtSignal(float)
    bitrate_signal = pyqtSignal(float, str)
    resolution_signal = pyqtSignal(str)

    def __init__(self, stream_url, fps_history_length):
        super().__init__()
        self.stream_url = stream_url  # Use the provided stream URL
        self._run_flag = True
        self.fps_history = deque(maxlen=fps_history_length)  # Moving average over specified frames

    def run(self):
        while self._run_flag:
            cap = cv2.VideoCapture(self.stream_url)  # Use the stream URL
            if cap.isOpened():
                self.stream_status_signal.emit(True)
                prev_time = time.time()
                frame_count = 0
                total_size = 0

                # Capture the resolution
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.resolution_signal.emit(f"{width}x{height}")

                while self._run_flag:
                    ret, cv_img = cap.read()
                    if ret:
                        # Calculate FPS with moving average
                        current_time = time.time()
                        fps = 1.0 / (current_time - prev_time)
                        prev_time = current_time
                        self.fps_history.append(fps)
                        avg_fps = sum(self.fps_history) / len(self.fps_history)
                        self.fps_signal.emit(avg_fps)

                        # Calculate bitrate
                        frame_size = cv_img.nbytes
                        total_size += frame_size
                        frame_count += 1

                        if frame_count >= avg_fps:  # Update bitrate every second based on FPS
                            bitrate = (total_size * 8) / 1000  # in kbps
                            if bitrate > 2000:
                                bitrate /= 1000  # Convert to mbps
                                self.bitrate_signal.emit(bitrate, "Mbps")
                            else:
                                self.bitrate_signal.emit(bitrate, "kbps")
                            frame_count = 0
                            total_size = 0

                        self.change_pixmap_signal.emit(cv_img)
                    else:
                        break
                cap.release()
                self.stream_status_signal.emit(False)
            else:
                self.stream_status_signal.emit(False)
                print("Waiting for RTMP stream...")
                self.msleep(1000)  # Wait for 1 second before trying again

    def stop(self):
        self._run_flag = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self, local_ip, port, stream_url, width, height, display_width, display_height, fullscreen, fps_history_length):
        super().__init__()
        self.setWindowTitle("RTMP Stream Viewer")
        self.resize(width, height)  # Set the window size from args
        self.display_width = display_width
        self.display_height = display_height

        if fullscreen:
            self.showFullScreen()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Video display label
        self.image_label = QLabel(self)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Group box for stream info
        info_group_box = QGroupBox("Stream Information")
        info_group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        info_layout = QVBoxLayout()
        info_group_box.setLayout(info_layout)

        # Stream information labels
        self.ip_label = QLabel(f"Local IP Address: {local_ip}")
        self.url_label = QLabel(f"RTMP URL: {stream_url}")
        self.status_label = QLabel("Stream Status: Not Connected")
        self.status_label.setStyleSheet("color: red;")
        self.fps_label = QLabel("FPS: 0")
        self.bitrate_label = QLabel("Bitrate: 0 kbps")
        self.resolution_label = QLabel("Resolution: 0x0")

        # Set font
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.ip_label.setFont(font)
        self.url_label.setFont(font)
        self.status_label.setFont(font)
        self.fps_label.setFont(font)
        self.bitrate_label.setFont(font)
        self.resolution_label.setFont(font)

        # Add labels to info layout
        info_layout.addWidget(self.ip_label)
        info_layout.addWidget(self.url_label)
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.fps_label)
        info_layout.addWidget(self.bitrate_label)
        info_layout.addWidget(self.resolution_label)

        # Quit button
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close_application)
        info_layout.addWidget(self.quit_button)

        # Add widgets to main layout
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(info_group_box)

        # Set margins and padding
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Start the video thread with provided stream URL and FPS history length
        self.thread = VideoThread(stream_url, fps_history_length)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.stream_status_signal.connect(self.update_stream_status)
        self.thread.fps_signal.connect(self.update_fps)
        self.thread.bitrate_signal.connect(self.update_bitrate)
        self.thread.resolution_signal.connect(self.update_resolution)
        self.thread.start()

    def close_application(self):
        self.thread.stop()
        QApplication.quit()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def update_stream_status(self, status):
        if status:
            self.status_label.setText("Stream Status: Connected")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Stream Status: Not Connected")
            self.status_label.setStyleSheet("color: red;")

    def update_fps(self, fps):
        self.fps_label.setText(f"FPS: {fps:.2f}")

    def update_bitrate(self, bitrate, unit):
        self.bitrate_label.setText(f"Bitrate: {bitrate:.2f} {unit}")

    def update_resolution(self, resolution):
        self.resolution_label.setText(f"Resolution: {resolution}")

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(
            rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888
        )
        p = convert_to_Qt_format.scaled(
            self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio
        )
        return QPixmap.fromImage(p)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"New client connected: {addr[0]}:{addr[1]}")

    # Receive the RTMP handshake
    c1 = await reader.read(1536)
    s1 = b'\x03' + os.urandom(1535)
    writer.write(s1)
    await writer.drain()

    # Complete the handshake
    c2 = await reader.read(1536)
    s2 = c1
    writer.write(s2)
    await writer.drain()

    # Handle RTMP messages
    while True:
        chunk_header = await reader.read(1)
        if not chunk_header:
            break
        # Implement RTMP protocol handling here


async def run_server(bind_ip, port, stream_path):
    local_ip = get_local_ip()
    server = await asyncio.start_server(handle_client, bind_ip, port)
    addr = server.sockets[0].getsockname()

    stream_url = f"rtmp://{local_ip}:{port}{stream_path}"

    print("\n--- RTMP Server Information ---")
    print(f"Local IP Address: {local_ip}")
    print(f"Server running on: {addr[0]}:{addr[1]}")
    print(f"RTMP URL: {stream_url}")
    print("Use this URL in your RTMP Streaming software")
    print("Make sure your device is on the same network as this server")
    print("Press 'Q' to quit the application")
    print("--------------------------------\n")

    async with server:
        await server.serve_forever()


def apply_dark_theme(app):
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(35, 35, 35))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    app.setPalette(palette)


if __name__ == '__main__':
    args = parse_args()  # Parse command-line arguments
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Apply dark theme unless disabled
    if not args.no_dark_theme:
        apply_dark_theme(app)

    # Get local IP address
    if args.local_ip:
        local_ip = args.local_ip
    else:
        local_ip = get_local_ip()

    port = args.port
    stream_path = args.stream_path
    stream_url = args.stream_url

    # If stream_url is not provided, build it
    if not stream_url:
        stream_url = f"rtmp://{local_ip}:{port}{stream_path}"

    # Parse window size
    window_size = args.window_size
    try:
        width, height = map(int, window_size.lower().split('x'))
    except ValueError:
        print("Invalid window size format. Using default 800x600.")
        width, height = 800, 600

    # Parse display size
    display_size = args.display_size
    try:
        display_width, display_height = map(int, display_size.lower().split('x'))
    except ValueError:
        print("Invalid display size format. Using default 640x480.")
        display_width, display_height = 640, 480

    # Start the MainWindow with parsed parameters
    main_window = MainWindow(
        local_ip=local_ip,
        port=port,
        stream_url=stream_url,
        width=width,
        height=height,
        display_width=display_width,
        display_height=display_height,
        fullscreen=args.fullscreen,
        fps_history_length=args.fps_history_length
    )
    main_window.show()

    loop = asyncio.get_event_loop()
    loop.create_task(run_server(args.ip, port, stream_path))

    if args.debug:
        print("Debug mode enabled")
        # Implement additional debug logging if necessary

    sys.exit(app.exec_())
