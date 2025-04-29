# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import uuid

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
import scrapy
# from sqlobject import *
from scrapy.pipelines.images import ImagesPipeline

from py2neo import Graph, Subgraph, NodeMatcher
from py2neo import Node, Relationship, Path
import WeiboSpider.WeiboSpider.NeoUtil as NeoUtil

class WeibospiderPipeline(object):

    graph = None

    def open_spider(self, spider):
        # 连接数据库
        # graph = Graph('http://localhost:7474', username='neo4j', password='123456') # 旧版本
        self.graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
        print(os.path)
        # 删除所有已有节点
        self.graph.delete_all()

        rsrc = Node("User", id=6593199887, name="原神", gender='f')
        self.graph.create(rsrc)


    def process_item(self, item, spider):
        NeoUtil.try_add_node(item)


    def close_spider(self, spider):
        pass
