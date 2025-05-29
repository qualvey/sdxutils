from tools import logger, iheader, env
from worktime import get_userid
from datetime import datetime, timedelta
import requests
import os
import json

logger = logger.get_logger(__name__)
headers = iheader.headers
branchid = "a92fd8a33b7811ea87766c92bf5c82be"
dir = f'{env.proj_dir}/schedule'
url = "https://hub.sdxnetcafe.com/api/admin/duty/roster/save"

headers['Content-Type'] = "application/json;charset=utf-8"

start_date = "2025-05-19" 
#如果不是today，那就设置为目标week的前一周的任意一天
#start_date = "today" 
rest_days_map = {
    "郭丰硕": [1, 2],         
    "汪永康": [7],       
    "巫媛媛": [5,6,7],
    "裴海军": []
}

handsome = '李龙涛'
crew_list = [ '裴海军','汪永康', '郭丰硕', '巫媛媛']

schedule_map = {
    '汪永康': '店长',
    '郭丰硕': '晚收',
    '巫媛媛': '早收',
    '裴海军': '中班',
}

#获取每个人的userid
userids = get_userid.get_userid()
with open(f'{dir}/userids.json', 'w', encoding='utf-8') as f:
    json.dump(userids, f,ensure_ascii=False, indent=2)
#获取所有的categoryid
categoryid_api = f"https://hub.sdxnetcafe.com/api/admin/duty/category/list/{branchid}"
categoryids_response = requests.get(url = categoryid_api, headers = headers)
categoryids_rawdata = categoryids_response.json()['data']
categoryids = {}
#用法:   categoryids['班次']
for i in categoryids_rawdata:
    categoryids[i['category']] = i['id']
with open(f'{dir}/categoryids', 'w', encoding='utf-8') as f:
    json.dump(categoryids, f, ensure_ascii = False, indent=4)

rest =  categoryids['休息']

#一周的日期

def get_next_week_days(dt):
    # 计算当前日期是星期几，星期一为0，星期日为6
    current_weekday = dt.weekday()
    # 计算上周日距离当前日期的天数
    days_since_last_sunday = 13-current_weekday
    # 计算下个周日的日期
    next_sunday = dt +  timedelta(days=days_since_last_sunday)
    # 计算上周一的日期
    next_monday = next_sunday - timedelta(days=6)
    week_dates = [next_monday + timedelta(days=i) for i in range(7)]
    logger.info(f'{next_monday},{next_sunday}')
    return week_dates
if start_date == "today":
    date_list = get_next_week_days(datetime.today().replace(hour=0, minute=0, second=0))
else : 
    date_list = get_next_week_days(datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0))
datestr_list = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in date_list]

in_out = {
    '店长': 'IN', 
    '晚收': 'IN',
    '早收': 'IN',
    '中班': 'OUT'
}

def get_list():
    logger.info(f'获取排班列表: date: {datestr_list[0]}')

    url = f'https://hub.sdxnetcafe.com/api/admin/duty/roster/list'
    params = {
            "branchId":  branchid,
            "dutyDate":  datestr_list[0]
    }
    response =  requests.get(url=url, params=params, headers = headers )
    data = response.json().get('data')
    with open(f'{env.proj_dir}/schedule/list.json', 'w', encoding='utf-8') as f :
              json.dump(data, f, ensure_ascii=False, indent = 4)
    return data

def gen_userdata(name):
    userid = userids[name]
    schedule = schedule_map[name]
    inout       = in_out[schedule]
    categoryid = categoryids[schedule]
    rest_day = rest_days_map.get(name, [])  # 这里就是 [1~7] 形式的列表


    data = []
    for dt in date_list:
        if dt.isoweekday() in rest_day:
            data.append({
                "branchId": branchid,
                "userId": userid,
                "categoryId": rest,
                "dutyDate": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "groupName": inout
            })
        else:
            data.append({
                "branchId": branchid,
                "userId": userid,
                "categoryId": categoryid,
                "dutyDate": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "groupName": inout
            })
    return data

def gen_ryu_schedule(update = False, days_id =None):
    ryu_userid = userids['李龙涛']
    data = []

    for idx, dt in enumerate(date_list, 0):
        if days_id:
            target_id = days_id[idx]
        iso_day = dt.isoweekday()  # 1 ~ 7

        flag = True
        for name, rest_day in rest_days_map.items():
            #breakpoint()
            if schedule_map[name] == '店长':
                continue
            if iso_day in rest_day:
                flag  = False
                schedule = schedule_map[name]
                categoryid = categoryids[schedule]
                item = {
                    "id": target_id if update else None,
                    "branchId": branchid,
                    "userId": ryu_userid,
                    "categoryId": categoryid,
                    "dutyDate": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "groupName": "OUT"
                }
                data.append(item)
                break  # 一天只替一个人
        if flag:
            logger.debug('设置休息')
            item = {
                "id": target_id if update else None,
                "branchId": branchid,
                "userId": ryu_userid,
                "categoryId": rest,
                "dutyDate": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "groupName": "OUT"
            }
            data.append(item)
    return data

def new_instance():
    for i in crew_list:
        data = gen_userdata(i)
        response = requests.post(url=url, json = data, headers = headers)

    data = gen_ryu_schedule()
    response = requests.post(url=url, json = data, headers = headers)

def update_data(name,days_id):
    userid = userids[name]
    schedule = schedule_map[name]
    inout       = in_out[schedule]
    categoryid = categoryids[schedule]
    rest_day = rest_days_map.get(name, [])  # 这里就是 [1~7] 形式的列表

    data = []
    for idx, dt in enumerate(date_list, 0): 
        target_id = days_id[idx]
        if dt.isoweekday() in rest_day:
            data.append({
                "id"        : target_id,
                "branchId": branchid,
                "userId": userid,
                "categoryId": rest,
                "dutyDate": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "groupName": inout
            })
        else:
            data.append({
                "id"        : target_id,
                "branchId": branchid,
                "userId": userid,
                "categoryId": categoryid,
                "dutyDate": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "groupName": inout
            })
    return data

def delete_api():
    delete_url = "https://hub.sdxnetcafe.com/api/admin/duty/roster/user"

    delete_data = {
        "branchId": branchid,
        "dutyDate": "2025-05-19 00:00:00",
            "userId"  : userids['郭丰硕']
    }

    response =  requests.delete(url=delete_url, headers = headers, json = delete_data)

def extract_days(data_list):
    result = {}
    for item in data_list:
        name = item.get("name")
        #days = {f"day{i}": item.get(f"day{i}") for i in range(1, 8)}
        #用list而不是dict
        days = [item.get(f"id{i}") for i in range(1, 8)]
        result[name] = days
    return result

old_list = get_list()


with open('./schedule/right_data.json', 'r' , encoding='utf-8') as f:

    data = json.load(f)

#response = requests.post(url=url, json = data, headers = headers)
#breakpoint()


if not old_list:
    logger.info('重新设置数据')
    new_instance()
else:
    final_json = []
    days_id_list = extract_days(old_list)
    for i in crew_list:
        if i in days_id_list:
            logger.info(f'更新{i}的数据')
            data = update_data(i,days_id_list[i])
            final_json += data
            with open(f'{env.proj_dir}/schedule/data.json', 'a', encoding = 'utf-8') as  f:
                pass

        else:
            logger.info(f'创建{i}的数据')
            data = gen_userdata(i)
            final_json += data

    if handsome in days_id_list:
        logger.info(f'更新{handsome}的数据')
        data = gen_ryu_schedule(update = True, days_id = days_id_list[handsome])
        final_json += data
    else:
        logger.info(f'创建{handsome}的数据')
        data = gen_ryu_schedule()
        final_json += data

    response = requests.post(url=url, json = data, headers = headers)
    breakpoint()

    with open(f'{env.proj_dir}/schedule/data.json', 'w', encoding = 'utf-8') as  f:
        json.dump(final_json, f , ensure_ascii=False, indent=4)
