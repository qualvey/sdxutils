
from copy       import copy

from openpyxl                import load_workbook
from openpyxl.styles         import Font, Border, Side,  Alignment, numbers
from openpyxl.cell.text      import InlineFont
from openpyxl.cell.rich_text import CellRichText, TextBlock, TextBlock
from openpyxl.utils import column_index_from_string, get_column_letter


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
