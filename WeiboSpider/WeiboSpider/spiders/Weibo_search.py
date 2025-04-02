import scrapy



def cookies2dicts(s:str):
    cookie = {}
    for line in s.split(';'):
        key, value = line.split('=', 1)
        cookie[key] = value
    return cookie

class WeiboSearchSpider(scrapy.Spider):
    name = "Weibo_search"
    allowed_domains = ["s.weibo.com"]
    key = "双减"
    url_sample = "https://s.weibo.com/weibo?q={}"
    start_urls = [url_sample.format(key)]
    cookies_str = "PC_TOKEN=1e450ef6ab; XSRF-TOKEN=Vxo1WCeFZys9dOEy-Is6XGI3; SL_G_WPT_TO=zh; SL_GWPT_Show_Hide_tmp=1; SL_wptGlobTipTmp=1; SCF=AiX32jEzYrtjOHSIAig0Z6JSN2-xiPD-voGyLWUWbqJlzb-qodBdMzqjWGV2Pek4vzXFm-vK256JPO9DhhkJYuQ.; SUB=_2A25KfRu6DeRhGeFJ6FcW8SzOzD6IHXVp8xFyrDV8PUNbmtANLRLBkW9NfAwZGx-oYe9OQrUDHhaKkAXv_Wq_hmoJ; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; ALF=02_1738602730; WBPSESS=iPpPH-JXjxwdk8QJixaFMEjvAgRG9EsjuPpPGdJQryPuThMN_DFYLleLoYKHvieXhr9XFWPNKxZ5huEBYGD7Xvp76eE5aep4RkOZ8oY8RYp-xi7CdN-b-lHfdVXbCMq6lRC9qmZW3WyXEaJQ35vKew=="
    headers = {'authority': 'weibo.com',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
               'referer': 'https://weibo.com/u/page/follow/5880246144',
               'cookie': cookies_str}
    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0],headers=self.headers, callback=self.parse)

    def parse(self, response):
        print(response.text)
