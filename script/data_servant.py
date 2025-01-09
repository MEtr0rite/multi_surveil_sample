from PySide6.QtCore import QTimer, Slot, QObject
import time
import cv2
import colorama
from script.worker_signal import WorkerSignals


class Worker(QObject):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        print("--------Initialize a Receiver servant")
        print(f"--------args:{args}")
        print(f"--------kwargs:{kwargs}")
        self.args = args
        self.kwargs = kwargs
        self.need_terminate = False
        self.signals = WorkerSignals()
        self.timer = QTimer()

        colorama.init(autoreset=True)

        addr = self.kwargs["addr"]
        self.cap = cv2.VideoCapture(addr)
        if self.cap.isOpened():
            self.signals.channel_established.emit()
            self.fw = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.fh = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.frame_rate = self.cap.get(cv2.CAP_PROP_FPS)
            print(f"--------successfully opened. {self.fw}*{self.fh}, {self.frame_rate} fps")
            self.timer.setInterval(int(500 / self.frame_rate))
            self.timer.timeout.connect(self.timeout_callback)
        else:
            print("--------can't open. please retry.")
            self.set_terminate()

    @Slot()
    def timeout_callback(self):
        if not self.need_terminate:
            cur_t = time.time()
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.signals.received_image.emit(frame)
                else:
                    print(colorama.Fore.RED + "--------Can't receive frame (stream end?). Retrying ...")
                    self.cap.open(self.kwargs["addr"])
            else:
                print(colorama.Fore.RED + "--------not opened. WHY???")
        else:
            print(colorama.Fore.RED + "\r--------Already terminated. WHY???", end="")

    @Slot()
    def set_terminate(self):
        print("--------Set Receiver termination successful.ip:" + self.kwargs["addr"])
        if self.timer.isActive():
            self.timer.stop()
        self.need_terminate = True
        self.cap.release()
        self.signals.finished.emit()

