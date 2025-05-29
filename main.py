import shutil
import os
import argparse
from datetime   import datetime, date, timedelta, time
from copy       import copy

from openpyxl                import load_workbook
from openpyxl.styles         import Font, Border, Side,  Alignment, numbers
from openpyxl.cell.text      import InlineFont
from openpyxl.cell.rich_text import CellRichText, TextBlock, TextBlock
from openpyxl.utils import column_index_from_string, get_column_letter

from meituan.main       import get_meituanSum, mt_status, get_mtgood_rates
from douyin.main        import get_douyin_data, get_dygood_rate
from operation.main     import resolve_operation_data
from operation import ThirdParty
from operation import elecdata as electron
from specialFee      import main as specialFee
from tools              import env
from tools.logger import get_logger

from xlutils.xlUtil import *

machian_sum = 76

logger = get_logger(__name__)

parser = argparse.ArgumentParser(description="日报表自动化套件")

parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
parser.add_argument("-dc", "--dateconfig", action="store_true", help="使用配置文件的日期")
parser.add_argument("-now", "--today", action="store_true", help="使用今天作为日期")
parser.add_argument("-ne", "--no-elec", action="store_true", help="不输入电表数据")
parser.add_argument("-dt", "--date", type=str  , help="指定日期")

args = parser.parse_args()

yesterday = date.today() - timedelta(days=1)
working_datetime_date = yesterday
working_date_str      = yesterday.strftime('%Y-%m-%d')
working_datetime      = datetime.combine(yesterday, datetime.min.time())

if args.dateconfig:
    working_datetime = env.working_datetime
    working_datetime_date  = working_datetime.date()
if args.today:
    working_datetime_date = datetime.today()
    working_date_str      = working_datetime_date.strftime('%Y-%m-%d')
    working_datetime      = datetime.combine(working_datetime_date, datetime.min.time())
if args.date:
    working_datetime      = datetime.strptime(args.date, "%Y-%m-%d")
    working_datetime_date = working_datetime.date()
    working_date_str      = working_datetime_date.strftime('%Y-%m-%d')

if args.no_elec:
    elec_usage = None
else:
    try:
        elec_usage = electron.get_elecUsage(working_datetime_date)
        if not elec_usage:
            logger.warning('电表数据获取错误，请检查')
    except Exception as e:
        logger.error(f'{e}')

logger.info(f'当前工作的日期是: {working_datetime_date}')

dir_str     = f"{env.proj_dir}/et/{working_datetime_date.strftime('%m%d')}日报表"
source_file = env.source_file
save2file   = f"{dir_str}/2025年日报表.xlsx"

mt, mt_len = get_meituanSum(working_datetime)
if not mt:
    logger.warning('美团数据没拿到')
dy, dy_len = get_douyin_data(working_datetime)
if not dy:
    logger.warning('抖音数据没有拿到')
english = resolve_operation_data(working_datetime)
if not english:
    logger.warning('运营数据没拿到')

ota_update  = ThirdParty.ota_update
repeat_ids = ThirdParty.check_unique(working_date_str)

d_status = 0

for thirdtype, ids in repeat_ids.items():
    for id in ids:
        logger.info(f'正在删除{thirdtype}:{id}')
        delete_status = ThirdParty.delete(id)
        if delete_status == 1:
            logger.warning(f'删除旧数据失败，不执行新数据更新')
            d_status = 1
if d_status == 0:
    logger.info('删除成功')
    ota_update(ota_name='DOUYIN', date_obj=working_datetime, income=dy)
    ota_update(ota_name='MEITUAN', date_obj=working_datetime, income=mt)

specialFee_list, special_sum = specialFee.get_specialFee(working_datetime)        #可以排序

working_sheetname = f'{working_datetime.month}月'
wb = load_workbook(source_file)

if working_sheetname in wb.sheetnames:
    ws = wb[working_sheetname]
    wb.active = ws
    logger.info(f'操作的worksheet{wb}:{ws}')
else:
    logger.error(f'当前月份的工作表不存在，请手动检查.{working_sheetname}')

def load_data():
    chinese = {}
    data_pure = {
        "用电量" : elec_usage ,
        "美团"   : mt   ,
        "抖音"   : dy
    }

    cn_en_map = {
        "网费充值"  :     "amountFee",
        "提现本金"  :     "withdrawPrincipal",
        "找零"      :     "checkoutDeposit",
        "零售"      :     "retail",
        "水吧"      :     "waterBar",
        "代购"      :     "agent",
        "退款"      :     "totalRefundFee",
        "报销"      :     None,
        "在线支付"  :     "onlineIn",
        "奖励金"    :     "awardFee",
        "卡券"      :     "cardVolumeFee",
        "特免"      :     "specialFree",
        "网费消耗"  :     "totalConsumeNetworkFee",
        "上机人次"  :     "onlineTimes",
        "上机时长"  :     "duration",
        "点单率"    :     "orderRate",
        "新会员"    :     "newMember"
    }

    for cn_name, eng_name in cn_en_map.items():
        if eng_name and eng_name in english:
            data_pure[cn_name] = english[eng_name]
        else:
            data_pure[cn_name] = 0

    data_pure["退款"]       = -data_pure["退款"] 
    if data_pure['退款'] == 0 :
        data_pure['退款'] = None

    data_pure["上机时长"]   = round(data_pure["上机时长"] /60, 2)
    return data_pure

def insert_data(data_pure):
    target_row = electron.get_row_by_date(ws, working_datetime_date)
    
    logger.info(f'电表数据所在行号 {target_row}')
    import json
    fmt_json = json.dumps(data_pure, ensure_ascii=False, indent=4)
    #logger.info(f'\n最终要写入et的数据:\n{fmt_json}')

    for col in ws.iter_cols(min_row=2, max_row=2, min_col=1, max_col=29):
        header = col[0].value  # 第二行的列标题
        if header in data_pure:
            ws.cell(row=target_row, column=col[0].column, value=data_pure[header])

    date_str = working_datetime.strftime("%Y年%m月%d日")
    #%-m 和 %-d 中的减号用于去除月份和日期中的前导零。请注意，这种用法在某些操作系统（如 Unix/Linux）上有效，但在 Windows 上可能不被支持。

    #ws["B36"].value = f"芜湖张家山店{date_str}营业状况"
    ws["C36"].value = f"芜湖张家山店{date_str}营业状况"
    ws["G36"].value = machian_sum


b = TextBlock

ws['G37'].font = font_yahei

def save(path):
    try:
        os.makedirs(dir_str, exist_ok=True)
        logger.info(f"目录 '{dir_str}' 创建成功")
    except Exception as e:
        logger.error(f"创建目录时发生错误: {e}")
    try:
        shutil.move(source_file, f"{source_file}.old")
        wb.save(source_file)
        wb.save(path)
        logger.debug(f'成功保存到  {path}')
    except FileNotFoundError:
        logger.error(f"文件 {path} 或目录 {os.path.dirname(source_file)} 不存在")
    except Exception as e:
        logger.error(f"复制文件 {path} 出错：{e}")

#判断specialFeesum和specialFee是否一致I#
data_pure = load_data()
if data_pure['特免'] != special_sum:
    logger.warn(f"特免金额不匹配，请检查!!运营数据中是{data_pure['特免']},订单列表中计算出来是{special_sum}")

insert_data(data_pure)

special_mark(ws = ws, special_data = specialFee_list, start_col='H', end_col='K' )

mt_good_num = get_mtgood_rates(working_datetime.strftime('%Y-%m-%d'))
dy_good_num = get_dygood_rate(working_datetime)
ota_comment(ws,mt_len, dy_len,mt_good_num,dy_good_num, 'H')
handle_headers(ws)
save(save2file)
