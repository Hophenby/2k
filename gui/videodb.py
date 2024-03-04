import sqlite3
import time, datetime
import os

from webutils.webfetch import VideoInfo
"""
import sys
import asyncio
from qasync import QEventLoop, asyncClose, asyncSlot
import threading
from PySide6.QtCore import QEvent, Qt, QTimer, QMimeData, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QCloseEvent, QMouseEvent, QPaintEvent, QPixmap, QClipboard, QTextDocument, QDesktopServices, QPainter, QColor, QBrush, QCursor
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
    QTextEdit,
    )
import requests"""


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
    c.execute('''CREATE TABLE IF NOT EXISTS memories
                 (video_id text, memory text, timestamp integer,primary key(video_id, timestamp))''')
    c.execute('''CREATE TABLE IF NOT EXISTS upload_history
                 (user_id text, video_id text, upload_time integer, primary key(user_id, video_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscribed_users
                 (user_id text primary key,last_check_time integer)''')
    conn.commit()
    conn.close()

def results_to_info(results,cursor=None):
    results_new=[]
    for video_info in results:
        keys=["video_id","title","thumbnail_url","upload_year","upload_month","upload_day","upload_hour","upload_minute","upload_second","view_count","mylist_count","description","user_name","user_id"]
        video_info=dict(zip(keys,video_info))
        tags = cursor.execute(f"""SELECT tag FROM tags WHERE video_id = "{video_info['video_id']}" """).fetchall()
        video_info["tags"]=[tag[0] for tag in tags]
        results_new.append(VideoInfo.from_dict(video_info))
    return (results_new)

def db_execute(slot=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            database = kwargs.get('database', None)
            if database is None:
                database = DATABASE
            if not os.path.exists(database):
                create_table(database)
            conn = sqlite3.connect(database)
            cursor = conn.cursor()
            kwargs['cursor'] = cursor
            print(f"executing {func.__name__}")
            try:
                result = func(*args, **kwargs)
                conn.commit()
            except Exception as e:
                print(f"error occured while executing {func.__name__}")
                print(f"{e.__class__.__name__}: {e}")
                result = None
            finally:
                cursor.close()
                conn.close()
            if slot is not None:
                slot(result,cursor=cursor)
            return result
        return wrapper
    return decorator

@db_execute()
def insert_video_info(video_info, database=None,cursor=None):
    cursor.execute("INSERT OR REPLACE INTO videos VALUES (:video_id, :title, :thumbnail_url, :upload_year, :upload_month, :upload_day, :upload_hour, :upload_minute, :upload_second, :view_count, :mylist_count, :description, :user_name, :user_id)", video_info.to_dict())
    for tag in video_info["tags"]:
        cursor.execute("INSERT OR REPLACE INTO tags VALUES (?, ?)", (video_info["video_id"], tag))
    print(f"inserted {video_info['video_id']}")

@db_execute()
def del_video_info(video_id, database=None,cursor=None):
    cursor.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
    cursor.execute("DELETE FROM tags WHERE video_id = ?", (video_id,))
    cursor.execute("DELETE FROM memories WHERE video_id = ?", (video_id,))

@db_execute()
def add_video_memories(video_id,memories,database=None,cursor=None):
    for memory in memories:
        cursor.execute("INSERT OR REPLACE INTO memories VALUES (?, ?, ?)", (video_id, memory["memory"], memory["timestamp"]))

@db_execute()
def del_video_memories_by_timestamp(video_id,timestamp,database=None,cursor=None):
    cursor.execute("DELETE FROM memories WHERE video_id = ? AND timestamp = ?", (video_id, timestamp))

@db_execute()
def is_uploader_subscribed(user_id, database=None,cursor=None):
    return cursor.execute("SELECT * FROM subscribed_users WHERE user_id = ?", (user_id,)).fetchone() is not None

@db_execute()
def get_last_check_time_from_user_id(user_id, database=None,cursor=None):
    return cursor.execute("SELECT last_check_time FROM subscribed_users WHERE user_id = ?", (user_id,)).fetchone()

@db_execute()
def subscribe_or_desub_uploader(user_id, database=None,cursor=None):
    if cursor.execute("SELECT * FROM subscribed_users WHERE user_id = ?", (user_id,)).fetchone() is not None:
        cursor.execute("DELETE FROM subscribed_users WHERE user_id = ?", (user_id,))
    else:
        now = int(datetime.datetime.now().timestamp())
        cursor.execute("INSERT OR REPLACE INTO subscribed_users VALUES (?, ?)", (user_id, now))

@db_execute(slot=results_to_info)
def get_saved_video_info_from_user_id(user_id, database=None,cursor=None):
    return cursor.execute("SELECT * FROM videos WHERE user_id = ?", (user_id,)).fetchall()

