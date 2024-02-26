import sqlite3
import os
import sys
import asyncio
import time
from qasync import QEventLoop, asyncClose, asyncSlot
import threading
from PySide6.QtCore import Qt, QTimer, QMimeData, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QPaintEvent, QPixmap, QClipboard, QTextDocument, QDesktopServices, QPainter, QColor, QBrush
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QCheckBox, 
    QHBoxLayout, 
    QScrollArea, 
    QToolTip,
    QMessageBox, 
    QSpacerItem, 
    QSizePolicy,
    QComboBox,
    )
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


def gen_img_html(img:QPixmap):
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buffer, "PNG")
    base64_data = byte_array.toBase64().data().decode()
    return f"<img src='data:image/png;base64,{base64_data}'/>"

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
            img_element = gen_img_html(self.thumbnail)
            QToolTip.showText(event.globalPos(), img_element)
            
class SearchResultWidget(QWidget):
    def __init__(self,video_info:dict,settings=None):
        super().__init__()

        #self.hide()
        self.settings = settings

        self.video_info = video_info

        self.thumbnail = QPixmap()

        self.video_id_label = QLabel(video_info["video_id"])
        self.video_id_label.setObjectName("video_id_label")
        self.video_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
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
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.scroll_area.setFixedHeight(100)

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

        self.open_website_button = QPushButton("Open Website")
        self.open_website_button.clicked.connect(self.open_website)

        thumbnail_layout = QVBoxLayout()
        thumbnail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        thumbnail_layout.addWidget(self.video_id_label)
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
        layout.addWidget(self.open_website_button)

        del_layout = QVBoxLayout()
        del_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        del_layout.addSpacerItem(QSpacerItem(24,0,QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Expanding))
        del_button = QPushButton("Delete")
        del_button.clicked.connect(self.del_from_db)
        del_layout.addWidget(del_button)
        layout.addLayout(del_layout)

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

    def paintEvent(self, event: QPaintEvent) -> None:
        
        '''painter = QPainter(self)
        painter.setBrush(QColor(235,235,255,255))
        painter.drawRoundedRect(self.rect(), 10, 10)'''

        return super().paintEvent(event)

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

    def open_website(self):
        QDesktopServices.openUrl(f"https://www.nicovideo.jp/watch/{self.video_info['video_id']}")

        pass

    def del_from_db(self):
        check = QMessageBox.question(self, "Delete", "Are you sure you want to delete this video from the database?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if check == QMessageBox.StandardButton.Yes:
            database=self.settings.settings["database_path"]
            conn = sqlite3.connect(database)
            c = conn.cursor()
            c.execute("DELETE FROM videos WHERE video_id = ?", (self.video_info["video_id"],))
            c.execute("DELETE FROM tags WHERE video_id = ?", (self.video_info["video_id"],))
            conn.commit()
            conn.close()
            self.close()

class DateSelector(QWidget):
    def __init__(self,additional_text=""):
        super().__init__()

        self.additional_text = QLabel(f"{additional_text}")
        self.additional_text.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Preferred)
        self.additional_text.setFixedWidth(60)

        self.year_combo = QComboBox()
        self.month_combo = QComboBox()
        self.day_combo = QComboBox()

        self.year_combo.addItems([str(i) for i in range(2007,2025)])
        self.year_combo.setCurrentIndex(17)
        self.year_combo.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Preferred)
        self.year_combo.setFixedWidth(80)

        self.month_combo.addItems([str(i) for i in range(1,13)])
        self.month_combo.setCurrentIndex(0)
        self.month_combo.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Preferred)
        self.month_combo.setFixedWidth(40)
        self.month_combo.currentIndexChanged.connect(self.update_day_combo)

        self.day_combo.addItems([str(i) for i in range(1,32)])
        self.day_combo.setCurrentIndex(0)
        self.day_combo.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Preferred)
        self.day_combo.setFixedWidth(40)

        self.timelayout = QHBoxLayout()
        self.timelayout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.timelayout.addWidget(self.additional_text)
        self.timelayout.addWidget(self.year_combo)
        self.timelayout.addWidget(QLabel("-"))
        self.timelayout.addWidget(self.month_combo)
        self.timelayout.addWidget(QLabel("-"))
        self.timelayout.addWidget(self.day_combo)

        self.setLayout(self.timelayout)

    def get_date(self):
        date=time.strptime(f"{self.year_combo.currentText()}-{self.month_combo.currentText()}-{self.day_combo.currentText()}","%Y-%m-%d")
        return date
    
    def update_day_combo(self):
        self.day_combo.clear()
        month = int(self.month_combo.currentText())
        if month in [1,3,5,7,8,10,12]:
            self.day_combo.addItems([str(i) for i in range(1,32)])
        elif month in [4,6,9,11]:
            self.day_combo.addItems([str(i) for i in range(1,31)])
        elif month == 2:
            year = int(self.year_combo.currentText())
            if year%4==0:
                if year%100==0:
                    if year%400==0:
                        self.day_combo.addItems([str(i) for i in range(1,30)])
                    else:
                        self.day_combo.addItems([str(i) for i in range(1,29)])
                else:
                    self.day_combo.addItems([str(i) for i in range(1,30)])
            else:
                self.day_combo.addItems([str(i) for i in range(1,29)])
        self.day_combo.setCurrentIndex(0)

class UploadDateFilter(QWidget):
    def __init__(self):
        super().__init__()
        self.enable_date_filter_check = QCheckBox("Date Filter")
        self.enable_date_filter_check.setChecked(False)
        self.enable_date_filter_check.stateChanged.connect(self.toggle_date_filter)

        self.date_selector_from = DateSelector("From:")
        self.date_selector_from.setVisible(False)
        self.date_selector_to = DateSelector("To:")
        self.date_selector_to.setVisible(False)

        self.date_layout = QVBoxLayout()
        self.date_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.date_layout.addWidget(self.enable_date_filter_check)
        self.date_layout.addWidget(self.date_selector_from)
        self.date_layout.addWidget(self.date_selector_to)

        self.setLayout(self.date_layout)

    def toggle_date_filter(self):
        if self.enable_date_filter_check.isChecked():
            self.date_selector_from.setVisible(True)
            self.date_selector_to.setVisible(True)
        else:
            self.date_selector_from.setVisible(False)
            self.date_selector_to.setVisible(False)

    def get_date_filter(self):
        if self.enable_date_filter_check.isChecked():
            return (self.date_selector_from.get_date(),self.date_selector_to.get_date())
        else:
            return None


        


        

class DatabaseSearchWindow(QMainWindow):
    def __init__(self,settings=None):
        super().__init__()
        self.setWindowTitle("222")
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
        checkboxes_objnames=["video_id","title","description","user_name","tag"]
        self.checkboxes={}
        checkboxes_layout = QVBoxLayout()
        for name,objname in zip(checkboxes_names,checkboxes_objnames):
            checkbox = QCheckBox(name)
            checkbox.setObjectName(objname)
            checkboxes_layout.addWidget(checkbox)
            self.checkboxes[objname]=checkbox

        self.date_filter = UploadDateFilter()

        self.search_state = QLabel("idle")
        
        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_input)

        search_button_and_checkboxes_layout = QHBoxLayout()
        search_button_and_checkboxes_layout.addLayout(checkboxes_layout)
        search_button_and_checkboxes_layout.addWidget(self.date_filter)
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
        
    @asyncSlot()
    async def search_database_from_info(self):
        self.search_state.setText("Searching...")
        self.search_button.setEnabled(False)
        time1 = time.time()
        try:
            # Get search query from input field
            query = self.search_input.text()
            
            if self.result_layout.count() > 0:
                for i in reversed(range(self.result_layout.count())):
                    self.result_layout.itemAt(i).widget().setParent(None)
            # Execute search query
            
            def search_thread():
                
                # Connect to SQLite database
                conn = sqlite3.connect("videos.db")
                cursor = conn.cursor()
                try:
                    results=[]

                    date_filter = self.date_filter.get_date_filter()
                    commands_and=[]
                    commands_or=[]
                    if date_filter is not None:
                        commands_and.append(f"upload_year*10000+upload_month*100+upload_day >= {date_filter[0].tm_year*10000+date_filter[0].tm_mon*100+date_filter[0].tm_mday} AND upload_year*10000+upload_month*100+upload_day <= {date_filter[1].tm_year*10000+date_filter[1].tm_mon*100+date_filter[1].tm_mday}")
                    for name,checkbox in self.checkboxes.items():
                        if checkbox.isChecked():
                            if name=="tag":
                                commands_or.append(f"video_id IN (SELECT video_id FROM tags WHERE tag LIKE '%{query}%')")
                                #cursor.execute(f"SELECT * FROM videos WHERE video_id IN (SELECT video_id FROM tags WHERE tag LIKE '%{query}%')")
                            else:
                                commands_or.append(f"{name} LIKE '%{query}%'")
                                #cursor.execute(f"SELECT * FROM videos WHERE {name} LIKE '%{query}%'")
                    command=""
                    if len(commands_and)>0:
                        command+=" AND ".join(commands_and)
                    if len(commands_or)>0:
                        if len(command)>0:
                            command+=" AND "
                        command+=f"({' OR '.join(commands_or)})"


                    if len(command)>0:
                        results=cursor.execute(f"SELECT * FROM videos WHERE {command}").fetchall()


                    results_new=[]
                    for video_info in results:
                        keys=["video_id","title","thumbnail_url","upload_year","upload_month","upload_day","upload_hour","upload_minute","upload_second","view_count","mylist_count","description","user_name","user_id"]
                        video_info=dict(zip(keys,video_info))
                        tags = cursor.execute(f"""SELECT tag FROM tags WHERE video_id = "{video_info['video_id']}" """).fetchall()
                        video_info["tags"]=[tag[0] for tag in tags]
                        results_new.append(video_info)
                except Exception as e:
                    print(e)
                    raise e
                finally:
                    # Close database connection
                    cursor.close()
                    conn.close()

                return results_new
            
            loop=asyncio.get_event_loop()
            results=await loop.run_in_executor(None,search_thread)
            time2 = time.time()
            
            # Display search results
            for video_info in results:
                result=SearchResultWidget(video_info,self.settings)
                self.result_layout.addWidget(result)
                
 
            self.search_state.setText("Finished. Found {} results".format(len(results)))
            time3 = time.time()
            print(f"search time: {time2-time1:.03f} display time: {time3-time2:.03f}")
        except Exception as e:
            self.search_state.setText("Error: " + str(e))
        finally:
            self.search_button.setEnabled(True)

    
    async def boot(self):
        pass

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    
    # Create the main window
    window=DatabaseSearchWindow()
    window.show()

    event_loop.create_task(window.boot())
    event_loop.run_until_complete(app_close_event.wait())
    event_loop.close()