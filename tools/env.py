import os
import json
import pytz
from datetime   import datetime, date

def get_directory(level=0):
    """
    获取当前脚本所在目录或其上级目录的绝对路径。
    参数：
        level (int): 指定获取上级目录的层级。默认为0，表示当前脚本所在目录；
                     1表示上一级目录，2表示上两级目录，依此类推。
    返回：
        str: 指定层级的目录的绝对路径。
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for _ in range(level):
        current_dir = os.path.dirname(current_dir)
    print(f'变量current_dir{current_dir}')
    return current_dir

def get_timestamp(datetime_obj, end_of_day=False, unit='ms'):
    """
    将北京时间的日期字符串转换为 Unix 时间戳。

    参数：
        date_str (str): 北京时间的日期字符串，格式为 "YYYY-MM-DD"。
        end_of_day (bool): 是否返回当天的结束时间戳。默认为 False，即返回当天的开始时间戳。
        unit (str): 返回时间戳的单位，'s' 表示秒，'ms' 表示毫秒。默认为 'ms'。

    返回：
        int: Unix 时间戳，单位由 unit 参数决定。
    """
    try:
        # 解析日期字符串
        beijing_date = datetime_obj

        # 设置北京时区
        beijing_timezone = pytz.timezone('Asia/Shanghai')
        beijing_datetime = beijing_timezone.localize(beijing_date)

        # 如果需要当天的结束时间戳，则设置时间为 23:59:59
        if end_of_day:
            beijing_datetime = beijing_datetime.replace(hour=23, minute=59, second=59)

        # 转换为 UTC 时间
        utc_datetime = beijing_datetime.astimezone(pytz.utc)

        # 转换为 Unix 时间戳（以秒为单位）
        timestamp_s = int(utc_datetime.timestamp())

        # 根据 unit 参数返回相应的时间戳
        if unit == 's':
            return timestamp_s
        elif unit == 'ms':
            return timestamp_s * 1000
        else:
            raise ValueError("unit 参数必须是 's' 或 'ms'。")
    except (ValueError, TypeError) as e:
        print(f"错误：{e}")
        return None  # 如果日期字符串格式错误或其他异常，则返回 None

home = os.environ.get('HOME') 
proj_dir = get_directory(1)

source_file = f"{proj_dir}/et/2025年日报表.xlsx"
elecUsage_file = f"{proj_dir}/et/2025年张家山店3月电表.xlsx"

config_file = f"{proj_dir}/config.json"
configjson  = {}

with open(config_file, 'r',encoding="UTF-8") as config:
    configjson = json.loads(config.read())

working_datetime = datetime.strptime(configjson['date'], "%Y-%m-%d")
date_str = working_datetime.strftime("%-m月%-d日")


print(dir())
if __name__ == "__main__":
    print(configjson)
    print("当前脚本所在目录:", get_directory())
    print("proj_dir:" ,proj_dir)
    print("上一级目录:", get_directory(1))
    print("上两级目录:", get_directory(2))
