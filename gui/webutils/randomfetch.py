import re, datetime, random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver import EdgeService, EdgeOptions, ChromeService, ChromeOptions, FirefoxService, FirefoxOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager 
from webdriver_manager.chrome import ChromeDriverManager 
from webdriver_manager.firefox import GeckoDriverManager

from webfetch import *

TAGS=["お洒落なミクうた","初音ミクオリジナル曲","やさしいミクうた","かわいいミクうた","ミクトロニカ"]

WHITELIST_TAGS=["VOCALOID"]
BLACKLIST_TAGS=["ニコカラ","vocaloidカバー曲","歌ってみた","ニコカラDB"]

class RandomFetcher:
    def __init__(self, proxy_mode=False,proxy_server=None):
        self.proxy_mode=proxy_mode
        self.proxy_server=proxy_server
        self.init_driver()

    def init_driver(self):
        
        #options=EdgeOptions()
        #options=FirefoxOptions()
        options=ChromeOptions()
        proxy=Proxy()
        if self.proxy_mode:
            proxy.proxy_type=ProxyType.MANUAL
            proxy.http_proxy=f"{self.proxy_server}"
            options.add_argument("--proxy-server={}".format(f"{self.proxy_server}"))
        #driver = webdriver.Edge(options=options,service=EdgeService(executable_path=EdgeChromiumDriverManager().install()))
        #driver = webdriver.Firefox(options=options,service=FirefoxService(executable_path=GeckoDriverManager().install()))
        driver = webdriver.Chrome(options=options,service=ChromeService(executable_path=ChromeDriverManager().install()))
        driver.minimize_window()
        self.driver=driver

    def random_fetch(self):
        driver=self.driver
        random_page=random.randint(1,15)
        random_tag=random.choice(TAGS)
        page=f"https://www.nicovideo.jp/tag/{random_tag}?page={random_page}&sort=f&order=d"
        driver.get(page)
    
