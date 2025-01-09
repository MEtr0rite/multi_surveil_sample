import sys
import cv2
from PySide6.QtCore import Slot, Signal, QThread, QObject
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton
from PySide6.QtGui import QImage, QPixmap


class VideoWorker(QObject):
    frame_ready = Signal(QImage)  # Signal to send the processed frame to the main thread
    finished = Signal()  # Signal to indicate that the worker has finished

    def __init__(self, fps=24):
        super().__init__()
        self.fps = fps
        self.running = True
        self.cap = cv2.VideoCapture("1.mp4")  # Use camera index 0 or video file path

        if not self.cap.isOpened():
            raise RuntimeError("Cannot open the video source")

    @Slot()
    def process_video(self):
        """Capture and process frames."""
        interval = 1.0 / self.fps  # Frame interval in seconds
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert frame to QImage
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Emit the QImage to the main thread
            self.frame_ready.emit(q_image)

            # Limit FPS
            QThread.msleep(int(interval * 1000))  # Sleep for the frame interval

        self.cap.release()
        self.finished.emit()

    def stop(self):
        """Stop the video processing loop."""
        print("STOPPPP")
        self.running = False


class VideoCaptureWidget(QWidget):
    def __init__(self, fps=24):
        super().__init__()
        self.setWindowTitle("OpenCV Video Capture with QThread")

        # QLabel to display the video frames
        self.video_label = QLabel()
        self.video_label.setFixedSize(480, 270)  # Set display size

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)

        # VideoWorker and QThread setup
        self.thread = QThread()
        self.worker = VideoWorker(fps=fps)
        self.worker.moveToThread(self.thread)

        start_button = QPushButton("Start this thread")
        close_button = QPushButton("Close this thread")
        start_button.pressed.connect(self.start_it)
        close_button.pressed.connect(self.worker.stop)
        layout.addWidget(start_button)
        layout.addWidget(close_button)

        self.setLayout(layout)

        # Connect signals and slots
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start the thread and video processing
        self.thread.started.connect(self.worker.process_video)

    @Slot()
    def update_frame(self, q_image):
        """Update the QLabel with the new frame."""
        self.video_label.setPixmap(QPixmap.fromImage(q_image))

    @Slot()
    def closeEvent(self, event):
        """Override closeEvent to stop the worker and release resources."""
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)

    @Slot()
    def start_it(self):
        if not self.thread.isRunning():
            self.thread.start()
            print("Thread open successful.")
        else:
            print("Already started")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create the VideoCapture widget with a frame rate limit
    fps = 24  # Desired frame rate (frames per second)
    video_widget = VideoCaptureWidget(fps=fps)
    video_widget.show()

    sys.exit(app.exec())
