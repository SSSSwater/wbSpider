import json
import os.path
import time

import scrapy
from scrapy_redis.spiders import RedisSpider
from ..items import WeibospiderUserItem
from fake_useragent import UserAgent
from collections import deque
import redis
from ..subcribe import subscribe_one, test_available
import copy


class WeiboSpider(RedisSpider):
    name = "WeiboUser"
    # allowed_domains = ["weibo.com"]
    url_sample = "https://m.weibo.cn/c/fans/followers?page={}&uid={}&cursor=-1&count=100"
    current_page = 1
    user_id = 6593199887
    redis_key = 'db:start_urls'
    # start_urls = [url_sample.format(current_page,user_id)]
    ua = UserAgent()

    q = deque()
    # cookies_str = ""
    # with open('cookies_mobile.txt', 'r') as f:
    #     cookies_str = f.read()

    # headers = {'authority': 'weibo.com',
    #            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    #            'referer': 'https://weibo.com/u/page/follow/{}?relate=fans'.format(user_id),
    #            'cookie':cookies_str}

    def start_requests(self):
        yield scrapy.Request(url=self.url_sample.format(1, self.user_id), callback=self.parse,
                             meta={'page': 1, 'domain': self.user_id})

    def parse(self, response):

        if response.status != 200:
            with open("err_log.txt", 'a') as err:
                err.write(response.status + ":\n" + response.text)
            time.sleep(2)
            yield scrapy.Request(url=self.url_sample.format(response.meta['page'], response.meta['domain']),
                                 meta={'page': response.meta['page'], 'domain': response.meta['domain']},
                                 callback=self.parse, dont_filter=True)
        else:
            try:
                datas = json.loads(response.text)
            except Exception:
                with open("err_log.txt", 'a') as err:
                    err.write(response.status + ":\n" + response.text)
            if datas['ok'] != 1:
                with open("err_log.txt", 'a') as err:
                    err.write(response.status + ":\n" + response.text)
            else:
                # 获取到数据
                list
                try:
                    users: list = datas['data']['list']['users']
                except Exception:
                    with open("err_log.txt", 'a') as err:
                        err.write(response.status + ":\n" + response.text)
                next_page = True
                if users:
                    for d in users:

                        if d['followers_count'] >= 10000000:
                            item = WeibospiderUserItem()
                            item['domain'] = response.meta['domain']
                            item['id'] = d['id']
                            item['name'] = d['name']
                            item['gender'] = d['gender']
                            item['followers_count'] = d['followers_count']
                            item['province'] = d['province']
                            item['city'] = d['city']
                            item['location'] = d['location']
                            item['description'] = d['description']
                            item['created_at'] = d['created_at']
                            item['avatar_img'] = d['avatar_hd']

                            # self.q.append(d['id'])

                            yield item
                            # if not test_available(d['id']):
                            #     print("我将关注\n\n\n")
                            # subscribe_one(d['id'])

                            with open("scrapy_log.txt", 'a') as log:
                                log.write("将`" + item['name'] + "`的第1页加入队列(粉丝数:"+ str(item['followers_count']) + ")\n")
                            yield scrapy.Request(url=self.url_sample.format(1, d['id']),
                                                 meta={'page': 1, 'domain': d['id']},
                                                 callback=self.parse)
                        else:
                            next_page = False
                            break
                    # yield scrapy.Request(url=self.url_sample.format(1,
                # self.current_page += 1
                if next_page:
                    with open("scrapy_log.txt", 'a',encoding='utf-8') as log:
                        log.write("将下一页(第" + response.meta['page'] + 1 + "页)加入队列\n")
                    yield scrapy.Request(url=self.url_sample.format(response.meta['page'] + 1, response.meta['domain']),
                                         meta={'page': response.meta['page'] + 1, 'domain': response.meta['domain']},
                                         callback=self.parse)

            # else:
            #     if self.q:
            #         self.user_id = self.q.popleft()
            #         yield scrapy.Request(url=self.url_sample.format(1, self.user_id),
            #                              callback=self.parse)
        # else:
        #     yield scrapy.Request(url=self.url_sample.format(1, id),
        #                          callback=self.parse, dont_filter=True)
