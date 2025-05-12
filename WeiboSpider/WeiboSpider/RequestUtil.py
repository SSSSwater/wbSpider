import json
import os

import requests
from .items import json2item
from fake_useragent import UserAgent


ua = UserAgent()
def get_fake_weibo_UA():
    return ua.safari + " Weibo (Xiaomi-Redmi K60__weibo__15.2.0__android__android14)"
cookies_p = "SCF=AiX32jEzYrtjOHSIAig0Z6JSN2-xiPD-voGyLWUWbqJlzb-qodBdMzqjWGV2Pek4vzXFm-vK256JPO9DhhkJYuQ.; SINAGLOBAL=468250115768.72687.1736163090160; ULV=1739963446045:5:4:1:1881349511191.3325.1739963445937:1739211340425; XSRF-TOKEN=bQb6bh0XCiWUYsnWMDPIy6x7; PC_TOKEN=16e0977b86; SUB=_2A25FHK9aDeRhGeFJ6FcW8SzOzD6IHXVmU66SrDV8PUNbmtAbLVrAkW9NfAwZG14fi3nbUplOULtlc-Mmn1nIto3g; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; ALF=02_1749052426; WBPSESS=iPpPH-JXjxwdk8QJixaFMOt_VgZGejtRqdz3QC8CjlcFfg5JRN9xZvqDwn-7utQG7oU10UgEqnuU4GdJKegmEBkZ5fB8zZCxb2UJH8F-THjWJ_CafX1rDpTHbY0F4dGe; SL_G_WPT_TO=zh; SL_GWPT_Show_Hide_tmp=1; SL_wptGlobTipTmp=1"
cookies_m = "SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; WEIBOCN_FROM=10E2195010; SUB=_2A25FFPVXDeRhGeFJ6FcW8SzOzD6IHXVmSaUfrDV6PUJbitAbLXbxkWtNfAwZG2f25TjBhGbfkQPXTP45l8ruM2nH; SCF=AiNI51DpEdPkbxxx7CPprScZAbturA5JKXI4gB5ipZu0ffrW2t8c0QggK2bNbpi5oQ..; _T_WM=28212530147; XSRF-TOKEN=54e67e; MLOGIN=1; M_WEIBOCN_PARAMS=from%3D10F2095010"

headers_p = {'authority': 'www.weibo.com',
               'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
               'referer': 'https://weibo.com/u/page/follow/' + str(id),
               'cookie': cookies_p,
               'accept':
                   'application/json,text/plain,*/*'
               }
def test_mobile(page,uid):
    headers = {'authority': 'weibo.com',
               'User-Agent': "Mozilla/5.0 (Linux; Android 14; 23013RK75C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.260 Mobile Safari/537.36 Weibo (Xiaomi-Redmi K60__weibo__15.2.0__android__android14)",
               'referer': 'https://weibo.com/u/' + str(id),
               'cookie': cookies_m,
               'accept':
                   'application/json,text/plain,*/*'
               }
    response = requests.get("https://m.weibo.cn/c/fans/followers?page={}&uid={}&cursor=-1&count=20".format(page,uid), headers=headers)
    datas = json.loads(response.text)['data']['list']['users']
    # print(datas)
    print(datas)



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

# test_mobile(10,5136362277)
# print(get_following_all_only_uid(2607381560))