# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WeibospiderUserItem(scrapy.Item):
    # define the fields for your item here like:
    domain = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    followers_count = scrapy.Field()
    gender = scrapy.Field()
    province = scrapy.Field()
    city = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    created_at = scrapy.Field()
    avatar_img = scrapy.Field()
    verified_type = scrapy.Field()
    verified_detail_key = scrapy.Field()
    verified_detail_desc = scrapy.Field()
    avatar_img = scrapy.Field()
    statuses_count = scrapy.Field()
    friends_count = scrapy.Field()
    pass


# domain为关注的人，即id->domain
# domain = -1表示该节点为所选节点的关注节点
def json2item(json, domain):
    item = WeibospiderUserItem()
    item['domain'] = domain
    item['id'] = json['id']
    item['name'] = json['name']
    item['gender'] = json['gender']
    item['followers_count'] = json['followers_count']
    item['province'] = int(json['province'])
    item['city'] = int(json['city'])
    item['location'] = json['location']
    item['verified_type'] = json['verified_type']
    if json['verified_type'] == 0:
        item['verified_detail_key'] = [d['key'] for d in json['verified_detail']['data']]
        item['verified_detail_desc'] = [d['desc'] for d in json['verified_detail']['data']]
    else:
        item['verified_detail_key'] = []
        item['verified_detail_desc'] = []

    item['description'] = json['description']
    item['created_at'] = json['created_at']
    item['avatar_img'] = json['avatar_hd']
    item['statuses_count'] = json['statuses_count']
    item['friends_count'] = json['friends_count']
    return item
