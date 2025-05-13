import copy
import json
import random
from copy import deepcopy

import scrapy
from scrapy_redis.spiders import RedisSpider
from ..items import json2item
from fake_useragent import UserAgent
import redis
from ..RedisUtil import RedisQueueManager
from ..RequestUtil import get_following_all
from ..NeoUtil import NeoUtil
from scrapy.utils.log import configure_logging
import logging
from scrapy.exceptions import IgnoreRequest
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import time
from scrapy import signals
from scrapy.signalmanager import dispatcher
from ..CommonUtils import *

class WeiboSpider(RedisSpider):
    name = "WeiboUser"
    # allowed_domains = ["weibo.com"]
    first_get_sample = "https://www.weibo.com/ajax/friendships/friends?page={}&uid={}"
    # pc端爬取关注
    url_sample = "https://www.weibo.com/ajax/friendships/friends?page={}&uid={}"
    # app端爬取粉丝
    # url_sample = "https://m.weibo.cn/c/fans/followers?page={}&uid={}&cursor=-1&count=20"
    current_page = 1
    redis_key = 'db:start_urls'
    ua = UserAgent()
    MAX_DEPTH = 1  # 设置最大爬取深度
    FANS_THRESHOLD = 2000000  # 粉丝数阈值
    FRIENDS_THRESHOLD = 150  # 关注数阈值
    SELECT_USER_PROBABILITY = 0.8  # 每个符合要求的用户有多少概率爬取
    SKIP_PAGE_PROBABILITY = 0.2  # 有多少概率跳过下一个关注页不爬取

    # 配置日志
    configure_logging(install_root_handler=False)

    with open('scrapy_log.txt','w') as f:
        f.write(f"日志初始化\n")
    logging.basicConfig(
        filename='scrapy_log.txt',
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        level=logging.INFO
    )


    def __init__(self, user_id=None, target_num=None, *args, **kwargs):
        super(WeiboSpider, self).__init__(*args, **kwargs)
        RedisQueueManager.clear_task()
        self.user_id = user_id if user_id else 6593199887  # 默认值
        self.target_num = target_num if target_num else 10  # 默认值
        self.stats = {}
        self.start_time = time.time()
        self.request_count = 0
        self.completed_count = 0
        self.is_idle = False
        self.idle_count = 0
        self.MAX_IDLE_COUNT = 10  # 最大空闲次数
        
        # 注册信号处理器
        dispatcher.connect(self.spider_idle, signal=signals.spider_idle)
        dispatcher.connect(self.request_scheduled, signal=signals.request_scheduled)
        dispatcher.connect(self.response_received, signal=signals.response_received)

    def request_scheduled(self, request, spider):
        """请求被调度时的处理"""
        self.request_count += 1
        logging.info(f"请求已调度: {request.url}")

    def response_received(self, response, request, spider):
        """收到响应时的处理"""
        self.completed_count += 1
        logging.info(f"请求已完成: {request.url}")

    def spider_idle(self, spider):
        """爬虫空闲时的处理"""
        if not self.is_idle:
            self.is_idle = True
            self.idle_count = 0
            logging.info("爬虫进入空闲状态")

        self.idle_count += 1
        logging.info(f"爬虫空闲次数: {self.idle_count}")

        # 检查是否所有请求都已完成
        if self.request_count > 0 and self.request_count == self.completed_count:
            logging.info("所有请求已完成")
            if self.idle_count >= self.MAX_IDLE_COUNT:
                logging.info("爬虫任务完成，准备关闭")
                self.crawler.engine.close_spider(self, '任务完成')

    def start_requests(self):
        """初始化爬虫，从初始用户开始"""
        logging.info("开始初始化爬虫")
        RedisQueueManager.set_status(1)
        NeoUtil.add_main_node(self.user_id)

        RedisQueueManager.set_status(2)
        # 获取初始用户列表
        start_list = get_following_all(self.user_id)
        logging.info(f"获取到 {len(start_list)} 个初始用户")
        selected_start = try_sample_from_list(start_list, self.target_num)

        # 批量添加用户到Neo4j
        for u in selected_start:
            NeoUtil.try_add_node(u)
            logging.info(f"添加用户 {u['name']}({u['id']}) 的关注列表")
            yield scrapy.Request(
                url=self.url_sample.format(1, u['id']),
                callback=self.parse,
                meta={
                    'page': 1,
                    'domain': u['id'],
                    'dapth': 1,
                    'current_user': u['id'],
                    'priority': 100,
                    'retry_times': 0
                },
                priority=100,
                dont_filter=True
            )
        RedisQueueManager.set_status(3)
        # batch_size = 100
        # for i in range(0, len(start_list), batch_size):
        #     batch = start_list[i:i + batch_size]
        #     for u in batch:
        #

    def parse(self, response):
        """解析粉丝列表页面"""
        try:
            datas = json.loads(response.text)
        except json.JSONDecodeError:
            logging.error(f"JSON解析错误，可能cookies已失效: {response.status} - {response.url}")
            return
        except Exception as e:
            logging.error(f"解析错误，未知原因: {str(e)} - {response.url}")
            return

        if datas['ok'] != 1:
            logging.error(f"API返回错误，可能用户禁止了非关注用户访问粉丝列表: {response.status} - {response.url}")
            return
        try:
            # 爬取粉丝列表时使用
            # users = datas['data']['list']['users']
            # 爬取关注列表时使用
            users = datas['users']
        except KeyError:
            logging.error(f"数据格式错误: {response.url}")
            return

        current_user = response.meta['current_user']
        current_page = response.meta['page']
        current_depth = response.meta['dapth']
        current_domain = response.meta['domain']
        current_priority = response.meta['priority']
        
        logging.info(f"正在爬取用户 {current_user} 的第 {current_page} 页关注列表")

        if not users:
            logging.info(f"用户 {current_user} 的第 {current_page} 页没有更多关注")
            return

        add_queue = True
        if current_depth > self.MAX_DEPTH:
            logging.info(f"用户 {current_user} 关注页深度 {current_depth} 达到上限，不将该页用户加入队列)")
            add_queue = False

        next_page = False
        for user in users:
            next_page = True
            if user['followers_count'] < self.FANS_THRESHOLD:
                continue

            # 保存用户数据到图数据库
            yield json2item(user, current_domain)

            if user['friends_count'] > self.FANS_THRESHOLD:
                continue
            if not rand_probability(self.SELECT_USER_PROBABILITY):
                continue
            # 如果条件都允许，创建新的爬取任务
            if add_queue:
                logging.info(f"将用户 {user['name']}({user['id']}) 加入队列")
                yield scrapy.Request(
                    url=self.url_sample.format(1, user['id']),
                    meta={
                        'page': 1,
                        'domain': user['id'],
                        'dapth': current_depth + 1,
                        'current_user': user['id'],
                        'priority': 100 - (current_depth - 1) * 20,
                        'retry_times': 0
                    },
                    callback=self.parse,
                    priority= 100 - (current_depth - 1) * 20
                )

        # 判断是否继续爬取下一页
        if next_page:
            page_add = 1
            f = True
            while(f):
                if rand_probability(self.SKIP_PAGE_PROBABILITY):
                    page_add += 1
                else:
                    f = False
            logging.info(f"用户 {current_user} 的第 {current_page} 页关注已爬取完毕，继续往后爬取{page_add}页")
            yield scrapy.Request(
                url=self.url_sample.format(current_page + 1, current_user),
                meta={
                    'page': current_page + page_add,
                    'domain': current_user,
                    'dapth': current_depth,
                    'current_user': current_user,
                    'priority': 100 - (current_depth - 1) * 20 + current_page,
                    'retry_times': 0
                },
                callback=self.parse,
                priority= 100 - (current_depth - 1) * 20 + current_page,
            )
    def closed(self, reason):
        """爬虫关闭时的处理"""
        end_time = time.time()
        duration = end_time - self.start_time
        RedisQueueManager.set_status(0)
        logging.info(f"爬虫运行完成，总耗时: {duration:.2f}秒")
        logging.info(f"关闭原因: {reason}")
        logging.info(f"总请求数: {self.request_count}")
        logging.info(f"完成请求数: {self.completed_count}")
        logging.info(f"空闲次数: {self.idle_count}")
