import sqlite3
import os
import sys
import threading
from PySide6.QtCore import Qt, QTimer, QMimeData, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QPaintEvent, QPixmap, QClipboard, QTextDocument
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QCheckBox, QHBoxLayout, QScrollArea, QToolTip
import requests


DATABASE = 'test1.db'

def create_table(database=None):
    if database is None:
        database = DATABASE
    if not os.path.exists(database):
        open(database, 'w').close()
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                 (video_id text primary key, title text, thumbnail_url text, upload_year integer, upload_month integer, upload_day integer, upload_hour integer, upload_minute integer, upload_second integer, view_count integer, mylist_count integer, description text, user_name text, user_id text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tags
                 (video_id text, tag text, primary key(video_id, tag))''')
    conn.commit()
    conn.close()

def insert_video_info(video_info,database=None):
    if video_info is None:
        return
    if database is None:
        database = DATABASE
    if not os.path.exists(database):
        create_table(database)
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO videos VALUES (:video_id, :title, :thumbnail_url, :upload_year, :upload_month, :upload_day, :upload_hour, :upload_minute, :upload_second, :view_count, :mylist_count, :description, :user_name, :user_id)", video_info)
    for tag in video_info["tags"]:
        c.execute("INSERT OR REPLACE INTO tags VALUES (?, ?)", (video_info["video_id"], tag))
    conn.commit()
    conn.close()


class ThumbnailLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail = None

    def setThumbnail(self, thumbnail:QPixmap):
        self.thumbnail = thumbnail
        self.setPixmap(thumbnail.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))

    def enterEvent(self, event):
        if self.thumbnail is not None:
            #pixmap = QPixmap.fromImage(self.thumbnail)
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            self.thumbnail.save(buffer, "PNG")
            base64_data = byte_array.toBase64().data().decode()
            QToolTip.showText(event.globalPos(), "<img src='data:image/png;base64,{}'/>".format(base64_data))
            
class SearchResultWidget(QWidget):
    def __init__(self,video_info:dict,settings=None):
        super().__init__()

        #self.hide()
        self.settings = settings

        self.video_info = video_info

        self.thumbnail = QPixmap()

        
        self.title_label = QLabel(video_info["title"])
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.title_label.setObjectName("title_label")

        self.thumbnail_label = ThumbnailLabel()
        self.thumbnail_label.setThumbnail(self.thumbnail)
        #self.thumbnail_label.setPixmap(self.thumbnail.scaled(100,100,Qt.AspectRatioMode.KeepAspectRatio))
        self.thumbnail_label.setObjectName("thumbnail_label")
        threading.Thread(target=self.load_thumbnail).start()

        self.desc_label = QLabel(video_info["description"])
        self.desc_label.setWordWrap(True)
        self.desc_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.desc_label.setObjectName("desc_label")
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.desc_label)


        self.uploader_and_time_label = QLabel(f"Uploader: {video_info['user_name']}   ||  Time: {video_info['upload_year']}-{video_info['upload_month']}-{video_info['upload_day']} {video_info['upload_hour']:02}:{video_info['upload_minute']:02}:{video_info['upload_second']:02}")
        self.uploader_and_time_label.setObjectName("uploader_and_time_label")
        self.uploader_and_time_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self.tags_label = QLabel(f"Tags: {'    '.join(video_info['tags'])}")
        self.tags_label.setObjectName("tags_label")
        self.tags_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.tags_label.setWordWrap(True)

        self.misc_label = QLabel(f"Views: {video_info['view_count']} Mylist: {video_info['mylist_count']}")
        self.misc_label.setObjectName("misc_label")
        self.misc_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.copy_info_button = QPushButton("Copy Info")
        self.copy_info_button.clicked.connect(self.copy_info)

        thumbnail_layout = QVBoxLayout()
        thumbnail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        thumbnail_layout.addWidget(QLabel(video_info["video_id"]))
        thumbnail_layout.addWidget(self.thumbnail_label)
        
        sublayout = QVBoxLayout()
        sublayout.addWidget(self.title_label)
        sublayout.addWidget(self.scroll_area)
        sublayout.addWidget(self.uploader_and_time_label)
        sublayout.addWidget(self.tags_label)
        sublayout.addWidget(self.misc_label)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(thumbnail_layout)
        layout.addLayout(sublayout)
        layout.addWidget(self.copy_info_button)

        self.setLayout(layout)

        self.setStyleSheet("""
        #title_label{
            font-size: 15px;
            font-weight: bold;
        }
        #desc_label{
            color: gray;
            font-size: 12px;
        }
        #uploader_and_time_label{
            color: blue;
            font-size: 12px;
        }
        #tags_label{
            color: green;
            font-size: 12px;
        }
        #misc_label{
            font-size: 12px;
        }
        """)

    def load_thumbnail(self):
        if self.settings is not None and self.settings.settings['proxy_enabled']:
            image_data = requests.get(self.video_info["thumbnail_url"]+".L", proxies={"http": self.settings.settings['proxy'], "https": self.settings.settings['proxy']})
        else:
            image_data = requests.get(self.video_info["thumbnail_url"]+".L")
        if image_data.status_code == 200:
            self.thumbnail.loadFromData(image_data.content)
            self.thumbnail_label.setThumbnail(self.thumbnail)
            #self.show()

    def copy_info(self):
        #copy the video_id then the thumbnail then the title to the clipboard
        clipboard = QApplication.clipboard()

        
        mime_data = QMimeData()
        mime_data.setHtml(f"{self.video_info['video_id']}<br><img src='{self.video_info['thumbnail_url']}'><br>{self.video_info['title']}")

        QTimer.singleShot(100,lambda: clipboard.setMimeData(mime_data, mode=QClipboard.Mode.Clipboard))

        

class DatabaseSearchWindow(QMainWindow):
    def __init__(self,settings=None):
        super().__init__()
        self.setWindowTitle("Database Search")
        self.setGeometry(200, 200, 1000, 500)

        self.settings = settings
        
        # Create widgets
        self.search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Search")
        
        self.result_area = QScrollArea()
        self.result_area.setWidgetResizable(True)
        self.result_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        scroll_widget = QWidget()
        self.result_area.setWidget(scroll_widget)

        self.result_layout = QVBoxLayout(scroll_widget)
        #self.result_area.setLayout(self.result_layout)

        checkboxes_names=["id","title","description","uploader","tags"]
        self.checkboxes={}
        checkboxes_layout = QVBoxLayout()
        for name in checkboxes_names:
            checkbox = QCheckBox(name)
            checkboxes_layout.addWidget(checkbox)
            self.checkboxes[name]=checkbox

        self.search_state = QLabel("")
        
        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_input)

        search_button_and_checkboxes_layout = QHBoxLayout()
        search_button_and_checkboxes_layout.addLayout(checkboxes_layout)
        search_button_and_checkboxes_layout.addWidget(self.search_button)
        layout.addLayout(search_button_and_checkboxes_layout)
        layout.addWidget(self.result_area)
        layout.addWidget(self.search_state)
        
        # Create central widget and set layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Connect button click event to search function
        self.search_button.clicked.connect(self.search_database_from_info)
        
    def search_database_from_info(self):
        self.search_state.setText("Searching...")
        # Get search query from input field
        query = self.search_input.text()
        
        # Connect to SQLite database
        conn = sqlite3.connect("videos.db")
        cursor = conn.cursor()
        
        # Execute search query
        results=[]
        for name,checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                if name=="id":
                    cursor.execute(f"SELECT * FROM videos WHERE video_id LIKE '%{query}%'")
                elif name=="title":
                    cursor.execute(f"SELECT * FROM videos WHERE title LIKE '%{query}%'")
                elif name=="description":
                    cursor.execute(f"SELECT * FROM videos WHERE description LIKE '%{query}%'")
                elif name=="uploader":
                    cursor.execute(f"SELECT * FROM videos WHERE user_name LIKE '%{query}%'")
                elif name=="tags":
                    cursor.execute(f"SELECT * FROM videos WHERE video_id IN (SELECT video_id FROM tags WHERE tag LIKE '%{query}%')")
                results+=(cursor.fetchall())
                print(len(results))

        
        # Display search results
        if self.result_layout.count() > 0:
            for i in reversed(range(self.result_layout.count())):
                self.result_layout.itemAt(i).widget().setParent(None)
        
        for video_info in results:
            #print(video_info)
            keys=["video_id","title","thumbnail_url","upload_year","upload_month","upload_day","upload_hour","upload_minute","upload_second","view_count","mylist_count","description","user_name","user_id"]
            video_info=dict(zip(keys,video_info))
            tags = cursor.execute(f"""SELECT tag FROM tags WHERE video_id = "{video_info['video_id']}" """).fetchall()
            video_info["tags"]=[tag[0] for tag in tags]
            #print(video_info)
            self.result_layout.addWidget(SearchResultWidget(video_info,self.settings))

        
        # Close database connection
        cursor.close()
        conn.close()
        self.search_state.setText("Finished. Found {} results".format(len(results)))

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    window = DatabaseSearchWindow()
    window.show()

    # Run the event loop
    sys.exit(app.exec())
