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
