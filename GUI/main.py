
# 保证根目录在 sys.path，便于包导入
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# gui_main.py

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
from tools import  logger as mylogger
logger = mylogger.get_logger(__name__)
# from xlutils.xlUtil import *
import xlutils.xlUtil as xlutils

machian_sum = 76

from typing import cast, Optional, Tuple
from decimal import Decimal
import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QLineEdit, QDoubleSpinBox
)

CONFIG_PATH = os.path.expanduser("~/.myapp_config.json")
class MyApp(QWidget):
    # 缺省参数常量
    DEFAULT_MT = 0
    DEFAULT_MT_LEN = 0
    DEFAULT_DY = 0
    DEFAULT_DY_LEN = 0
    DEFAULT_ENGLISH = {}
    DEFAULT_SPECIAL_SUM = 0
    DEFAULT_SPECIAL_LIST = []
    DEFAULT_ELEC_USAGE = 0.0
    DEFAULT_WS = None

    def run_report(self):
        yesterday = datetime.today() - timedelta(days=1)
        working_datetime = datetime.combine(yesterday, datetime.min.time())
        working_date_str = yesterday.strftime('%Y-%m-%d')

        # 获取美团、抖音、运营等数据
        try:
            mt, mt_len = get_meituanSum(working_datetime)
        except Exception:
            mt, mt_len = self.DEFAULT_MT, self.DEFAULT_MT_LEN
        try:
            douyindata = final_out(working_datetime)
            if douyindata and douyindata[0] is not None and douyindata[1] is not None:
                dy, dy_len = douyindata
            else:
                dy, dy_len = self.DEFAULT_DY, self.DEFAULT_DY_LEN
        except Exception:
            dy, dy_len = self.DEFAULT_DY, self.DEFAULT_DY_LEN
        try:
       
            english = resolve_operation_data(working_datetime)
            if not english:
                english = self.DEFAULT_ENGLISH
        except Exception:
            english = self.DEFAULT_ENGLISH
        try:
            print(f"获取特免数据")
            specialFee_list, special_sum = specialFee.get_specialFee(working_datetime)
        except Exception:
            specialFee_list, special_sum = self.DEFAULT_SPECIAL_LIST, self.DEFAULT_SPECIAL_SUM
        try:
            elec_usage = electron.get_elecUsage(working_datetime)
        except Exception:
            elec_usage = self.DEFAULT_ELEC_USAGE

        # 初始化表格
        try:
            print(f"使用的模板文件是: {self.selected_file}")
            source_file = self.selected_file if self.selected_file is not None else ""
            wb = xlutils.init_sheet(working_datetime, source_file=source_file)
            ws = wb.active
        except Exception:
            print("表格初始化失败，使用缺省值")
            ws = self.DEFAULT_WS
            wb = None

        # 业务逻辑
        if ws and wb is not None:
            missing_dates = xlutils.find_missing_dates(ws, working_datetime)
            logger.info(f'缺失数据的日期有: {missing_dates}')
            data_pure = xlutils.load_data(
                elec_usage, mt, float(dy), english, {
                    "网费充值": "amountFee",
                    "提现本金": "withdrawPrincipal",
                    "找零": "checkoutDeposit",
                    "零售": "retail",
                    "水吧": "waterBar",
                    "代购": "agent",
                    "退款": "totalRefundFee",
                    "报销": None,
                    "在线支付": "onlineIn",
                    "奖励金": "awardFee",
                    "卡券": "cardVolumeFee",
                    "特免": "specialFree",
                    "网费消耗": "totalConsumeNetworkFee",
                    "上机人次": "onlineTimes",
                    "上机时长": "duration",
                    "点单率": "orderRate",
                    "新会员": "newMember"
                }
            )
            if data_pure['特免'] != special_sum:
                logger.warning(f"特免金额不匹配，请检查!!运营数据中是{data_pure['特免']},订单列表中计算出来是{special_sum}")
            else:
                logger.info(f"特免金额匹配，pass.")

            xlutils.insert_data(ws, data_pure, working_datetime, machian_sum=self.machine_count)
            xlutils.special_mark(ws=ws, special_data=specialFee_list, start_col='H', end_col='K')
            mt_good_num = get_mtgood_rates(working_datetime.strftime('%Y-%m-%d'))
            dy_good_num = get_dygood_rate(working_datetime)
            xlutils.ota_comment(ws, mt_len, dy_len, mt_good_num, dy_good_num, 'H')
            xlutils.handle_headers(ws)
            # 保存路径由用户选择
            save_path = self.output_file
            if not save_path:
                # 如果未选择，自动生成一个默认路径
                default_name = "日报表.xlsx"
                if self.selected_file:
                    default_name = os.path.splitext(os.path.basename(self.selected_file))[0] + "_日报表.xlsx"
                save_path = os.path.join(self.last_dir, default_name)
                self.output_file = save_path
            save_dir = os.path.dirname(save_path)
            os.makedirs(save_dir, exist_ok=True)
            xlutils.save(save_path, wb, source_file=self.selected_file, dir_str=save_dir)
            print(f"报表已保存: {save_path}")
        else:
            print("表格初始化失败，无法生成报表。")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("数呆熊报表自动化工具")
        self.setGeometry(100, 100, 400, 180)
        self.last_dir = os.path.expanduser("~")  # 默认初始目录为用户主目录
        self.selected_file = None
        self.output_dir = self.last_dir  # 默认输出目录同上次目录
        self.save_name = "a.xlsx"
        self.output_file = os.path.join(self.output_dir,self.save_name) # 用户选择的保存文件路径
        
        self.electric_meter_value = 0
        self.machine_count = 76
        self.load_config()
        self.init_ui()

    def load_config(self):
        """加载配置文件（如上次保存目录、选中文件等）"""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.last_dir = config.get("last_dir", self.last_dir)
                self.output_dir = config.get("output_dir", self.output_dir)
                self.save_name = config.get("save_name", "日报表.xlsx")   
                self.selected_file = config.get("selected_file", self.selected_file)
                self.output_file = os.path.join(self.output_dir, self.save_name)    
                self.electric_meter_value = config.get("electric_meter_value", self.electric_meter_value)
                self.machine_count = config.get("machine_count", self.machine_count)
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        else:
            logger.info("没有配置文件")
            # 没有配置文件，使用默认值
            pass

    def save_config(self):
        """保存配置文件"""
        config = {
            "last_dir": self.last_dir,
            "selected_file": self.selected_file,
            "electric_meter_value": self.electric_meter_value,
            "machine_count": self.machine_count,
            "output_dir":self.output_dir,
            "save_name": self.save_name or None
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存配置文件失败: {e}")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)

        # 显示选中文件路径
        self.file_label = QLabel(self.selected_file or "未选择文件")
        self.file_label.setStyleSheet("font-size: 15px; color: #333;")
        layout.addWidget(self.file_label)

        # 文件选择按钮
        self.select_file_btn = QPushButton("选择输入模板文件")
        self.select_file_btn.setFixedSize(180, 36)
        self.select_file_btn.setStyleSheet(
            "font-size: 15px; background-color: #4CAF50; color: white; border-radius: 6px;"
        )
        self.select_file_btn.clicked.connect(self.select_file)
        file_btn_layout = QHBoxLayout()
        file_btn_layout.addStretch()
        file_btn_layout.addWidget(self.select_file_btn)
        file_btn_layout.addStretch()
        layout.addLayout(file_btn_layout)

        # 目标保存目录选择
        self.save_dir_label = QLabel(self.output_dir or self.last_dir or "未选择保存目录")
        self.save_dir_label.setStyleSheet("font-size: 15px; color: #333;")
        layout.addWidget(self.save_dir_label)

        self.select_save_dir_btn = QPushButton("选择保存目录")
        self.select_save_dir_btn.setFixedSize(180, 36)
        self.select_save_dir_btn.setStyleSheet(
            "font-size: 15px; background-color: #FF9800; color: white; border-radius: 6px;"
        )
        self.select_save_dir_btn.clicked.connect(self.select_save_dir)
        save_dir_btn_layout = QHBoxLayout()
        save_dir_btn_layout.addStretch()
        save_dir_btn_layout.addWidget(self.select_save_dir_btn)
        save_dir_btn_layout.addStretch()
        layout.addLayout(save_dir_btn_layout)

        # 文件名输入框
        default_name = "python.xlsx"
        if self.selected_file:
            default_name = os.path.splitext(os.path.basename(self.selected_file))[0] + "py.xlsx"
        self.save_name_edit = QLineEdit(default_name)
        self.save_name_edit.setPlaceholderText("保存文件名")
        self.save_name_edit.setStyleSheet("font-size: 15px;")
        self.save_name_edit.setText(self.save_name or default_name or "输入文件名")
        self.save_name_edit.textChanged.connect(self.update_save_name)
        layout.addWidget(self.save_name_edit)

        # 保存文件路径显示标签
        self.save_file_label = QLabel(self.output_file or "未选择保存文件")
        self.save_file_label.setStyleSheet("font-size: 15px; color: #333;")
        layout.addWidget(self.save_file_label)

        # 创建开始按钮
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setFixedSize(120, 40)
        self.start_btn.clicked.connect(self.run_report)  # 点击连接方法
        layout.addWidget(self.start_btn)

        self.setLayout(layout)
    def update_save_name(self, text):
        self.save_name = self.save_name_edit.text().strip()
        self.output_file = os.path.join(self.output_dir, self.save_name)
        self.save_config()
        self.save_file_label.setText(self.output_file)
        if self.output_dir:
            self.save_dir_label.setText(self.output_file)
        
    def select_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录", self.last_dir)
        if dir_path:
            self.output_dir = dir_path
            self.save_dir_label.setText(dir_path)
            
            self.output_file = os.path.join(self.output_dir, self.save_name_edit.text().strip() or "日报表.xlsx")
            self.save_config()
            self.save_file_label.setText(self.output_file)
        else:
            self.save_dir_label.setText("未选择保存目录")

    def on_machine_changed(self, value):
        self.machine_count = int(value)
        print(f"机器数量变为: {self.machine_count}")

    def on_meter_changed(self, value):
        self.electric_meter_value = value
        print(f"电表数据变为: {self.electric_meter_value}")

    def select_file(self):
        # 使用上次选择的目录作为起始目录
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择模板文件",
            self.last_dir,
            "所有文件 (*.*)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(file_path)
            # 更新 last_dir 为当前选择文件所在目录
            self.last_dir = os.path.dirname(file_path)
            self.save_config()
        else:
            self.file_label.setText("未选择文件")
            self.selected_file = None
    def update_view(self):
        if self.selected_file:
            self.file_label.setText(self.selected_file)
        else:
            self.file_label.setText("未选择文件")
        if self.output_dir:
            self.save_dir_label.setText(self.output_dir)
        else:
            self.save_dir_label.setText("未选择保存目录")
        if self.output_file:
            self.save_file_label.setText(self.output_file)
        else:
            self.save_file_label.setText("未选择保存文件")

    def start_process(self):
        # 只调用run_report，所有业务逻辑和异常在run_report中处理
        self.run_report()


# 启动主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
