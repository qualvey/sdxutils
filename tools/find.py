
from openpyxl import load_workbook
from datetime import datetime, date
import json

def get_cell_by_datetime(worksheet,search_value,start_cell="A1",end_cell="A33"):
    """
    参数：工作表，查找值<datatime>, 开始和终止的cell位置
    返回：第一个匹配到的cell行号
    """
    try:
        min_row, max_row = worksheet[start_cell].row, worksheet[end_cell].row
        min_col, max_col = worksheet[start_cell].column, worksheet[end_cell].column

        for row in worksheet.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
            for cell in row:
                if isinstance(cell.value, datetime):  # 确保是 datetime 类型
                    if cell.value.date() == search_value.date():  # 对比日期部分
                        print("!!!!!!!",cell,search_value)
                        return cell

        return None  # 未找到匹配值

    except KeyError:
        print(f"错误: {start_cell} 或 {end_cell} 可能超出了工作表范围")
        return None

