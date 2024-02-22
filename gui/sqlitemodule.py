import sqlite3
import os

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