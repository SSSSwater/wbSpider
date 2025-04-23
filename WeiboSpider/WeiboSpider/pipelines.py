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
import requests
import pymysql
# from sqlobject import *
from scrapy.pipelines.images import ImagesPipeline

from py2neo import Graph, Subgraph, NodeMatcher
from py2neo import Node, Relationship, Path


class WeibospiderPipeline(object):

    graph = None

    def open_spider(self, spider):
        # 连接数据库
        # graph = Graph('http://localhost:7474', username='neo4j', password='123456') # 旧版本
        self.graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))

        # 删除所有已有节点
        self.graph.delete_all()

        rsrc = Node("User", id=6593199887, name="原神", gender='f')
        self.graph.create(rsrc)

        # self.db = pymysql.connect(host='localhost',
        #                           user='root',
        #                           password='123456',
        #                           database='weibo_data')
        # self.cursor = self.db.cursor()

    def process_item(self, item, spider):
        nodes = NodeMatcher(self.graph)

        domain = nodes.match("User", id=item['domain']).first()
        user:Node =None
        if not nodes.match("User", id=item['id']).exists():
            user = Node("User", id=item['id'], name=item['name'], gender=item['gender'],
                        followers_count=item['followers_count'], province=item['province'], city=item['city'],
                        location=item['location'], description=item['description'], created_at=item['created_at'],
                        avatar_img=item['avatar_img'])

            self.graph.create(user)
        else:
            user = nodes.match("User", id=item['id']).first()

        user_to_domain = Relationship(user, '关注',domain)
        self.graph.create(user_to_domain)
        # sql = """INSERT IGNORE INTO user_data( `id`,
        #          `name`, `gender`, `followers_counts`, `province`, `city, `location`, `description`, `created_at`, `avatar_img`)
        #          VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');""".format(item['id'],
        #                                                                                         item['name'],
        #                                                                                         item['gender'],
        #                                                                                         item['followers_count'],
        #                                                                                         item['province'],
        #                                                                                         item['city'],
        #                                                                                         item['location'],
        #                                                                                         item['description'],
        #                                                                                         item['created_at'],
        #                                                                                         item['avatar_img'])
        # print(sql)
        # self.cursor.execute(sql)
        # self.db.commit()

    def close_spider(self, spider):
        pass
        # self.db.close()


class BaiduImagePipeline(object):
    IMAGES_STORE = get_project_settings().get('IMAGES_STORE')

    def process_item(self, item, spider):
        img = requests.get(item['imageLink'])
        IMAGES_STORE = get_project_settings().get('IMAGES_STORE')

        if not os.path.exists("images/" + spider.key):
            os.makedirs("images/" + spider.key)
        with open("images/" + spider.key + "/" + uuid.uuid4().hex + ".jpg", "wb") as f:
            f.write(img.content)
