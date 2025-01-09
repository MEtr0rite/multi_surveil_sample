from PySide6.QtCore import Signal, QObject


class WorkerSignals(QObject):

    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress
    '''

    finished = Signal()
    received_image = Signal(object)
    processed_image = Signal(object)
    channel_established = Signal()
    cannot_open = Signal()
    # terminate_flag = Signal(int)

