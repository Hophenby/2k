import re, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver import EdgeService, EdgeOptions, ChromeService, ChromeOptions, FirefoxService, FirefoxOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager 
from webdriver_manager.chrome import ChromeDriverManager 
from webdriver_manager.firefox import GeckoDriverManager


PROXY_HOST = "http://localhost:7890"

class VideoInfo:
    def __init__(self, video_id, title, thumbnail_url, upload_year, upload_month, upload_day, upload_hour, upload_minute, upload_second, view_count, mylist_count, description, tags, user_name, user_id):
        self.video_id = video_id
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.upload_year = upload_year
        self.upload_month = upload_month
        self.upload_day = upload_day
        self.upload_hour = upload_hour
        self.upload_minute = upload_minute
        self.upload_second = upload_second
        self.view_count = view_count
        self.mylist_count = mylist_count
        self.description = description
        self.tags = tags
        self.user_name = user_name
        self.user_id = user_id

    @classmethod
    def from_dict(cls, video_dict):
        return cls(video_dict["video_id"], video_dict["title"], video_dict["thumbnail_url"], video_dict["upload_year"], video_dict["upload_month"], video_dict["upload_day"], video_dict["upload_hour"], video_dict["upload_minute"], video_dict["upload_second"], video_dict["view_count"], video_dict["mylist_count"], video_dict["description"], video_dict["tags"], video_dict["user_name"], video_dict["user_id"])
    
    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return {
            "video_id": self.video_id,
            "title": self.title,
            "thumbnail_url": self.thumbnail_url,
            "upload_year": self.upload_year,
            "upload_month": self.upload_month,
            "upload_day": self.upload_day,
            "upload_hour": self.upload_hour,
            "upload_minute": self.upload_minute,
            "upload_second": self.upload_second,
            "view_count": self.view_count,
            "mylist_count": self.mylist_count,
            "description": self.description,
            "tags": self.tags,
            "user_name": self.user_name,
            "user_id": self.user_id
        }

def get_video_info(video_id,driver:webdriver.Chrome):
    video_info={}
    try:
        #print(f"processing video {video_id}")
        driver.get(f"https://www.nicozon.net/watch/{video_id}")


        watch_content_element = driver.find_element(By.XPATH, '//div[@id="watch-content"]')
        ul_elements = watch_content_element.find_elements(By.XPATH, '//ul[@class="inline-ul"]')
        '''for i, ul_element in enumerate(ul_elements):
            print(f"taglist {i}: {ul_element.text}")'''

        #print()

        video_info["video_id"]=video_id
        
        title_element = driver.find_element(By.XPATH, '//h1[@id="title"]')
        #print(f"title: {title_element.text}")
        video_info["title"]=title_element.text
        

        img_element = driver.find_element(By.XPATH, '//img[contains(@src, "nicovideo.cdn.nimg.jp/thumbnails/")]')
        #print(len(thumbnail_elements))
        url = img_element.get_attribute("src")
        #print(f"thumbnail url: {url}")
        video_info["thumbnail_url"]=url

        infolist=ul_elements[1].find_elements(By.CSS_SELECTOR, "li")
        matched_time = re.match((r"^(\d{4})/(\d{2})/(\d{2}) (\d{2}):(\d{2}):(\d{2}) 投稿$"), infolist[0].text)
        if matched_time:
            #print(f"upload time: {matched_time.group(1)}-{matched_time.group(2)}-{matched_time.group(3)} {matched_time.group(4)}:{matched_time.group(5)}:{matched_time.group(6)}")
            video_info["upload_year"]=int(matched_time.group(1))
            video_info["upload_month"]=int(matched_time.group(2))
            video_info["upload_day"]=int(matched_time.group(3))
            video_info["upload_hour"]=int(matched_time.group(4))
            video_info["upload_minute"]=int(matched_time.group(5))
            video_info["upload_second"]=int(matched_time.group(6))

        view_count = re.search(r'\d+',infolist[1].text).group()
        mylist_count = re.search(r'\d+',infolist[2].text).group()
        #print(f"view count: {view_count}")
        #print(f"mylist count: {mylist_count}")
        video_info["view_count"]=int(view_count)
        video_info["mylist_count"]=int(mylist_count)

        watch_discription_element = driver.find_element(By.XPATH, '//div[@class="watch-description"]')
        #print(f"description: {watch_discription_element.text}")
        video_info["description"]=watch_discription_element.text
                            
        taglist=ul_elements[2].find_elements(By.CLASS_NAME, "tagname")
        #print(f"tag count: {len(taglist)}")
        '''for tag in taglist:
            print(f"tag name: {tag.text}")
            try:
                tag_url = tag.get_attribute("href")
                print(f"tag url: {tag_url}")
            except:
                print("no url")'''
        video_info["tags"]=[tag.text for tag in taglist]
        
        driver.get(f"https://www.nicovideo.jp/watch/{video_id}")

        user_name_element = driver.find_element(By.XPATH, '//a[@class="Link" and contains(@href, "/user/")]')
        #print(f"user name: {user_name_element.text}")
        video_info["user_name"]=user_name_element.get_attribute("title").rstrip(" さん")

        user_id = user_name_element.get_attribute("href").lstrip("https://www.nicovideo.jp/user/")
        #print(f"user id: {user_id}")
        video_info["user_id"]=user_id
        
    except Exception as e:
        print(f"error occured while processing video {video_id}")
        print(f"{e.__class__.__name__}: {e}")
        video_info=None
                
    '''finally:
        driver.quit()'''


    return VideoInfo.from_dict(video_info)


def get_user_page_video(user_id,driver:webdriver.Chrome):
    video_ids=[]
    try:
        driver.get(f"https://www.nicovideo.jp/user/{user_id}/video")
        nickname_element = driver.find_element(By.XPATH, '//h3[@class="UserDetailsHeader-nickname"]')
        nickname = nickname_element.text
        video_elements = driver.find_elements(By.XPATH, "//div[@data-video-thumbnail-comment-hover='true' and contains(@class, 'NC-MediaObject')]")
        for video_element in video_elements:
            id_element = video_element.find_element(By.CLASS_NAME, "NC-Link")
            video_id = re.search(r"sm\d{6,9}", str(id_element.get_attribute("href"))).group()

            title_element = video_element.find_element(By.CLASS_NAME, "NC-MediaObjectTitle").text

            registered_at = video_element.find_element(By.CLASS_NAME, "NC-VideoRegisteredAtText-text").text
            registered_at = re.match(r"(\d{4})/(\d{1,2})/(\d{1,2}) (\d{1,2}):(\d{2})", registered_at).groups()

            timestamp = datetime.datetime(int(registered_at[0]), int(registered_at[1]), int(registered_at[2]), int(registered_at[3]), int(registered_at[4])).timestamp()
            timestamp = int(timestamp)

            video_ids.append({"video_id": video_id, "timestamp": timestamp, "title": title_element})
    except Exception as e:
        print(f"error occured while processing user {user_id}")
        print(f"{e.__class__.__name__}: {e}")
        video_ids=None
        nickname=None
        
    return nickname,video_ids


def get_videos_info(video_ids,proxy_mode=False,proxy_server=None):
    options=EdgeOptions()
    #options=FirefoxOptions()
    #options=ChromeOptions()
    options.add_argument("--headless")
    proxy=Proxy()
    if proxy_mode:
        proxy.proxy_type=ProxyType.MANUAL
        proxy.http_proxy=f"{proxy_server}"
        options.add_argument("--proxy-server={}".format(f"{proxy_server}"))
    driver = webdriver.Edge(options=options,service=EdgeService(executable_path=EdgeChromiumDriverManager().install()))
    #driver = webdriver.Firefox(options=options,service=FirefoxService(executable_path=GeckoDriverManager().install()))
    #driver = webdriver.Chrome(options=options,service=ChromeService(executable_path=ChromeDriverManager().install()))
    try:

        videos_info=[]
        for video_id in video_ids:
            try:
                video_info=get_video_info(video_id,driver)
                if video_info:
                    videos_info.append(video_info)
            except Exception as e:
                print(f"error occured while processing video {video_id}")
                print(f"{e.__class__.__name__}: {e}")
    finally:
        driver.quit()


    return videos_info

def get_users_videos(user_ids,proxy_mode=False,proxy_server=None):
    options=EdgeOptions()
    #options=FirefoxOptions()
    #options=ChromeOptions()
    options.add_argument("--headless")
    proxy=Proxy()
    if proxy_mode:
        proxy.proxy_type=ProxyType.MANUAL
        proxy.http_proxy=f"{proxy_server}"
        options.add_argument("--proxy-server={}".format(f"{proxy_server}"))
    driver = webdriver.Edge(options=options,service=EdgeService(executable_path=EdgeChromiumDriverManager().install()))
    #driver = webdriver.Firefox(options=options,service=FirefoxService(executable_path=GeckoDriverManager().install()))
    #driver = webdriver.Chrome(options=options,service=ChromeService(executable_path=ChromeDriverManager().install()))
    try:

        users_videos=[]
        for user_id in user_ids:
            user_videos={}
            user_name,video_ids=get_user_page_video(user_id,driver)
            if video_ids:
                user_videos["user_name"]=user_name
                user_videos["video_ids"]=video_ids
                user_videos["user_id"]=user_id
                users_videos.append(user_videos)
    finally:
        driver.quit()


    return users_videos

if __name__ == "__main__":
    print(get_videos_info(["sm34711325"],True,"http://localhost:7890"))
    print(get_users_videos(["66296951"],True,"http://localhost:7890"))