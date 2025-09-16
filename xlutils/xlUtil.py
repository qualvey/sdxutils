
from copy       import copy

from openpyxl                import load_workbook
from openpyxl.styles         import Font, Border, Side,  Alignment, numbers
from openpyxl.cell.text      import InlineFont
from openpyxl.cell.rich_text import CellRichText, TextBlock, TextBlock
from openpyxl.utils import column_index_from_string, get_column_letter
from tools import  logger as mylogger
logger = mylogger.get_logger(__name__)
import shutil
import os
import argparse
from datetime               import datetime, date, timedelta 

from openpyxl                import load_workbook , Workbook
from openpyxl.cell.rich_text import  TextBlock, TextBlock
from openpyxl.worksheet.worksheet import Worksheet

from meituan.main       import get_meituanSum,  get_mtgood_rates
from douyin.main        import final_out, get_dygood_rate

from operation.main     import resolve_operation_data
from operation          import ThirdParty
from operation          import elecdata as electron
from specialFee         import main as specialFee
from tools              import env



font_wenquan = Font(name='WenQuanYi Zen Hei',
                size=11,
                bold=False,
                italic=False,
                vertAlign=None,
                underline='none',
                strike=False,
                color='FF000000'
        )

font_yahei = Font(name='Microsoft YaHei',
                size= 8,
                bold=False,
                italic=False,
                vertAlign=None,
                underline='none',
                strike=False,
                color='FF000000'
        )

yahei_inline = InlineFont(rFont='Microsoft YaHei',
                sz=11,
                color='FF000000'
        )
yahei_22 = InlineFont(rFont='Microsoft YaHei',
                sz=22,
                color='FFFF0000'
                    )
yahei_red_8 = InlineFont(rFont='Microsoft YaHei',
                sz=8,
                color='FFFF0000'
                    )

left_alignment = Alignment(horizontal='left')
center_alignment = Alignment(horizontal='center')

def special_mark(ws, special_data, start_col, end_col, start_row=37, end_row=47):

    thin    = Side(border_style="thin", color="888888")
    medium  = Side(border_style="medium", color="000000")
    dotted  = Side(border_style="dotted", color="000000")

    merged_ranges = ws.merged_cells.ranges

    start_col_index = column_index_from_string(start_col)
    end_col_index   = column_index_from_string(end_col)
    merge_right_col_index = end_col_index - 1  # 合并区域去掉“元”列

    merge_left_col  = start_col
    merge_right_col = get_column_letter(merge_right_col_index)
    yuan_col        = end_col  # 最右边是“元”列
    for row in range(start_row, end_row):
        for col_letter in [start_col ]:  # 例如 H 和 K
            cell = ws[f'{col_letter}{row}']
            cell.value = None

    for row in range(start_row, end_row):
        merge_range = f'{merge_left_col}{row}:{merge_right_col}{row}'
        full_range  = f'{merge_left_col}{row}:{yuan_col}{row}'

        # 如果整行已合并，拆分后再合并前几列
        if any(str(rng) == full_range for rng in merged_ranges):
            ws.unmerge_cells(full_range)
        ws.merge_cells(merge_range)

        left_cell  = ws[f'{merge_left_col}{row}']
        yuan_cell  = ws[f'{yuan_col}{row}']
        mid_cell   = ws.cell(row=row, column=merge_right_col_index)

        yuan_cell.value = None

        left_cell.border = Border(left = thin, bottom=dotted)
        mid_cell.border  = Border(left=None, right=None, bottom=dotted)
        yuan_cell.border = Border(bottom=dotted,right=medium)

        base_font = copy(ws[f'{merge_left_col}{start_row}'].font)
        left_cell.font   = base_font
        mid_cell.font    = base_font
        yuan_cell.font   = base_font

    # 设置最后一行底部边框
    bottom = end_row - 1
    ws[f'{merge_left_col}{bottom}'].border  = Border(left=thin, bottom=dotted)
    ws[f'{merge_right_col}{bottom}'].border = Border(bottom=dotted)
    ws[f'{yuan_col}{bottom}'].border        = Border(bottom=dotted, right=medium)

    # 写入数据
    titlecell = ws.cell(row=37, column=start_col_index)
    titlecell.value = "特免明细:"
    titlecell.alignment = left_alignment
    for index, item in enumerate(special_data):
        row = start_row+1 + index
        if row >= end_row:
            break
        if '：' in item:
            reason, value = item.split('：', 1)
        else:
            reason, value = item, ''

        text_cell = ws.cell(row=row, column=start_col_index)
        text_cell.value = item
        text_cell.alignment = left_alignment

        yuan_cell = ws.cell(row=row, column=end_col_index)
        yuan_cell.value = "元"
        yuan_cell.alignment = center_alignment

def ota_comment(ws,mt_len, dy_len,mt_good_num, dy_good_num, column):

    col_index = column_index_from_string(column)

    title  = ws.cell(row = 53, column = col_index)
    dycell = ws.cell(row = 54, column = col_index)
    mtcell = ws.cell(row = 55, column = col_index)
    good_rate_cell = ws.cell(row = 56, column = col_index)
    bad_rate_cell  = ws.cell(row = 57, column = col_index)

    for row in [54, 55, 56, 57]:
        ws.cell(row=row, column=col_index).alignment = left_alignment

    title.value  = f'OTA平台线上评价：'
    title.alignment = left_alignment

    mtcell.value = f"美团：{mt_len}单  好评数：{mt_good_num}个"
    dycell.value = f'抖音：{dy_len}单  好评数：{dy_good_num}个'
    好评率 = (mt_good_num+dy_good_num)*100/(mt_len+dy_len)
    good_rate_cell.value = f"今日好评率: {round(好评率, 2)}%"
    bad_rate_cell.value  = f"今日差评数: 0个"

def A1Bug(worksheet):
    '''
        A1的标题样式有bug，单独执行这个函数来处理
    '''
    red_font = Font(color="FF0000")
    rich_text = CellRichText(
        [
            "网费收入",
            TextBlock(InlineFont(red_font), "(网费+提现+找零)"),  # 使用 InlineFont 包装
        ]
    )
    worksheet['A1'] = rich_text
    font1 = Font(bold=True, size=16)
    worksheet['A1'].font = font1

def handle_headers(ws):
    mcells = [ "f1", "j1", "n1", "s1", "w1", "ac1" ]
    ws['A36'].number_format = 'yyyy-mm-dd'

    for cell in mcells:
        text = ws[cell].value
        start_index = text.find("(")
        end_index = text.find(")")

        if start_index != -1 and end_index != -1:
            # 创建 Font 对象，设置字体大小
            small_font = Font(size=8)
            # 创建 CellRichText 对象
            rich_text = CellRichText(
                [
                    text[:start_index],  # 括号前的文本
                    TextBlock(InlineFont(small_font), text[start_index:end_index + 1]),  # 括号内的文本，小字
                    text[end_index + 1:],  # 括号后的文本
                ]
            )
        else:
            # 如果没有括号，直接设置文本
            rich_text = CellRichText([text])
        ws[cell] = rich_text
        A1Bug(ws)

from openpyxl.worksheet.worksheet import Worksheet
from datetime import datetime, date

def find_missing_dates(ws: Worksheet, end_datetime: datetime, col_date="A", col_data="B") -> list[date]:
    """
    在指定 worksheet 中查找截止日期之前缺失数据的日期

    参数:
        ws (Worksheet): openpyxl 工作表对象
        end_datetime (datetime): 截止日期（只检查早于它的日期）
        col_date (str): 日期所在列 (默认 "A")
        col_data (str): 数据所在列 (默认 "B")

    返回:
        list[datetime.date]: 缺失数据的日期列表
    """
    missing_dates = []

    for row in range(2, ws.max_row + 1):  # 假设第1行是表头
        date_cell = ws[f"{col_date}{row}"].value
        data_cell = ws[f"{col_data}{row}"].value

        if date_cell is None:
            continue  # 跳过空日期

        # 转换日期
        if isinstance(date_cell, datetime):
            date_value = date_cell.date()
        else:
            # 尝试解析字符串
            try:
                date_value = datetime.strptime(str(date_cell), "%Y-%m-%d").date()
            except:
                continue

        # 判断是否早于 end_datetime，且数据为空
        if date_value < end_datetime.date() and (data_cell is None or str(data_cell).strip() == ""):
            missing_dates.append(date_value)

    return missing_dates

def init_sheet(working_datetime: datetime, source_file: str) -> Workbook :
    '''
        return workbook
    '''
    logger.info("init_sheet")
    working_sheetname = f'{working_datetime.month}月'
    wb = load_workbook(source_file)

    if working_sheetname in wb.sheetnames:
        ws = wb[working_sheetname]
        wb.active = ws
        logger.info(f'操作的worksheet{wb}:{ws}')
        ws['G37'].font = font_yahei
        return wb
    else:
        logger.error(f'当前月份的工作表不存在，请手动检查.{working_sheetname}')
        raise ValueError("出错了")

def load_data(
        elec_usage: float, 
        mt: float, dy: float,
        english: dict,
        cn_en_map: dict
        )     -> dict:
    """
    :param english: 英文字段组成的原始数据
    :param elec_usage: 用电量
    :param mt: 美团营收
    :param dy: 抖音营收
    :return: 映射并处理后的数据字典
    """
    main_data: dict[str, float | None] = {
        "用电量" : elec_usage ,
        "美团"   : mt   ,
        "抖音"   : dy
    }

    for cn_name, eng_name in cn_en_map.items():
        main_data[cn_name] = english.get(eng_name, 0) if eng_name else 0

    if not main_data["退款"]:
        main_data["退款"] = None
    else:
        main_data["退款"]     = -main_data["退款"] 

    if main_data["上机时长"] is not None:
        main_data["上机时长"]   = round(main_data["上机时长"] /60, 2)

    return main_data

from typing import cast, Optional, Tuple
from decimal import Decimal

def insert_data(ws: Worksheet, data: dict, working_datetime:datetime, machian_sum:int) -> Worksheet:

    target_row:int | None = electron.get_row_by_date(ws, working_datetime)
    target_row  = cast(int, target_row)
    
    logger.info(f'电表数据所在行号 {target_row}')

    for col in ws.iter_cols(
        min_row=2,
        max_row=2,
        min_col=1,
        max_col=29):

        header = col[0].value  # 第二行的列标题

        if header in data and target_row:
            ws.cell(row=target_row, column=col[0].column, value=data[header]) # type: ignore

    date_str = working_datetime.strftime("%Y年%m月%d日")
    #%-m 和 %-d 中的减号用于去除月份和日期中的前导零。请注意，这种用法在某些操作系统（如 Unix/Linux）上有效，但在 Windows 上可能不被支持。

    ws["C36"].value = f"芜湖张家山店{date_str}营业状况"
    ws["G36"].value = machian_sum
    return ws

def save(path: str, wb: Workbook,source_file:str,dir_str:str):
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

class Wshadler:
    def __init__(self, filepath: str, working_sheetname: str):
        self.filepath = filepath
        self.working_sheetname = working_sheetname

    def load_workbook(self):
        try:
            wb = load_workbook(self.filepath)
            logger.info(f'成功加载工作簿: {self.filepath}')
        except Exception as e:
            logger.error(f'无法加载工作簿: {self.filepath}. 错误: {e}')
            raise

        if self.working_sheetname in wb.sheetnames:
            ws = wb[self.working_sheetname]
            wb.active = ws
            logger.info(f'操作的worksheet{wb}:{ws}')
            ws['G37'].font = font_yahei
            return wb
        else:
            logger.error(f'当前月份的工作表不存在，请手动检查.{self.working_sheetname}')
            raise ValueError("出错了")
