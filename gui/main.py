import asyncio
import sys

# from PyQt6.QtWidgets import (
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QPixmap
from qasync import QEventLoop, asyncClose, asyncSlot
import webfetch


PROXY_HOST = "http://localhost"
PROXY_PORT = 7890

class MainWindow(QWidget):
    """Main window."""

    _DEF_URL: str = ""
    """Default URL."""

    def __init__(self):
        super().__init__()

        self.setLayout(QVBoxLayout())

        self.lbl_status = QLabel("Idle", self)
        self.layout().addWidget(self.lbl_status)

        self.edit_url = QLineEdit(self._DEF_URL, self)
        self.layout().addWidget(self.edit_url)

        self.edit_response = QLabel(self)
        self.layout().addWidget(self.edit_response)
        self.edit_response_text = QTextEdit("", self)
        self.layout().addWidget(self.edit_response_text)

        self.btn_fetch = QPushButton("Fetch", self)
        self.btn_fetch.clicked.connect(self.on_btn_fetch_clicked)
        self.layout().addWidget(self.btn_fetch)


    @asyncClose
    async def closeEvent(self, event):  # noqa:N802
        pass

    async def boot(self):
        pass

    @asyncSlot()
    async def on_btn_fetch_clicked(self):
        self.btn_fetch.setEnabled(False)
        self.lbl_status.setText("Fetching...")

        try:
            video_ids = self.edit_url.text().split()
            loop=asyncio.get_event_loop()
            info_list=await loop.run_in_executor(None,webfetch.get_videos_info,video_ids,True,PROXY_HOST,PROXY_PORT)
            self.edit_response_text.setText(str(info_list))

        except Exception as exc:
            self.lbl_status.setText("Error: {}".format(exc))
        else:
            self.lbl_status.setText("Finished!")
        finally:
            self.btn_fetch.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    
    main_window = MainWindow()
    main_window.show()

    event_loop.create_task(main_window.boot())
    event_loop.run_until_complete(app_close_event.wait())
    event_loop.close()
     