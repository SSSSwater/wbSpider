# Scrapy settings for WeiboSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from .RequestUtil import cookies_m,cookies_p,get_fake_weibo_UA,get_fake_chrome_UA

BOT_NAME = "WeiboSpider"

SPIDER_MODULES = ["WeiboSpider.spiders"]
NEWSPIDER_MODULE = "WeiboSpider.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 100

# 基础重试配置
RETRY_ENABLED = False  # 禁止重试
# RETRY_TIMES = 3       # 最大重试次数（默认2次）
# RETRY_HTTP_CODES = [500, 502, 503, 504, 404, 403]  # 需要重试的HTTP状态码
# RETRY_PRIORITY_ADJUST = 0  # 每次重试优先级调整（避免重复请求阻塞队列）

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8
DOWNLOAD_DELAY = 1  # 下载延迟
RANDOMIZE_DOWNLOAD_DELAY = True  # 随机化下载延迟
DOWNLOAD_TIMEOUT = 1  # 下载超时时间

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:

DEFAULT_REQUEST_HEADERS = {'authority': 'weibo.com',
                           'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
                           'cookie': cookies_p,
                           'accept':
                               'application/json,text/plain,*/*', 'referer': 'https://weibo.com/'
                           }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "WeiboSpider.middlewares.WeibospiderSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {

    # 'WeiboSpider.middlewares.ProxyMiddleware': 543,
    "WeiboSpider.middlewares.ErrorLoggerMiddleware": 545,
   "WeiboSpider.middlewares.WeibospiderDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy.extensions.corestats.CoreStats': 0,
    'scrapy.extensions.memusage.MemoryUsage': 0,
    'scrapy.extensions.logstats.LogStats': 0,
    'scrapy.extensions.feedexport.FeedExporter': 0,
    'scrapy.extensions.spiderstate.SpiderState': 0,
    'scrapy.extensions.throttle.AutoThrottle': 0,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "WeiboSpider.pipelines.WeibospiderPipeline": 200,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0
AUTOTHROTTLE_MAX_DELAY = 3
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [401, 403, 404, 500, 502, 503, 504]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
IMAGES_STORE = "./images"

# Redis 地址
REDIS_URL = 'redis://localhost:6379'

# Scrapy-Redis 配置
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER_PERSIST = True
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderPriorityQueue'


# 重定向设置
REDIRECT_ENABLED = True  # 允许重定向
REDIRECT_MAX_TIMES = 5  # 最大重定向次数

# 其他设置
AJAXCRAWL_ENABLED = True  # 启用AJAX爬取
REACTOR_THREADPOOL_MAXSIZE = 10  # 线程池大小
DNS_TIMEOUT = 10  # DNS超时时间

# 日志设置
LOG_LEVEL = 'INFO'  # 日志级别
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'  # 日志格式
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# 启用内存使用限制
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 4096
MEMUSAGE_WARNING_MB = 2048

# 启用统计信息
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'
STATS_DUMP = True

# 保存未检验代理的Redis key
PROXIES_UNCHECKED_LIST = 'proxies:unchecked:list'

# 已经存在的未检验HTTP代理和HTTPS代理集合
PROXIES_UNCHECKED_SET = 'proxies:unchecked:set'