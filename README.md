# Simple RTMP Stream Viewer 

A Python-based RTMP (Real-Time Messaging Protocol) Stream Viewer application built with PyQt5 and OpenCV. This application allows you to run an RTMP server and view the incoming video stream with real-time statistics such as FPS, bitrate, and resolution.

## Table of Contents

📥 Installation | 🚀 Usage ➡️ 📝 Basic 🔧 CLI | 🌟 Features | 📋 Requirements | 🤝 Contributing | ⚖️ License

## Installation

### Prerequisites

- **Python 3.6 or higher** is required.
- **pip** package manager should be installed.

### Install Required Python Packages

Open your terminal or command prompt and run the following command to install the necessary packages:

```bash
pip install asyncio opencv-python numpy PyQt5
```

## Usage

### Basic Usage

Run the application using the following command:

```bash
python rtmp_stream_viewer.py
```

This will start the RTMP server on the default port **1935** and launch the viewer application with default settings.

### Command-Line Options

You can customize the application's behavior using various command-line options:

```bash
python rtmp_stream_viewer.py [options]
```

#### Available Options:

- `--port PORT`: Specify the RTMP server port (default: **1935**).

- `--stream-path PATH`: Define the RTMP stream path (default: **/live/stream**).

- `--window-size WIDTHxHEIGHT`: Set the application window size (default: **800x600**).

- `--display-size WIDTHxHEIGHT`: Set the video display size within the application (default: **640x480**).

- `--no-dark-theme`: Disable the dark theme.

- `--fullscreen`: Run the application in fullscreen mode.

- `--fps-history-length LENGTH`: Set the FPS history length for moving average calculation (default: **120**).

- `--debug`: Enable debug logging for troubleshooting.

- `--ip IP_ADDRESS`: Specify the IP address to bind the RTMP server to (default: **0.0.0.0**).

- `--local-ip IP_ADDRESS`: Specify the local IP address to display (default: auto-detected).

- `--stream-url URL`: Specify a custom RTMP stream URL to connect to (overrides other stream settings).

- `--version`: Show the application version and exit.

#### Examples:

- **Specify a Different Port and Stream Path:**

  ```bash
  python rtmp_stream_viewer.py --port 1936 --stream-path /my/stream
  ```

- **Set a Custom Window Size and Disable the Dark Theme:**

  ```bash
  python rtmp_stream_viewer.py --window-size 1024x768 --no-dark-theme
  ```

- **Run in Fullscreen Mode with a Specific Display Size:**

  ```bash
  python rtmp_stream_viewer.py --fullscreen --display-size 800x600
  ```

- **Enable Debug Logging:**

  ```bash
  python rtmp_stream_viewer.py --debug
  ```

- **Specify a Custom Stream URL:**

  ```bash
  python rtmp_stream_viewer.py --stream-url rtmp://example.com:1935/live/stream
  ```

- **Bind the RTMP Server to a Specific IP Address:**

  ```bash
  python rtmp_stream_viewer.py --ip 192.168.1.100
  ```

## Features

- **RTMP Server**: Starts an RTMP server to receive live video streams.
- **Real-Time Viewing**: Displays the incoming video stream using PyQt5.
- **Statistics Display**: Shows real-time FPS, bitrate, and resolution.
- **Customizable UI**: Command-line options to customize window size, display size, and theme.
- **Fullscreen Mode**: Option to run the viewer in fullscreen.
- **Debug Mode**: Enable debug logging for troubleshooting purposes.

## Requirements

- **Python 3.6 or higher**
- **Asyncio**
- **OpenCV (cv2)**
- **NumPy**
- **PyQt5**


## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

**Disclaimer:** This application is for educational purposes. Ensure you have the rights and permissions to stream and view the content you are accessing.