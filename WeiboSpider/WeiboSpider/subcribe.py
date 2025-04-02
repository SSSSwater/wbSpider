import json

import requests

cookies_str = ""
with open('cookies.txt', 'r') as f:
    cookies_str = f.read()


def test_available(id):
    headers = {'authority': 'weibo.com',
               'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
               'referer': 'https://weibo.com/u/' + str(id),
               'cookie': cookies_str,
               'accept':
                   'application/json,text/plain,*/*'
               }
    response = requests.get("https://weibo.com/ajax/friendships/friends?&page=1&uid={}".format(id), headers=headers)
    if json.loads(response.text)['ok'] == 1:
        return True
    else:
        return False


def subscribe_one(id):
    headers = {'authority': 'weibo.com',
               'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
               'referer': 'https://weibo.com/u/' + str(id),
               'cookie': cookies_str,
               'accept':
                   'application/json,text/plain,*/*'
               }
    data = {"friend_uid":id,"page":"profile","lpage":"profile"}
    response = requests.post("https://weibo.com/ajax/friendships/create",
                             json=data, headers=headers)
