import shutil
import os
import argparse
from datetime   import datetime, date, timedelta
from copy       import copy

from openpyxl                import load_workbook
from openpyxl.styles         import Font, Border, Side,  Alignment
from openpyxl.cell.text      import InlineFont
from openpyxl.cell.rich_text import CellRichText, TextBlock, TextBlock

from tools              import env
from openpyxl.utils import range_boundaries
from tools import logger

logger = logger.get_logger(__name__)

market_et_path = f'{env.proj_dir}/et/0524市调表.xlsx'
save_path = f'{env.proj_dir}/et/market_et_test.xlsx'
workbook = load_workbook(market_et_path)
worksheet = workbook.active
#target = find_last_filled_cell(worksheet, 'A1:A50')
#target_row = target.row
#breakpoint()
#
#workday = next_tuesday_or_saturday(target.value)
#
##if date.today().weekday() == 1 or date.today().weekday() == 5:
##    workday = date.today()
#
#append_date(worksheet, target.row, workday)
#
#print(worksheet['A34'].value)
#
#def copy_firm(column_letter, start_row):
#    '''
#    column_letter   : string,
#    start_row       : int
#        '''
#
#    for i in range(4):
#        worksheet[f'{column_letter}{start_row+4}'].value = worksheet[f'{column_letter}{start_row}'].value
#        start_row -= 1
#
#copy_firm('B', target_row)
#copy_firm('D', target_row)
#copy_firm('F', target_row)
#
workbook.save(save_path)
