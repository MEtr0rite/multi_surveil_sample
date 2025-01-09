import colorama
from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QWidget, QApplication
)
from PySide6.QtCore import (
    Slot, QThread, Qt,
)
from PySide6.QtGui import (
    QDesktopServices, QPixmap, QImage
)
import PySide6
from script import data_servant, processor_servant
import cv2
import os


class SurveilUnit(QWidget):

    def __init__(self, parent=None, id=None, ip=None):

        super(SurveilUnit, self).__init__(parent)

        self.is_running = False
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("A Random Name"))
        self.start_button = QPushButton("Start this thread")
        self.close_button = QPushButton("Close this thread")
        self.image = QLabel("Waiting...")
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.close_button)

        self.w_worker = data_servant.Worker(id=id, addr=ip)
        self.p_worker = processor_servant.Worker(frame_rate=self.w_worker.frame_rate)

        self.start_button.pressed.connect(self.start_it)
        self.close_button.pressed.connect(self.close_thread)

        self.w_thread = QThread()
        self.p_thread = QThread()
        self.w_worker.moveToThread(self.w_thread)
        self.p_worker.moveToThread(self.p_thread)

        self.w_worker.signals.channel_established.connect(self.set_legal_flag)

        self.w_worker.signals.received_image.connect(self.p_worker.process_image)
        self.p_worker.signals.processed_image.connect(self.update_image)

        self.w_thread.started.connect(self.w_worker.timer.start)

        self.w_worker.signals.finished.connect(self.w_worker.deleteLater)
        self.w_worker.signals.finished.connect(lambda: print("w_worker finished"))
        self.w_worker.signals.finished.connect(self.w_thread.quit)
        self.w_thread.finished.connect(lambda: print("w_thread finished"))
        self.w_thread.finished.connect(self.w_thread.deleteLater)
        self.w_thread.finished.connect(self.deleteLater)

        self.p_worker.signals.finished.connect(self.p_worker.deleteLater)
        self.p_worker.signals.finished.connect(lambda: print("p_worker finished"))
        self.p_worker.signals.finished.connect(self.p_thread.quit)
        self.p_thread.finished.connect(lambda: print("p_thread finished"))
        self.p_thread.finished.connect(self.p_thread.deleteLater)
        self.p_thread.finished.connect(self.deleteLater)

        self.setLayout(self.layout)

    @Slot()
    def start_it(self):
        if not self.w_thread.isRunning():
            self.w_thread.start()
            print(f"Receiver Thread {self.w_worker.thread()} open successful.")
            self.p_thread.start()
            print(f"Processor Thread {self.p_worker.thread()} open successful.")
        else:
            print(f"Threads Already started or Initialization not finished.")

    @Slot()
    def set_legal_flag(self):
        print(f"Thread {self.w_worker.thread()} is running!")
        self.is_running = True

    @Slot()
    def update_image(self, frame):
        if frame is not None:
            # print(" IMAGE RECEIVED", end="")
            image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.image.setPixmap(pixmap)
        else:
            print(colorama.Fore.RED + " IMAGE NOT RECEIVED")

    @Slot()
    def close_thread(self):
        self.w_worker.set_terminate()
        self.p_worker.set_terminate()
        # self.w_thread.wait()
        # self.p_thread.wait()
        # self.deleteLater()

    @Slot()
    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        print(f"CLOSING SURVEILLANCE")
        self.close_thread()
        super().closeEvent(event)


if __name__ == "__main__":
    print(os.curdir)
    app = QApplication()
    temp = SurveilUnit(id=1, ip="1.mp4")
    temp.show()
    app.exec()
