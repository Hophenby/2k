import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver import EdgeService, EdgeOptions, ChromeService, ChromeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager 
from webdriver_manager.chrome import ChromeDriverManager 


PROXY_HOST = "http://localhost:7890"


def get_video_info(video_id,driver:webdriver.Edge,proxy=None):
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


    return video_info


def get_videos_info(video_ids,proxy_mode=False,proxy_host=None,proxy_port=None):
    options=EdgeOptions()
    proxy=Proxy()
    if proxy_mode:
        proxy.proxy_type=ProxyType.MANUAL
        proxy.http_proxy=f"{proxy_host}:{proxy_port}"
        #options=ChromeOptions()
        options.add_argument("--proxy-server={}".format(f"{proxy_host}:{proxy_port}"))
    driver = webdriver.Edge(options=options,service=EdgeService(executable_path=EdgeChromiumDriverManager().install()))
    try:

        videos_info=[]
        for video_id in video_ids:
            video_info=get_video_info(video_id,driver,proxy)
            if video_info:
                videos_info.append(video_info)
    finally:
        driver.quit()


    return videos_info

#print(get_videos_info(["sm34711325"],True,"http://localhost",7890))