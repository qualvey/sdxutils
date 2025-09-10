from openpyxl import load_workbook
import tkinter as tk
from datetime import datetime, date, timedelta
from tools import env
from tools.logger import get_logger
import sys

import sqlite3
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt
from datetime import datetime

logger = get_logger(__name__)
#用电量使用整数
class UserCanceledException(Exception):
    pass



class InputWindow(QWidget):
    def __init__(self, search_date:datetime):
        super().__init__()
        self.value = None
        self.setWindowTitle("输入电表数据")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        self.label_title = QLabel(f"请输入用电量：{search_date.strftime('%Y-%m-%d')}")
        layout.addWidget(self.label_title, alignment=Qt.AlignCenter)

        self.entry = QLineEdit()
        layout.addWidget(self.entry)

        self.btn = QPushButton("确认")
        self.btn.clicked.connect(self.on_submit)
        layout.addWidget(self.btn, alignment=Qt.AlignCenter)

        self.label_status = QLabel("")
        layout.addWidget(self.label_status, alignment=Qt.AlignCenter)

        self.entry.returnPressed.connect(self.on_submit)

        self.setLayout(layout)

    def on_submit(self):
        try:
            self.value = float(self.entry.text())
            self.close()
        except ValueError:
            self.label_status.setText("请输入有效数字")

def GUI_input(search_date:str) -> float | None:
    app = QApplication(sys.argv)
    window = InputWindow(search_date)
    window.show()
    app.exec()

    if window.value is None:
        raise UserCanceledException("用户未输入有效电量，退出。")
    return window.value

def init_db():
# 连接到 SQLite 数据库（如果文件不存在，会自动创建）
    db_path = f'{env.proj_dir}/energy_data.db'
    conn = sqlite3.connect(db_path)
    print(f'db_path is : {db_path}')
  
    cursor = conn.cursor()
# 创建表（如果不存在）
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS daily_energy_consumption (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_date DATE NOT NULL UNIQUE,
        energy_consumed REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
    cursor.execute(create_table_query)
    conn.commit()
def get_ele_usage(search_date):
    app = QApplication(sys.argv)
    window = InputWindow(search_date)
    window.show()
    app.exec()

    if window.value is None:
        raise UserCanceledException("用户未输入有效电量，退出。")
    return window.value

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def update_sql_elec(record_date, energy_consumed):
    init_db()

    conn = sqlite3.connect(f'{env.proj_dir}/energy_data.db')
    cursor = conn.cursor()
    '''
        record_date <datetime.datetime>
        energy_consumed <float>
    '''
    record_date = record_date.strftime('%Y-%m-%d')
    try:
        insert_query = '''
        INSERT INTO daily_energy_consumption (record_date, energy_consumed)
        VALUES (?, ?)
        ON CONFLICT(record_date) DO UPDATE SET energy_consumed = excluded.energy_consumed;
        '''
        cursor.execute(insert_query, (record_date, energy_consumed))
        conn.commit()
        print("数据插入成功")
    except sqlite3.Error as err:
        print(f"插入数据时发生错误: {err}")

# 定义查询日期
def query_data(date_str):

    conn = sqlite3.connect(f'{env.proj_dir}/energy_data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT energy_consumed FROM daily_energy_consumption WHERE record_date = ?', (date_str,))

    rows = cursor.fetchall()
    for row in rows:
        print(row)
        return(row[0])

elecSheet   = env.elecUsage_file

wb = load_workbook(elecSheet)
#data_only = True 获取数据而不是公式
#dataonly不能保存，保存就破坏公式了
ws = wb.active

def get_row_by_date(worksheet,date:datetime,start_cell="A1",end_cell="A35") -> int | None:
    date_str:str = date.date()
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
                    if cell.value.date() == date_str:  # 对比日期部分
                        #breakpoint()
                        return cell.row  # 直接返回行号

        return None  # 未找到匹配值

    except KeyError:
        print(f"错误: {start_cell} 或 {end_cell} 可能超出了工作表范围")
        return None

class UserCancledException(Exception):
    pass
def write_elecxl(elec_usage, target_row, destination):
    if not target_row :
        print('电表有问题，未获取正确的位置')
        return 
    ws[f"B{target_row}"].value = elec_usage
    wb.save(elecSheet)
    wb.save(destination)

def get_elecUsage(datetime_obj: datetime) -> float:
    search_date = datetime_obj
    if_exist = query_data(search_date.strftime('%Y-%m-%d'))

    if if_exist:
        logger.warning('该日期已经存在电表数据，如果要修改，请手动操作sqlite')
        ele_usage = if_exist
    else:
        # GUI 输入窗口
        ele_usage = get_ele_usage(search_date)
        update_sql_elec(datetime_obj, ele_usage)

    # 计算差值
    previous_day = datetime_obj - timedelta(days=1)
    previous_day_str = previous_day.strftime('%Y-%m-%d')
    previous_day_value = query_data(previous_day_str)
    logger.info(previous_day_value)

    if previous_day_value:
        result = ele_usage - previous_day_value
    else:
        logger.warning(f'前一天<{previous_day}>的数据不存在,是否添加? y<int>/n')
        user_input = input(f'输入 y 紧跟电表数据，例如 y123.4，或 n 退出\n').strip().lower()
        if user_input.startswith("y") and is_float(user_input[1:]):
            pre_day_value = float(user_input[1:])
            result = ele_usage - pre_day_value

            conn = sqlite3.connect(f'{env.proj_dir}/energy_data.db')
            cursor = conn.cursor()
            record_date = previous_day.strftime('%Y-%m-%d')

            try:
                cursor.execute('''
                    INSERT INTO daily_energy_consumption (record_date, energy_consumed)
                    VALUES (?, ?)
                    ON CONFLICT(record_date) DO UPDATE SET energy_consumed = excluded.energy_consumed;
                ''', (record_date, pre_day_value))
                conn.commit()
                print("数据插入成功")
            except sqlite3.Error as err:
                print(f"插入数据时发生错误: {err}")
            finally:
                cursor.close()
                conn.close()
        else:
            logger.warning(f"user_input 无效: {user_input}")
            raise UserCancledException("用户取消，电表模块退出")

    result = result * 80
    return int(round(result))

if __name__ == "__main__":
    a = get_row_by_date(ws, "a")
    #breakpoint()
