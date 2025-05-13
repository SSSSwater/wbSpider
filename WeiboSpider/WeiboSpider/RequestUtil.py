import json
import os
import random

import requests
from .items import json2item
from fake_useragent import UserAgent


ua = UserAgent()
def get_fake_chrome_UA():
    return ua.chrome
def get_fake_weibo_UA():
    return ua.safari + " Weibo (Xiaomi-Redmi K60__weibo__15.2.0__android__android14)"
cookies_p = "SCF=ArocenNkCpg0L-tQtc2zwrlouksUjDWqD8rehjo-TJ4ODPiZggA6j4iTaEQe7KcPp6xpDvDbDRVBk0o8p2F6wFk.; SINAGLOBAL=2144935806551.7065.1743670926392; ULV=1743670926408:1:1:1:2144935806551.7065.1743670926392:; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5JpX5KMhUgL.FoMNe0-NeKzES0z2dJLoIp7LxKML1KBLBKnLxKqL1hnLBoMNS0efS02EeoME; ALF=1749175197; SUB=_2A25FHs7NDeRhGeFJ6FcW8SzOzD6IHXVmUk4FrDV8PUJbkNAbLVWskW1NfAwZG6H6ezKVvLVoxpQzqGOHZnG2x-XC; PC_TOKEN=337beb8769; XSRF-TOKEN=3zu1PN7Oix35_dsp3E-yMMEU; WBPSESS=iPpPH-JXjxwdk8QJixaFMEjvAgRG9EsjuPpPGdJQryPuThMN_DFYLleLoYKHvieXkgSxvT1swHLXNTeYgTx7rITAgyjJFRXV4M-BxqT4GXIyabbryoBiMkzpVLXQ8SDQBw4kb9EQq-9HAGKBtY9coQ=="
cookies_m = "SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; WEIBOCN_FROM=10E2195010; SUB=_2A25FFPVXDeRhGeFJ6FcW8SzOzD6IHXVmSaUfrDV6PUJbitAbLXbxkWtNfAwZG2f25TjBhGbfkQPXTP45l8ruM2nH; SCF=AiNI51DpEdPkbxxx7CPprSck-NKSIp7n81pSeWMff_GFc90kqQazjIjEpGGhb6Hfig..; _T_WM=66318150462; MLOGIN=1; M_WEIBOCN_PARAMS=from%3D10F2095010; XSRF-TOKEN=57a341; mweibo_short_token=5428639177"

headers_p = {'authority': 'www.weibo.com',
               'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
               'referer': 'https://weibo.com/u/page/follow/' + str(id),
               'cookie': cookies_p,
               'accept':
                   'application/json,text/plain,*/*'
               }
def test_mobile(page,uid):
    headers = {'authority': 'weibo.com',
               'User-Agent': get_fake_weibo_UA(),
               # 'User-Agent': "Mozilla/5.0 (Linux; Android 14; 23013RK75C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.260 Mobile Safari/537.36 Weibo (Xiaomi-Redmi K60__weibo__15.2.0__android__android14)",
               'referer': 'https://weibo.com/u/' + str(id),
               'cookie': cookies_m,
               'accept':
                   'application/json,text/plain,*/*'
               }
    response = requests.get("https://m.weibo.cn/c/fans/followers?page={}&uid={}&cursor=-1&count=20".format(page,uid), headers=headers)
    datas = json.loads(response.text)['data']['list']['users']
    # print(datas)
    print(datas)

def get_random_IP():
    proxies = requests.get("https://proxy.scdn.io/api/get_proxy.php?protocol=http&count=1").json()['data']['proxies']
    return proxies[0]

def get_following_page(id, page):
    first_get_sample = "https://www.weibo.com/ajax/friendships/friends?uid={}&page={}"

    response = requests.get(first_get_sample.format(id,page), headers=headers_p).json()
    if response['ok'] == 1 and response['users']:
        return response['users']
    else:
        return None
def get_following_all(id):
    cur = 1
    have_next = True
    all_list = []
    while True:
        cur_page = get_following_page(id, cur)
        if not cur_page:
            break;
        for u in cur_page:
            item = json2item(u,-1)
            all_list.append(item)
        cur+=1
    return all_list
def get_following_all_only_uid(id):
    cur = 1
    have_next = True
    all_list = []
    while True:
        cur_page = get_following_page(id, cur)
        if not cur_page:
            break;
        for u in cur_page:
            all_list.append(u['id'])
        cur+=1
    return all_list
def get_info(id):
    response = requests.get("https://www.weibo.com/ajax/profile/info?uid={}".format(id), headers=headers_p).json()
    return  response

# print(get_random_IP())
# test_mobile(1,5136362277)
# print(get_following_all_only_uid(2607381560))