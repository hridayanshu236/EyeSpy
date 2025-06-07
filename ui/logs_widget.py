from PyQt5.QtWidgets import QTextEdit

class LogsWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.append("Logs:\n")

    def log(self, message):
        self.append(message)
