# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os

# from sqlobject import *

from py2neo import Graph
from WeiboSpider.WeiboSpider.NeoUtil import NeoUtil

class WeibospiderPipeline(object):

    graph = None

    def open_spider(self, spider):
        # 连接数据库
        # graph = Graph('http://localhost:7474', username='neo4j', password='123456') # 旧版本
        self.graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
        print(os.path)
        # 删除所有已有节点
        NeoUtil.clear()

    def process_item(self, item, spider):
        NeoUtil.try_add_node(item)


    def close_spider(self, spider):
        pass
