from tools import iheader, env
import requests
import json


url = "https://hub.sdxnetcafe.com/api/admin/salary/user/list?branchId=a92fd8a33b7811ea87766c92bf5c82be"

response = requests.get(url , headers=iheader.headers, timeout=10)

if (response.reason=='OK'):
    response_usrId = response.json()
else:
    print('请求userinfo失败，检查token是否过期')

def get_userid():
    userIDs={}
    for item in response_usrId['data']:
        userIDs[item['name']] = item['id']
    return userIDs
