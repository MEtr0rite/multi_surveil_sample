from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QWidget, QMainWindow, QApplication, QHBoxLayout,
    QDialog
)
from PySide6.QtCore import QTimer, Slot, QThreadPool
import PySide6
import sys
import time
from script.rtsp_chooser import RtspDialog
from script.surveil_unit import SurveilUnit


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.THREAD_LIMIT = 20
        self.thread_counter = 0
        self.unit_dict = []
        # self.last_rtsp_ip = None
        self.last_rtsp_ip = "rtsp://admin:SHZD12345@192.168.102.136:554/STreaming/Channels/101"
        # self.last_rtsp_ip = "data/GBC/1.mp4"

        self.layout = QVBoxLayout()

        self.l = QLabel("Waiting...")
        self.layout.addWidget(self.l)

        b = QPushButton("Open a new one!")
        b.pressed.connect(self.open_video)
        self.layout.addWidget(b)

        self.video_layout = QHBoxLayout()
        self.idle_label = QLabel("Waiting...")
        self.video_layout.addWidget(self.idle_label)
        self.layout.addLayout(self.video_layout)

        self.w = QWidget()

        self.w.setFixedHeight(720)
        self.w.setLayout(self.layout)

        self.setCentralWidget(self.w)

        self.show()

        print(f"Multithreading with maximum {QThreadPool.globalInstance().maxThreadCount()} threads")

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

    @Slot()
    def closeEvent(self, event: PySide6.QtGui.QCloseEvent):
        print("\nNOW CLOSING")
        for it in self.unit_dict:
            it.close_thread()
        event.accept()
        super().closeEvent(event)
        pass

    @Slot()
    def adjust_thread_counter(self):
        self.thread_counter = self.thread_counter - 1
        if self.thread_counter < 1:
            self.idle_label = QLabel("Waiting...")
            self.video_layout.addWidget(self.idle_label)

    @Slot()
    def open_video(self):
        if self.thread_counter < self.THREAD_LIMIT:
            rtsp_chooser = RtspDialog(self, self.last_rtsp_ip)
            result = rtsp_chooser.exec()
            if result == QDialog.Accepted:
                entered_text = rtsp_chooser.getEnteredText()
                print("\nEntered text:", entered_text)
                rtsp_ip = entered_text
                self.thread_counter = self.thread_counter + 1
                surveil_unit = SurveilUnit(id=self.thread_counter, ip=rtsp_ip)
                if not surveil_unit.w_worker.need_terminate:
                    surveil_unit.w_thread.finished.connect(self.adjust_thread_counter)
                    self.video_layout.addWidget(surveil_unit)
                    self.unit_dict.append(surveil_unit)  # is this needed?
                    if self.thread_counter == 1:
                        self.idle_label.deleteLater()
                else:
                    self.thread_counter = self.thread_counter - 1
                    print("Unsuccessful try. surveil unit deleted.")
                    surveil_unit.deleteLater()
            else:
                print("Unaccepted change.")
        else:
            print("Thread limitation reached.")

    @Slot()
    def recurring_timer(self):
        t = time.localtime()
        str_t = time.strftime('%Y-%m-%d %H:%M:%S', t)
        self.l.setText(str_t)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec()
