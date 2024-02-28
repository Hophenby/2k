import asyncio
import sys
import re
import time,datetime

from qasync import QEventLoop, asyncClose, asyncSlot
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
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer

from webfetch import get_users_videos, get_videos_info
from settings import Settings
from videodb import db_execute,SearchResultWidget,insert_video_info,get_last_check_time_from_user_id,subscribe_or_desub_uploader

class NoticeMenu(QMenu):
    def __init__(self, parent=None, settings:Settings=None,display_area:QScrollArea=None):
        super().__init__("videocheck", parent)
        self.settings = settings
        self.check_action=QAction("Check for new videos")
        self.check_action.triggered.connect(self.check_for_new_videos)
        self.addAction(self.check_action)
        self.addSeparator()
        self.display_area = display_area
        self.videoMenus=[]

    @asyncSlot()
    async def check_for_new_videos(self):

        self.check_action.setEnabled(False)
        self.check_action.setText("Checking for new videos...")

        @db_execute()
        def get_subscribed_users(cursor=None,database=None):
            cursor.execute("SELECT user_id FROM subscribed_users")
            return cursor.fetchall()
        
        @db_execute(slot=lambda results,cursor=None: [{"video_id":result[1],"timestamp":result[2]} for result in results])
        def get_videos_by_user_id(cursor=None,database=None,user_id=None,from_time=None):
            cursor.execute("SELECT video_id FROM upload_history WHERE user_id=(?) AND upload_time>(?)",(user_id,from_time))
            return cursor.fetchall()
        
        try:
            database = self.settings['database_path']
            users = get_subscribed_users(database=database)
            eventloop = asyncio.get_event_loop()
            users_videos = await eventloop.run_in_executor(None,get_users_videos,[user[0] for user in users], self.settings['proxy_enabled'], self.settings['proxy'])
            if users_videos is not None:
                for user_videos in users_videos:
                    try:
                        user_name = user_videos["user_name"]
                        user_id = user_videos["user_id"]
                        saved_videos = get_videos_by_user_id(database=database,user_id=user_id)
                        timestamps=[video["timestamp"] for video in saved_videos]

                        video_ids = user_videos["video_ids"]
                        last_video_time = get_last_check_time_from_user_id(database=database,user_id=user_id)
                        new_videos = [video_id for video_id in video_ids if video_id["timestamp"] > last_video_time[0]]
                        if len(new_videos) > 0:
                            info_list = await eventloop.run_in_executor(None,get_videos_info,[video_id["video_id"] for video_id in video_ids], self.settings['proxy_enabled'], self.settings['proxy'])
                            if info_list is not None:
                                self.videoMenus.append(VideoMenu(user_name,info_list, parent=self, settings=self.settings,display_area=self.display_area))
                                self.addMenu(self.videoMenus[-1])
                        
                        subscribe_or_desub_uploader(database=database,user_id=user_id)
                        subscribe_or_desub_uploader(database=database,user_id=user_id)
                                
                    except Exception as exc:
                        print(f"{exc.__class__.__name__}: {exc}")

                pass
        except Exception as exc:
            print(f"{exc.__class__.__name__}: {exc}")

        self.check_action.setEnabled(True)
        self.check_action.setText("Check for new videos")

    
class VideoMenu(QMenu):
    def __init__(self,user_name, info_list, parent=None, display_area:QScrollArea=None,settings:Settings=None):
        self.settings = settings
        self.user_name = user_name
        self.info_list = info_list
        self.display_area = display_area
        self.action_list = []
        super().__init__(f"{user_name}", parent)
        for info in info_list:
            action=VideoAction(info, parent=self, display_area=self.display_area,settings=self.settings)
            self.addAction(action)
        
class VideoAction(QAction):
    def __init__(self,info, parent=None, display_area:QScrollArea=None,settings:Settings=None):
        self.settings = settings
        self.info = info
        self.display_area = display_area
        time_info=f'{info["upload_year"]}-{info["upload_month"]}-{info["upload_day"]} {info["upload_hour"]}:{info["upload_minute"]}'
        super().__init__(f'[{info["video_id"]}]{info["title"]}({time_info})', parent)
        self.triggered.connect(self.open_video)

    @asyncSlot()
    async def open_video(self):
        @db_execute()
        def insert_to_upload_history(cursor=None,database=None,video_id=None,user_id=None,upload_time=None):
            cursor.execute("INSERT INTO upload_history (video_id,user_id,upload_time) VALUES (?,?,?)", (video_id,user_id,upload_time))
        info=self.info
        upload_time=datetime.datetime(info["upload_year"],info["upload_month"],info["upload_day"],info["upload_hour"],info["upload_minute"]).timestamp()
        insert_to_upload_history(database=self.settings['database_path'],video_id=self.info["video_id"],user_id=self.info["user_id"],upload_time=int(upload_time))
        insert_button = QPushButton("Insert to database")
        insert_button.clicked.connect(lambda: insert_video_info(self.info,database=self.settings["database_path"]))
        self.display_area.widget().layout().addWidget(SearchResultWidget(self.info,self.settings,[insert_button]))
        
