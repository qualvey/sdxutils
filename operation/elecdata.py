from openpyxl import load_workbook, Workbook
from openpyxl.utils import coordinate_to_tuple

import tkinter as tk
from datetime import datetime, date, timedelta

from tools import env
from tools.logger import get_logger

import sqlite3

logger = get_logger(__name__)

class UserCancledException(Exception):
    pass

#表解构
#sqlite> PRAGMA table_info(daily_energy_consumption);
# 0|id|INTEGER|0||1
# 1|record_date|DATE|1||0
# 2|energy_consumed|REAL|1||0
# 3|created_at|TIMESTAMP|0|CURRENT_TIMESTAMP|0
class ElecDataService:
    #参数： date: 查询的日期
    #      db_path: sqlite数据库文件路径，默认在项目目录下
    def __init__(self,date:datetime,db_path:str = f'{env.proj_dir}/energy_data.db'):
        logger.info("ElecDataService init")
        logger.info(f"数据库路径: {db_path}")
        self.date = date
        self.db_path = db_path
        # self.value = value
        # 连接到 SQLite 数据库（如果文件不存在，会自动创建）
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    # 创建表（如果不存在）
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS daily_energy_consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date DATE NOT NULL UNIQUE,
            energy_consumed REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def is_float(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def update_sql(self,record_date:datetime, energy_consumed:float):
        print(f"更新数据库，日期: {record_date}, 用电量: {energy_consumed} 0099")    

        record_date_str:str = record_date.strftime('%Y-%m-%d')
        try:
            insert_query = '''
            INSERT INTO daily_energy_consumption (record_date, energy_consumed)
            VALUES (?, ?)
            ON CONFLICT(record_date) DO UPDATE SET energy_consumed = excluded.energy_consumed;
            '''
            self.cursor.execute(insert_query, (record_date_str, energy_consumed))
            self.conn.commit()
            print("数据插入成功")
        except sqlite3.Error as err:
            print(f"插入数据时发生错误: {err}")

    # 定义查询日期
    def query_sql(self,date_str:str) -> float | None:
        self.cursor.execute('SELECT energy_consumed FROM daily_energy_consumption WHERE record_date = ?', (date_str,))
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)
            return(row[0])
    # from openpyxl.utils import coordinate_to_tuple  # Already imported at the top
    from openpyxl.utils import coordinate_to_tuple

    from openpyxl.worksheet.worksheet import Worksheet
    @staticmethod
    def get_row_by_date(worksheet:Worksheet, date:datetime, start_cell="A1", end_cell="A35") -> int | None:
        date_str:str = str(date.date())
        try:
            min_row, min_col = coordinate_to_tuple(start_cell)
            max_row, max_col = coordinate_to_tuple(end_cell)

            for row in worksheet.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
                for cell in row:
                    if isinstance(cell.value, datetime):  # 确保是 datetime 类型
                        if cell.value.date() == date.date():  # 对比日期部分
                            #breakpoint()
                            return cell.row  # 直接返回行号

            return None  # 未找到匹配值

        except KeyError:
            # Removed nested UserCancledException definition; now defined at module level
            return None

    def get_elecUsage(self) -> float:
        search_date = self.date
        if_exist = self.query_sql(search_date.strftime('%Y-%m-%d'))

        if if_exist:
            logger.warning('该日期已经存在电表数据，如果要修改，请手动操作sqlite')
            ele_usage = if_exist
        else:
            # GUI 输入窗口
            root = tk.Tk()
            root.title("输入电表数据")
            root.geometry('300x150')

            input_result = {'value': 0.0  }

            def on_enter_pressed(event=None):
                val = entry.get()
                try:
                    input_result['value'] = float(val)
                    root.quit()
                except ValueError:
                    label.config(text="请输入有效数字")

            tk.Label(root, text=f"请输入用电量：{search_date.strftime('%Y-%m-%d')}").pack(pady=10)
            entry = tk.Entry(root)
            entry.pack()
            entry.bind("<Return>", on_enter_pressed)

            tk.Button(root, text="确认", command=on_enter_pressed).pack(pady=10)
            label = tk.Label(root, text="")
            label.pack()

            root.mainloop()
            root.destroy()

            if input_result['value'] is None:
                raise UserCancledException("用户未输入有效电量，退出。")

            ele_usage = input_result['value']
            self.update_sql(search_date, ele_usage)

        # 计算差值
        previous_day = self.date - timedelta(days=1)
        previous_day_str = previous_day.strftime('%Y-%m-%d')
        previous_day_value = self.query_sql(previous_day_str)
        logger.info(f'前一天:{previous_day_value}')

        if previous_day_value:
            result = ele_usage - previous_day_value
            logger.info(f'用电量{result}')
        else:
            logger.warning(f'前一天<{previous_day}>的数据不存在,是否添加? y<int>/n')
            user_input = input(f'输入 y 紧跟电表数据，例如 y123.4，或 n 退出\n').strip().lower()
            if user_input.startswith("y") and self.is_float(user_input[1:]):
                pre_day_value = float(user_input[1:])
                result = ele_usage - pre_day_value
              
                record_date = previous_day.strftime('%Y-%m-%d')

                try:
                    self.cursor.execute('''
                        INSERT INTO daily_energy_consumption (record_date, energy_consumed)
                        VALUES (?, ?)
                        ON CONFLICT(record_date) DO UPDATE SET energy_consumed = excluded.energy_consumed;
                    ''', (record_date, pre_day_value))
                    self.conn.commit()
                    print("数据插入成功")
                except sqlite3.Error as err:
                    print(f"插入数据时发生错误: {err}")
                finally:
                    self.cursor.close()
                    self.conn.close()
            else:
                logger.warning(f"user_input 无效: {user_input}")
                raise UserCancledException("用户取消，电表模块退出")

        result = result * 80
        return float(result)

if __name__ == "__main__":
    ee = ElecDataService(datetime(2025,9,15))