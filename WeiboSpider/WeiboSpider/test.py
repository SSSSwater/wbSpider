import json

import requests

# cookies_p = "SCF=AiX32jEzYrtjOHSIAig0Z6JSN2-xiPD-voGyLWUWbqJlzb-qodBdMzqjWGV2Pek4vzXFm-vK256JPO9DhhkJYuQ.; SINAGLOBAL=468250115768.72687.1736163090160; _s_tentry=passport.weibo.com; Apache=9966005663652.209.1739005590838; ULV=1739005590888:2:1:1:9966005663652.209.1739005590838:1736163090162; SL_G_WPT_TO=zh; SL_GWPT_Show_Hide_tmp=1; XSRF-TOKEN=PfUFkTnw2gczUWjCEOt2-zO3; SL_wptGlobTipTmp=1; SUB=_2A25Ko09aDeRhGeFJ6FcW8SzOzD6IHXVpwc6SrDV8PUNbmtANLWjkkW9NfAwZGz6Je3aLW-no3RvQxn1U6FgaBwbv; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; ALF=02_1741605898; WBPSESS=iPpPH-JXjxwdk8QJixaFMEjvAgRG9EsjuPpPGdJQryOPQuRyyhc53i13QNF-a3V1TD1HZSH2OEIwUkrc0CB6BE5chsGoeb0E0bdpoHRZ0De4cvievMD1ENF42i3JhqeBxNn5Vrqm3Cj67bFPPcmYNw=="
cookies_m = "SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF.CK3QCQ_vRBgT33LMMYiI5NHD95QNS0efS02EeoMEWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M0SKMpeozNentt; WEIBOCN_FROM=10E2195010; SUB=_2A25KlcQoDeRhGeFJ6FcW8SzOzD6IHXVpyPZgrDV6PUJbitAYLVrDkWtNfAwZG5d4rSzJIDMgfx1cPajpIbGAuND_; SCF=AiNI51DpEdPkbxxx7CPprSeBEPbxOT-lhpgXhbJORvYaYeGwggG-ytjoekpcnzvwcA..; _T_WM=50656465720; MLOGIN=1; M_WEIBOCN_PARAMS=from%3D10F2095010; XSRF-TOKEN=d1c363; mweibo_short_token=6ee0c1e4a4"
cookies_str = ""
# with open('cookies.txt', 'r') as f:
#     cookies_str = f.read()

def test_mobile():
    headers = {'authority': 'weibo.com',
               'User-Agent': "Mozilla/5.0 (Linux; Android 14; 23013RK75C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.260 Mobile Safari/537.36 Weibo (Xiaomi-Redmi K60__weibo__15.2.0__android__android14)",
               'referer': 'https://weibo.com/u/' + str(id),
               'cookie': cookies_m,
               'accept':
                   'application/json,text/plain,*/*'
               }
    response = requests.get("https://m.weibo.cn/c/fans/followers?page=1&uid=1323527941&cursor=-1&count=100", headers=headers)
    print(response.text)

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

test_mobile()