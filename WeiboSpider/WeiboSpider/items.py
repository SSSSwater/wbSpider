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
    pass

def json2item(json):
    item = WeibospiderUserItem()
    item['id'] = json['id']
    item['name'] = json['name']
    item['gender'] = json['gender']
    item['followers_count'] = json['followers_count']
    item['province'] = int(json['province'])
    item['city'] = int(json['city'])
    item['location'] = json['location']
    item['description'] = json['description']
    item['created_at'] = json['created_at']
    item['avatar_img'] = json['avatar_hd']
    return item
