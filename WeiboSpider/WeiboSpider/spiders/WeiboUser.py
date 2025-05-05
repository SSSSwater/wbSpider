import json
import os.path
import time
from datetime import datetime

import scrapy
from scrapy_redis.spiders import RedisSpider
from ..items import WeibospiderUserItem,json2item
from fake_useragent import UserAgent
from collections import deque
import redis
from ..subcribe import subscribe_one, test_available
import copy
from ..Util.RedisUtil import RedisQueueManager
from ..Util.RequestUtil import get_following_all
from ..Util.NeoUtil import NeoUtil

class WeiboSpider(RedisSpider):


    name = "WeiboUser"
    # allowed_domains = ["weibo.com"]
    first_get_sample = "https://www.weibo.com/ajax/friendships/friends?page={}&uid={}"
    url_sample = "https://m.weibo.cn/c/fans/followers?page={}&uid={}&cursor=-1&count=20"
    current_page = 1
    user_id = 6593199887
    redis_key = 'db:start_urls'
    # start_urls = [url_sample.format(current_page,user_id)]
    ua = UserAgent()

    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    # cookies_str = ""
    # with open('cookies_mobile.txt', 'r') as f:
    #     cookies_str = f.read()

    # headers = {'authority': 'weibo.com',
    #            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    #            'referer': 'https://weibo.com/u/page/follow/{}?relate=fans'.format(user_id),
    #            'cookie':cookies_str}

    def start_requests(self):
        with open("scrapy_log.txt", 'w') as log:
            log.write("")
        RedisQueueManager.clear_task()
        NeoUtil.add_main_node(self.user_id)
        start_list  = get_following_all(self.user_id)
        print(len(start_list))
        for u in start_list:
            NeoUtil.try_add_node(u)
            # yield u
            yield scrapy.Request(url=self.url_sample.format(1,self.user_id), callback=self.parse,
                         meta={'page': 1, 'domain': u['id'],'depth':1}, priority=1)
        # yield scrapy.Request(url=self.first_get_sample.format(1,self.user_id), callback=self.start_parse,meta={'page': 1},priority=100)
        # yield scrapy.Request(url=self.url_sample.format(1,self.user_id), callback=self.parse,
        #                  meta={'page': 1, 'domain': self.user_id}, priority=100)

    # def start_parse(self, response):
    #     datas = {'ok': 0}
    #     try:
    #         datas = json.loads(response.text)
    #     except Exception:
    #         with open("err_log.txt", 'a') as err:
    #             err.write(str(response.status) + ":\n" + response.text)
    #     if datas['ok'] != 1:
    #         with open("err_log.txt", 'a') as err:
    #             err.write(str(response.status) + ":\n" + response.text)
    #     else:
    #         users: list
    #         # 获取到数据
    #         try:
    #             users = datas['users']
    #         except Exception:
    #             with open("err_log.txt", 'a') as err:
    #                 err.write(str(response.status) + ":\n" + response.text)
    #
    #         # 检测是否有下一页
    #         next_page = False
    #         if users:
    #             next_page = True
    #             for d in users:
    #                 if d['followers_count'] >= 10000000:
    #                     yield json2item(d,-1)
    #                     with open("scrapy_log.txt", 'a') as log:
    #                         log.write("将`" + d['name'] + "`的第1页加入队列(粉丝数:" + str(
    #                             d['followers_count']) + ")\n")
    #                     yield scrapy.Request(url=self.url_sample.format(1, d['id']),
    #                                          meta={'page': 1, 'domain': d['id']},
    #                                          callback=self.parse, priority=1)
    #         if next_page:
    #             with open("scrapy_log.txt", 'a') as log:
    #                 log.write("将下一页(第" + str(response.meta['page'] + 1) + "页)加入队列\n")
    #             yield scrapy.Request(
    #                 url=self.first_get_sample.format(response.meta['page'] + 1, self.user_id),
    #                 meta={'page': response.meta['page'] + 1,},
    #                 callback=self.start_parse, priority=100)

    def parse(self, response):
        datas={'ok' : 0}
        try:
            datas = json.loads(response.text)
        except Exception:
            with open("err_log.txt", 'a') as err:
                err.write(str(response.status) + ":\n" + response.text)
        if datas['ok'] != 1:
            with open("err_log.txt", 'a') as err:
                err.write(str(response.status) + ":\n" + response.text)
        else:
            users:list
            # 获取到数据
            try:
                users = datas['data']['list']['users']
            except Exception:
                with open("err_log.txt", 'a') as err:
                    err.write(str(response.status) + ":\n" + response.text)

            #检测第一页粉丝数是否小于阈值的flag
            next_page = True
            if users:
                for d in users:

                    if d['followers_count'] >= 1000000:
                        yield json2item(d,response.meta['domain'])
                        if response.meta['depth'] <= 16:
                            with open("scrapy_log.txt", 'a') as log:
                                log.write("将`" + d['name'] + "`的第1页加入队列(粉丝数:"+ str(d['followers_count']) + ")\n")
                            yield scrapy.Request(url=self.url_sample.format(1, d['id']),
                                                 meta={'page': 1, 'domain': d['id'],'depth':response.meta['depth'] + 1},
                                                 callback=self.parse, priority=1)
                    else:
                        next_page = False
                        break
                # yield scrapy.Request(url=self.url_sample.format(1,
            # self.current_page += 1
            if next_page:
                with open("scrapy_log.txt", 'a') as log:
                    log.write("将下一页(第" + str(response.meta['page'] + 1) + "页)加入队列\n")
                yield scrapy.Request(url=self.url_sample.format(response.meta['page'] + 1, response.meta['domain']),
                                     meta={'page': response.meta['page'] + 1, 'domain': response.meta['domain'],'depth':response.meta['depth']},
                                     callback=self.parse,priority=response.meta['page'] + 1)

