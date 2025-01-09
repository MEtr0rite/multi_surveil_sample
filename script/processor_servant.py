from PySide6.QtCore import Slot, QObject
import time
import cv2
import numpy as np
import os
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
        print("--------Initialize a Processor servant")
        print(f"--------args:{args}")
        print(f"--------kwargs:{kwargs}")
        self.args = args
        self.kwargs = kwargs

        str_t = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        self.out_dir = os.path.join("cache", str_t)
        os.makedirs(self.out_dir, exist_ok=True)

        self.frame_rate = self.kwargs["frame_rate"]
        self.update_freq = 16
        self.roi = None
        # self.roi = [0, 200, 1920, 1080]
        # print(self.kwargs["frame_rate"], type(self.kwargs["frame_rate"]))
        self.threshold = 50
        self.frm_size = 8
        self.signals = WorkerSignals()
        self.counts = 0
        self.move_counts = 0
        self.stop_counts = 0
        self.null_counts = 0
        self.bg_counts = 0
        self.isWriting = False
        self.SKIP_BG_UPDATE = False
        self.move_state = False
        self.out = None
        self.bg_pic = None
        self.frm_que = []
        self.bg_que = []

    def update_background(self, frame):

        if self.bg_pic is None:
            self.bg_pic = frame
            return
        if self.SKIP_BG_UPDATE:
            return
        self.counts += 1

        if self.counts >= self.frame_rate:
            self.counts = 0
            self.bg_que.append(frame)
            self.bg_counts += 1
            if self.bg_counts >= self.update_freq:
                print("\n now update background\n")
                temp = np.median(self.bg_que, axis=0).astype(np.uint8)
                self.bg_pic = np.median([self.bg_pic, temp], axis=0).astype(np.uint8)
                self.bg_counts = 0
                self.bg_que = []

    def check_movement(self, frame):

        frame_diff = cv2.cvtColor(cv2.absdiff(frame, self.bg_pic), cv2.COLOR_BGR2GRAY)
        ret, thres = cv2.threshold(frame_diff, self.threshold, 255, cv2.THRESH_BINARY)
        temp = cv2.dilate(thres, None, iterations=2)
        temp = cv2.erode(temp, None, iterations=1)
        self.frm_que.append(temp)

        if len(self.frm_que) >= self.frm_size:

            sum_frames = sum(self.frm_que).astype(np.uint8)
            contours, hierarchy = cv2.findContours(sum_frames, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            self.move_state = False
            sum0 = max0 = 0
            cur_diff = frame.copy()
            area = sum_frames.shape[0] * sum_frames.shape[1]
            for i, cnt in enumerate(contours):
                sum0 = sum0 + cv2.contourArea(cnt)
                max0 = np.max([max0, cv2.contourArea(cnt)])
                cv2.drawContours(cur_diff, contours, i, (0, 0, 255), 3)
                if max0 * 200 > area:  # or sum0 * 20 > area:
                    self.move_state = True
                    break
            self.frm_que = []

            cur_diff = cv2.resize(cur_diff, (480, 270))
            # self.signals.processed_image.emit(cur_diff)
            self.signals.processed_image.emit(cv2.cvtColor(cur_diff, cv2.COLOR_BGR2RGB))
            #                           self.move_state, self.isWriting)

    @Slot()
    def process_image(self, frame):
        if self.roi is not None:
            frame = frame[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]]
        self.update_background(frame)
        self.check_movement(frame)

        if self.move_state:
            self.move_counts += 1
            self.stop_counts = 0  # max(self.stop_counts - 1, 0)
            if self.move_counts >= self.frame_rate:
                if not self.isWriting:
                    self.isWriting = True
                    str_t = time.strftime('%Y%m%d_%H%M%S.avi', time.localtime())
                    new_dir = os.path.join(self.out_dir, str_t)
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    fh, fw, cha = frame.shape
                    print(f"\nsave at: {new_dir, (fw, fh)}")
                    self.out = cv2.VideoWriter(new_dir, fourcc, int(self.frame_rate),
                                               (int(fw), int(fh)), True)
                self.out.write(frame)
        else:
            self.move_counts = max(self.move_counts - 1, 0)
            self.stop_counts += 1
            if self.stop_counts >= self.frame_rate:
                self.close_output()
        pass

    def close_output(self):
        self.stop_counts = 0
        self.isWriting = False
        if self.out is not None and self.out.isOpened():
            self.out.release()
        self.out = None

    @Slot()
    def set_terminate(self):
        self.close_output()
        print("output closed")
        self.signals.finished.emit()
