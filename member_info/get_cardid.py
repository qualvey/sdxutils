import requests
from tools import iheader
from tools import logger as mylogger
import json
import argparse

logger = mylogger.get_logger(__name__)


headers = iheader.headers

def get_person_info(name: str) -> list:

    api = "https://hub.sdxnetcafe.com/api/member/member/list"
    params = {
        "realName": name,
        "cardId": "",
        "page": 1,
        "limit" :100,
        "branchId" : "a92fd8a33b7811ea87766c92bf5c82be",
        "bindid" : "154556880f1c11e9be2a7cd30ae00910"
        }

    response = requests.get(url = api, params=params, headers=headers)
    resJson = response.json()
    with open('./member.json', 'w', encoding='utf-8') as f:
        json.dump(resJson, f, ensure_ascii=False , indent=4)
#rows可能不止一个,多个结果怎么处理
#可能有mobile，nickname
    result = resJson.get('data').get('rows')
    flag = 0
    if result:
        result_number = len(result)
    else:
        flag = 1
        result_number = 0


    if result_number > 1 and flag == 0:
        members = []
        for i in range(result_number-1):
            member = result[i]
            data = {}
            sex_map = {1: '男', 2: '女'}
            data['性别'] = sex_map.get(member.get('sex'), '未知')
            data['手机号'] = member.get('mobile')
            data['nickname'] = member.get('nickname')
            data['realName'] = member.get('realName')
            data['certId']   = member.get('certId')
            members.append(data) 
    elif flag == 0 :
        members = []
        member = result[0]
        data = {}
        sex_map = {1: '男', 2: '女'}
        data['性别'] = sex_map.get(member.get('sex'), '未知')
        data['手机号'] = member.get('mobile')
        data['nickname'] = member.get('nickname')
        data['realName'] = member.get('realName')
        data['certId']   = member.get('certId')
        members.append(data) 
    else:
        return []
    return members

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="获取用户信息")
    parser.add_argument('name',              type=str, help='姓名')
    parser.add_argument('-n', '--name', type=str, default=None, help='姓名')
    args = parser.parse_args()

    name = args.name
    result = get_person_info(name)
    str_json = json.dumps(result, ensure_ascii=False, indent=4)
    logger.info(str_json)
