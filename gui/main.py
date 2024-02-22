import asyncio
import sys
import re

# from PyQt6.QtWidgets import (
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QMenuBar,
    QMenu,
    QScrollArea
)
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtCore import QByteArray
from qasync import QEventLoop, asyncClose, asyncSlot
import webfetch,settings,sqlitemodule


PROXY_HOST = "http://localhost"
PROXY_PORT = 7890

class MainWindow(QMainWindow):
    """Main window."""

    _DEF_URL: str = ""
    """Default URL."""

    def __init__(self):
        super().__init__()
        self.initial_profile_settings()
        self.initUI()

    def initial_profile_settings(self):
        self.pf_settings = settings.Settings()
        self.pf_settings.load_settings_from_file()
        self.settings_window = None
        self.database_window = None

    def initUI(self):
        """Initialize the UI."""
        self.setWindowTitle("111")
        self.setGeometry(200, 200, 1000, 500)
        CentralWidget = QWidget()
        CentralWidget.setLayout(QVBoxLayout())
        self.setCentralWidget(CentralWidget)

        self.edit_url = QLineEdit(self._DEF_URL, self)
        self.btn_fetch = QPushButton("Fetch", self)
        self.edit_response_text = QScrollArea(self)
        self.lbl_status = QLabel("Idle", self)

        scroll_widget = QWidget()
        self.scroll_widget_layout = QVBoxLayout()
        scroll_widget.setLayout(self.scroll_widget_layout)
        self.edit_response_text.setWidget(scroll_widget)
        self.edit_response_text.setWidgetResizable(True)
        

        layout = CentralWidget.layout()
        layout.addWidget(self.edit_url)
        layout.addWidget(self.btn_fetch)
        layout.addWidget(self.edit_response_text)
        layout.addWidget(self.lbl_status)


        self.btn_fetch.clicked.connect(self.on_btn_fetch_clicked)

        menubar=self.menuBar()
        file_menu = menubar.addMenu('file')
        settings_action = QAction('settings',self)
        settings_action.triggered.connect(self.open_settings_window)
        file_menu.addAction(settings_action)

        database_menu = menubar.addMenu('database')
        database_action = QAction('open database',self)
        database_action.triggered.connect(self.open_database)
        database_menu.addAction(database_action)

    def open_settings_window(self):
        print("settings")
        if self.settings_window is not None:
            self.settings_window.close()
        self.settings_window = settings.SettingsWindow(self.pf_settings,self.update_settings)
        self.settings_window.show()
    
    def open_database(self):
        print("database")
        if self.database_window is not None:
            self.database_window.close()
        self.database_window = sqlitemodule.DatabaseSearchWindow()
        self.database_window.show()
        pass
        
    def update_settings(self,settings:settings.Settings):
        self.pf_settings=settings

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
            video_ids = re.findall(r"(?:sm\d{6,9}|so\d{6,9})", self.edit_url.text())
            loop=asyncio.get_event_loop()
            info_list=await loop.run_in_executor(None,webfetch.get_videos_info,video_ids,self.pf_settings["proxy_enabled"],self.pf_settings["proxy"])
            for info in info_list:
                self.search_result_widget = sqlitemodule.SearchResultWidget(info)
                self.scroll_widget_layout.addWidget(self.search_result_widget)
                sqlitemodule.insert_video_info(info,self.pf_settings["database_path"])
                

        except Exception as exc:
            self.lbl_status.setText(f"{exc.__class__.__name__}: {exc}")
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
     