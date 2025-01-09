import sys
from PySide6.QtWidgets import (
    QDialog,
    QApplication,
    QWidget,
    QDialogButtonBox,
    QVBoxLayout,
    QLabel,
    QLineEdit,
)


class RtspDialog(QDialog):
    # hi there
    '''
    use parent to indicate parent in Qt frame
    use ip to indicate (remote or local) video source
    '''
    def __init__(self, parent=None, ip=None):
        super(RtspDialog, self).__init__(parent)
        self.resize(800, 80)
        self.setWindowTitle("Rtsp Address Input")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.textInput = QLineEdit()
        self.textInput.setPlaceholderText("Enter rtsp address")
        if ip is not None:
            self.textInput.setText(ip)

        self.layout.addWidget(self.textInput)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def getEnteredText(self):
        return self.textInput.text()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = RtspDialog()
    mainWindow.show()
    result = app.exec()
