import json
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

    # 并发设置
    custom_settings = {
        'CONCURRENT_REQUESTS': 32,  # 全局并发请求数
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,  # 每个域名的并发请求数
        'CONCURRENT_REQUESTS_PER_IP': 8,  # 每个IP的并发请求数
        'DOWNLOAD_DELAY': 0.5,  # 下载延迟
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # 随机化下载延迟
        'COOKIES_ENABLED': False,  # 禁用cookies
        'RETRY_ENABLED': True,  # 启用重试
        'RETRY_TIMES': 3,  # 重试次数
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429],  # 需要重试的HTTP状态码
        'DOWNLOAD_TIMEOUT': 15,  # 下载超时时间
        'REDIRECT_ENABLED': True,  # 允许重定向
        'REDIRECT_MAX_TIMES': 5,  # 最大重定向次数
        'AJAXCRAWL_ENABLED': True,  # 启用AJAX爬取
        'REACTOR_THREADPOOL_MAXSIZE': 20,  # 线程池大小
        'DNS_TIMEOUT': 10,  # DNS超时时间
        'LOG_LEVEL': 'INFO',  # 日志级别
    }

    # 配置日志
    configure_logging(install_root_handler=False)

    with open('scrapy_log.txt','w') as f:
        f.write(f"日志初始化")
    logging.basicConfig(
        filename='scrapy_log.txt',
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        level=logging.INFO
    )

    def __init__(self, user_id=None, *args, **kwargs):
        super(WeiboSpider, self).__init__(*args, **kwargs)
        self.user_id = user_id if user_id else 6593199887  # 默认值
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
        # if self.request_count > 0 and self.request_count == self.completed_count:
        #     logging.info("所有请求已完成")
        #     if self.idle_count >= self.MAX_IDLE_COUNT:
        #         logging.info("爬虫任务完成，准备关闭")
        #         self.crawler.engine.close_spider(self, '任务完成')

    def start_requests(self):
        """初始化爬虫，从初始用户开始"""
        logging.info("开始初始化爬虫")
        RedisQueueManager.clear_task()
        RedisQueueManager.set_status(1)
        NeoUtil.add_main_node(self.user_id)

        RedisQueueManager.set_status(2)
        # 获取初始用户列表
        start_list = get_following_all(self.user_id)
        logging.info(f"获取到 {len(start_list)} 个初始用户")
        
        # 批量添加用户到Neo4j

        for u in start_list:
            NeoUtil.try_add_node(u)
        RedisQueueManager.set_status(3)
        batch_size = 100
        for i in range(0, len(start_list), batch_size):
            batch = start_list[i:i + batch_size]
            for u in batch:
                logging.info(f"开始爬取用户 {u['name']}({u['id']}) 的粉丝列表")
                yield scrapy.Request(
                    url=self.url_sample.format(1, u['id']),
                    callback=self.parse,
                    meta={
                        'page': 1,
                        'domain': u['id'],
                        'depth': 1,
                        'current_user': u['id'],
                        'priority': 100,
                        'retry_times': 0
                    },
                    priority=100,
                    dont_filter=True
                )

    def parse(self, response):
        """解析粉丝列表页面"""
        try:
            datas = json.loads(response.text)
        except json.JSONDecodeError:
            logging.error(f"JSON解析错误: {response.status} - {response.url}")
            return
        except Exception as e:
            logging.error(f"解析错误: {str(e)} - {response.url}")
            return

        if datas['ok'] != 1:
            logging.error(f"API返回错误: {response.status} - {response.url}")
            return

        try:
            users = datas['data']['list']['users']
        except KeyError:
            logging.error(f"数据格式错误: {response.url}")
            return

        current_user = response.meta['current_user']
        current_page = response.meta.get('page', 1)
        current_depth = response.meta.get('depth', 1)
        
        logging.info(f"正在爬取用户 {current_user} 的第 {current_page} 页粉丝列表(深度:{current_depth})")

        if not users:
            logging.info(f"用户 {current_user} 的第 {current_page} 页没有更多粉丝")
            return

        # 统计当前页面有效用户数量
        next_page = False
        for user in users:
            # 保存用户数据到图数据库
            yield json2item(user, response.meta['domain'])
            
            if user['followers_count'] >= self.FANS_THRESHOLD:
                next_page = True
                # 如果深度允许，创建新的爬取任务
                if response.meta.get('depth', 1) < self.MAX_DEPTH:
                    with open("scrapy_log.txt", 'a') as log:
                        logging.info(f"将用户 {user['name']}({user['id']}) 加入队列(粉丝数:{user['followers_count']}, 深度:{response.meta.get('depth', 1) + 1})\n")
                    yield scrapy.Request(
                        url=self.url_sample.format(1, user['id']),
                        meta={
                            'page': 1,
                            'domain': user['id'],
                            'depth': current_depth + 1,
                            'current_user': user['id'],
                            'priority': 20,
                            'retry_times': 0
                        },
                        callback=self.parse,
                        priority=20
                    )
            else:
                with open("scrapy_log.txt", 'a') as log:
                    logging.info(f"用户 {user['name']}({user['id']}) 粉丝数 {user['followers_count']} 小于阈值，跳过\n")
                next_page = False
                break

        # 判断是否继续爬取下一页
        if next_page:
            with open("scrapy_log.txt", 'a') as log:
                logging.info(f"用户 {response.meta['current_user']} 的第 {response.meta.get('page', 1)} 页粉丝数都大于阈值，继续爬取下一页\n")
            yield scrapy.Request(
                url=self.url_sample.format(current_page + 1, current_user),
                meta={
                    'page': current_page + 1,
                    'domain': current_user,
                    'depth': current_depth,
                    'current_user': current_user,
                    'priority': response.meta['priority'] + 1,
                    'retry_times': 0
                },
                callback=self.parse,
                priority=response.meta['priority'] + 1
            )
        else:
            logging.info(f"用户 {current_user} 的第 {current_page} 页最后一个粉丝数未超过阈值，停止爬取")

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
