# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os

# from sqlobject import *

from py2neo import Graph
from .NeoUtil import NeoUtil

class WeibospiderPipeline(object):

    graph = None

    def open_spider(self, spider):
        # 删除所有已有节点
        NeoUtil.clear()
        # pass

    def process_item(self, item, spider):
        NeoUtil.try_add_node(item)
        # pass


    def close_spider(self, spider):
        pass
