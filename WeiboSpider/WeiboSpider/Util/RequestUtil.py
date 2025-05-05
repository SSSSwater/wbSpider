import json

import requests
from ..items import json2item
# cookies_p = "SCF=AiX32jEzYrtjOHSIAig0Z6JSN2-xiPD-voGyLWUWbqJlzb-qodBdMzqjWGV2Pek4vzXFm-vK256JPO9DhhkJYuQ.; SINAGLOBAL=468250115768.72687.1736163090160; _s_tentry=passport.weibo.com; Apache=9966005663652.209.1739005590838; ULV=1739005590888:2:1:1:9966005663652.209.1739005590838:1736163090162; SL_G_WPT_TO=zh; SL_GWPT_Show_Hide_tmp=1; XSRF-TOKEN=PfUFkTnw2gczUWjCEOt2-zO3; SL_wptGlobTipTmp=1; SUB=_2A25Ko09aDeRhGeFJ6FcW8SzOzD6IHXVpwc6SrDV8PUNbmtANLWjkkW9NfAwZGz6Je3aLW-no3RvQxn1U6FgaBwbv; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; ALF=02_1741605898; WBPSESS=iPpPH-JXjxwdk8QJixaFMEjvAgRG9EsjuPpPGdJQryOPQuRyyhc53i13QNF-a3V1TD1HZSH2OEIwUkrc0CB6BE5chsGoeb0E0bdpoHRZ0De4cvievMD1ENF42i3JhqeBxNn5Vrqm3Cj67bFPPcmYNw=="
# cookies_m = "SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; WEIBOCN_FROM=10E2195010; SUB=_2A25K7mQeDeRhGeFJ6FcW8SzOzD6IHXVmYBZWrDV6PUJbitAYLRLNkWtNfAwZG0O8TSxvDvDjgj_MONgQWdT2OF0j; SCF=AiNI51DpEdPkbxxx7CPprSe4YHclZd38HjJtnLxUb1Yhq2oCCmzWBh-9NN86HDy3lw..; _T_WM=12749890856; XSRF-TOKEN=0373f7; MLOGIN=1; M_WEIBOCN_PARAMS=from%3D10F2095010%26luicode%3D10001110%26lfid%3D10001110cust_-_1; mweibo_short_token=07c7a42669"
with open('../cookies.txt', 'r') as f:
    cookies_p = f.read()
with open('../cookies_mobile.txt', 'r') as f:
    cookies_m = f.read()
headers_p = {'authority': 'www.weibo.com',
               'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
               'referer': 'https://weibo.com/u/page/follow/' + str(id),
               'cookie': cookies_p,
               'accept':
                   'application/json,text/plain,*/*'
               }
def test_mobile():
    headers = {'authority': 'weibo.com',
               'User-Agent': "Mozilla/5.0 (Linux; Android 14; 23013RK75C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.260 Mobile Safari/537.36 Weibo (Xiaomi-Redmi K60__weibo__15.2.0__android__android14)",
               'referer': 'https://weibo.com/u/' + str(id),
               'cookie': cookies_m,
               'accept':
                   'application/json,text/plain,*/*'
               }
    response = requests.get("https://m.weibo.cn/api/friendships/sortedList?uid=2071587462&type=2", headers=headers)
    datas = json.loads(response.text)
    # print(datas)
    print([(u['user']['id'],u['user']['screen_name'],u['user']['followers_count']) for u in datas['data']['users']])



def get_following_page(id, page):
    first_get_sample = "https://www.weibo.com/ajax/friendships/friends?uid={}&page={}"

    response = requests.get(first_get_sample.format(id,page), headers=headers_p).json()
    return response['users']
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
def get_info(id):
    response = requests.get("https://www.weibo.com/ajax/profile/info?uid={}".format(id), headers=headers_p).json()
    return  response
print(len(get_following_all(6593199887)))
