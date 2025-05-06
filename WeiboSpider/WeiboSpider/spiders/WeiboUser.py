import json

import scrapy
from scrapy_redis.spiders import RedisSpider
from ..items import json2item
from fake_useragent import UserAgent
import redis
from WeiboSpider.WeiboSpider.RedisUtil import RedisQueueManager
from WeiboSpider.WeiboSpider.RequestUtil import get_following_all
from WeiboSpider.WeiboSpider.NeoUtil import NeoUtil


class WeiboSpider(RedisSpider):
    name = "WeiboUser"
    # allowed_domains = ["weibo.com"]
    first_get_sample = "https://www.weibo.com/ajax/friendships/friends?page={}&uid={}"
    url_sample = "https://m.weibo.cn/c/fans/followers?page={}&uid={}&cursor=-1&count=20"
    current_page = 1
    redis_key = 'db:start_urls'
    ua = UserAgent()
    MAX_DEPTH = 1  # 设置最大爬取深度
    FANS_THRESHOLD = 5000000  # 粉丝数阈值
    MIN_VALID_USERS = 5  # 每页最少需要有多少个有效用户才继续爬取

    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

    # cookies_str = ""
    # with open('cookies_mobile.txt', 'r') as f:
    #     cookies_str = f.read()

    # headers = {'authority': 'weibo.com',
    #            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    #            'referer': 'https://weibo.com/u/page/follow/{}?relate=fans'.format(user_id),
    #            'cookie':cookies_str}

    def __init__(self, user_id=None, *args, **kwargs):
        super(WeiboSpider, self).__init__(*args, **kwargs)
        self.user_id = user_id if user_id else 6593199887  # 默认值

    def start_requests(self):
        """初始化爬虫，从初始用户开始"""
        with open("scrapy_log.txt", 'w') as log:
            log.write("")
        RedisQueueManager.clear_task()
        NeoUtil.add_main_node(self.user_id)
        
        # 获取初始用户列表
        start_list = get_following_all(self.user_id)
        with open("scrapy_log.txt", 'a') as log:
            log.write(f"获取到 {len(start_list)} 个初始用户\n")
        
        # 为每个初始用户创建爬取任务，深度为1
        for u in start_list:
            NeoUtil.try_add_node(u)
            with open("scrapy_log.txt", 'a') as log:
                log.write(f"开始爬取用户 {u['name']}({u['id']}) 的粉丝列表\n")
            yield scrapy.Request(
                url=self.url_sample.format(1, u['id']),
                callback=self.parse,
                meta={
                    'page': 1,
                    'domain': u['id'],
                    'depth': 1,
                    'current_user': u['id'],  # 记录当前正在爬取的用户
                    'priority': 100
                },
                priority=100
            )

    def parse(self, response):
        """解析粉丝列表页面"""
        datas = {'ok': 0}
        try:
            datas = json.loads(response.text)
        except Exception:
            with open("err_log.txt", 'a') as err:
                err.write(str(response.status) + ":\n" + response.text)
            return

        if datas['ok'] != 1:
            with open("err_log.txt", 'a') as err:
                err.write(str(response.status) + ":\n" + response.text)
            return

        try:
            users = datas['data']['list']['users']
        except Exception:
            with open("err_log.txt", 'a') as err:
                err.write(str(response.status) + ":\n" + response.text)
            return


        with open("scrapy_log.txt", 'a') as log:
            log.write(f"正在爬取用户 {response.meta['current_user']} 的第 {response.meta.get('page', 1)} 页粉丝列表(深度:{response.meta.get('depth', 1)})\n")

        if not users:
            with open("scrapy_log.txt", 'a') as log:
                log.write(f"用户 {response.meta['current_user']} 的第 {response.meta.get('page', 1)} 页没有更多粉丝\n")
            return

        # 统计当前页面有效用户数量
        next_page = False
        for user in users:
            # 保存用户数据到图数据库
            yield json2item(user, response.meta['domain'])
            
            # 统计有效用户数量
            if user['followers_count'] >= self.FANS_THRESHOLD:
                next_page = True
                # 如果深度允许，创建新的爬取任务
                if response.meta.get('depth', 1) < self.MAX_DEPTH:
                    with open("scrapy_log.txt", 'a') as log:
                        log.write(f"将用户 {user['name']}({user['id']}) 加入队列(粉丝数:{user['followers_count']}, 深度:{response.meta.get('depth', 1) + 1})\n")
                    yield scrapy.Request(
                        url=self.url_sample.format(1, user['id']),
                        meta={
                            'page': 1,
                            'domain': user['id'],
                            'depth': response.meta.get('depth', 1) + 1,
                            'current_user': user['id'],
                            'priority': 20
                        },
                        callback=self.parse,
                        priority=20
                    )
            else:
                with open("scrapy_log.txt", 'a') as log:
                    log.write(f"用户 {user['name']}({user['id']}) 粉丝数 {user['followers_count']} 小于阈值，跳过\n")
                next_page = False
                break

        # 判断是否继续爬取下一页
        if next_page:
            with open("scrapy_log.txt", 'a') as log:
                log.write(f"用户 {response.meta['current_user']} 的第 {response.meta.get('page', 1)} 页粉丝数都大于阈值，继续爬取下一页\n")
            yield scrapy.Request(
                url=self.url_sample.format(response.meta.get('page', 1) + 1, response.meta['current_user']),
                meta={
                    'page': response.meta.get('page', 1) + 1,
                    'domain': response.meta['current_user'],
                    'depth': response.meta.get('depth', 1),  # 保持当前深度不变
                    'current_user': response.meta['current_user'],
                    'priority': response.meta['priority'] + 1
                },
                callback=self.parse,
                priority=response.meta['priority'] + 1  # 同一用户的下一页优先级较高
            )
        else:
            with open("scrapy_log.txt", 'a') as log:
                log.write(f"用户 {response.meta['current_user']} 的第 {response.meta.get('page', 1)} 页出现粉丝数小于阈值的用户，停止爬取该用户的后续页面\n")
