import PySide6
from PySide6.QtCore import Qt
from PySide6.QtWidgets import  QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QPushButton, QLabel
import json

class Settings:
    def __init__(self):
        self.settings = {
            'proxy_enabled': False,
            'proxy': '',
            'database_path': '1.db',
            "check_video_while_start": False,
        }

    def __getitem__(self, key):
        return self.settings[key]

    def load_settings_from_file(self):
        try:
            with open('settings.json', 'r') as file:
                localsettings = json.load(file)
                for key in self.settings.keys():
                    self.settings[key] = localsettings.get(key, self.settings[key])
        except FileNotFoundError:
            self.save_settings_to_file()
            pass

    def save_settings_to_file(self):
        with open('settings.json', 'w') as file:
            json.dump(self.settings, file)

class SettingsWindow(QWidget):
    def __init__(self,settings, save_settings_callback=None):
        super().__init__()
        #self.setParent(parent)

        self.save_settings_callback = save_settings_callback
        self.settings = Settings()
        self.settings.load_settings_from_file()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('settings')
        self.setGeometry(200, 200, 300, 200)


        self.allsettings = {}

        layout = QVBoxLayout()
        self.setLayout(layout)
        for option,value in self.settings.settings.items():
            sublayout = QHBoxLayout()
            sublayout.setAlignment(Qt.AlignmentFlag.AlignJustify)
            if type(value) == bool:
                settingswidget = QCheckBox(option)
                settingswidget.setChecked(value)
                sublayout.addWidget(settingswidget)
            
            else:
                settingswidget = QLineEdit(value)
                optionlabel = QLabel(option)
                sublayout.addWidget(optionlabel)
                sublayout.addWidget(settingswidget)
            self.allsettings[option] = settingswidget
            layout.addLayout(sublayout)
        savebutton = QPushButton('Save')
        savebutton.clicked.connect(self.save_settings)
        layout.addWidget(savebutton)

    def save_settings(self):
        for option,widget in self.allsettings.items():
            if type(widget) == QCheckBox:
                self.settings.settings[option] = widget.isChecked()
            elif type(widget) == QLineEdit:
                self.settings.settings[option] = widget.text()
        self.settings.save_settings_to_file()
        if self.save_settings_callback:
            self.save_settings_callback(self.settings)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    settings_window = SettingsWindow(Settings())
    settings_window.show()
    app.exec()