# gui_main.py

import os,sys, json, subprocess,threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from datetime               import datetime,  timedelta 
# from meituan.main       import get_meituanSum,  get_mtgood_rates

from tools import  logger as mylogger
from operation import OTAUpdater
logger = mylogger.get_logger(__name__)

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QLineEdit,QMessageBox
)
#这种导入方式在pyinstall打包后会报错
# from . import OperationWorker,SpecialFeeWorker,ElecWorker,DouyinWorker
from GUI.operation_worker import OperationWorker
from GUI.specialFee_worker import SpecialFeeWorker
from GUI.elec_worker import ElecWorker
from GUI.douyinWorker import DouyinWorker

from GUI.meituanWorker import MeituanWorker
from xlutils import Wshandler

CONFIG_PATH = os.path.expanduser("~/.myapp_config.json")

#点击开始，根据UI层面的参数，调用各个模块的接口，完成业务逻辑

class MyApp(QWidget):
    working_datetime = datetime.combine(datetime.today() - timedelta(days=1), datetime.min.time())
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数呆熊报表自动化工具")
        self.setGeometry(100, 100, 400, 180)
        self.last_dir = os.path.expanduser("~")  # 默认初始目录为用户主目录
        self.selected_file = "~/Documents/日报表模板.xlsx"  # 用户选择的输入文件路径
        self.output_dir = self.last_dir  # 默认输出目录同上次目录
        self.save_name = "a.xlsx"
        self.output_file = os.path.join(self.output_dir,self.save_name) # 用户选择的保存文件路径

        yesterday = datetime.today() - timedelta(days=1)
        self.working_date = datetime.combine(yesterday, datetime.min.time())
        self.results = {}
        self.workers = []
        self.completed_count = 0
        self.electric_meter_value = 0
        self.machine_count = 76
        self.load_config()
        self.init_ui()
        self.machian_sum = 76

    def handle_finished(self, name, data):
        self.results[name] = data   # 按 name 存储每个任务的数据
        self.results['machine_count'] = self.machian_sum
        self.completed_count += 1
        print(f"任务 {name} 完成，当前完成数: {self.completed_count}/{len(self.workers)}")
        if self.completed_count == len(self.workers):
            self.all_done()
    
    def all_done(self):
        self.completed_count = 0
        infomation = json.dumps(self.results, indent=4, ensure_ascii=False)
        logger.info(f"所有任务完成，结果: {infomation}")
        otaworker = OTAUpdater(self.results, self.working_date)
        thread_ota  = threading.Thread(target=otaworker.run, daemon=True)
        thread_ota.start()
        genws = Wshandler(self.working_date, self.selected_file , self.output_file, self.results)
        genws.run()
        self.results = {}
        QMessageBox.information(self, "完成", "所有数据处理完成，报表已生成！")
        self.workers = []   

    def start_douyin(self):
        self.douyin_worker = DouyinWorker("douyin",self.working_datetime)
        self.douyin_worker.finished.connect(self.handle_finished)
        self.douyin_worker.error.connect(self.on_douyin_error)
        self.douyin_worker.start()  
        self.workers.append(self.douyin_worker)    
                                                 
    def start_meituan_fetch(self):  
        self.meituan_worker = MeituanWorker("meituan",self.working_datetime)
        self.meituan_worker.finished.connect(self.handle_finished)
        self.meituan_worker.error.connect(self.on_douyin_error)
        self.meituan_worker.start()
        self.workers.append(self.meituan_worker)

    def get_special_data(self):
        self.special_worker = SpecialFeeWorker('specialfee',self.working_datetime)
        self.special_worker.finished.connect(self.handle_finished)
        self.special_worker.error.connect(self.on_special_error)
        self.special_worker.start()
        self.workers.append(self.special_worker)
        # self.special_worker.wait()

    def start_elec_fetch(self):
        self.elec_worker = ElecWorker('elecworker',self.working_datetime)
        self.elec_worker.finished.connect(self.handle_finished)
        self.elec_worker.error.connect(self.on_elec_error)
        self.elec_worker.start()
        self.workers.append(self.elec_worker)
    def get_op_data(self):
        self.worker = OperationWorker('operation', self.working_datetime)
        self.worker.finished.connect(self.handle_finished)
        self.worker.error.connect(self.on_op_error)
        self.worker.start()
        self.workers.append(self.worker)


    def run_report(self):

        # 获取美团、抖音、运营等数据
        self.start_meituan_fetch()  # 启动美团数据获取线程
        self.get_op_data()          # 启动运营数据获取线程
        self.get_special_data()     # 获取特免数据
        self.start_douyin()         # 获取抖音数据
        self.start_elec_fetch()      # 获取电表数据

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
                logger.info(f'outputfile{self.output_file}')   
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
            "save_name": self.save_name or None,
            # "cookies":{
            #     "mt": self.mt_cookie,
            #     "dy": self.dy_cookie
            # }
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存配置文件失败: {e}")

    def init_ui(self):
        layout = QVBoxLayout()
        h_layout = QHBoxLayout()
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
        # layout.addWidget(self.save_name_edit)
        #用嵌套的h_layout显示
        h_layout.addWidget(self.save_name_edit)
        # 按钮
        self.show_in_explorer_btn = QPushButton("在 Explorer 中显示")
        self.show_in_explorer_btn.setStyleSheet("font-size: 15px;")
        h_layout.addWidget(self.show_in_explorer_btn)

        # 按钮点击事件
        def open_in_explorer():
            file_path = self.output_file
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            if os.path.exists(file_path):
                if sys.platform.startswith("win"):
                    subprocess.run(f'explorer /select,"{file_path}"')
                elif sys.platform.startswith("darwin"):
                    subprocess.run(["open", "-R", file_path])
                else:
                    subprocess.run(["xdg-open", os.path.dirname(file_path)])
            else:
                print("文件不存在:", file_path)

        self.show_in_explorer_btn.clicked.connect(open_in_explorer)
        layout.addLayout(h_layout)

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
            self.selected_file = "~/Documents/日报表模板.xlsx"
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


    def on_op_error(self, msg: str):
        # 弹窗提示
        box = QMessageBox(self)
        box.setWindowTitle("运营数据错误")
        box.setText(msg)
        box.exec()

    def on_douyin_error(self, msg: str):
        # 弹窗提示
        box = QMessageBox(self)
        box.setWindowTitle("抖音数据错误")
        box.setText(msg)
        box.exec()
        
    def on_special_error(self, msg: str):
        # 弹窗提示
        box = QMessageBox(self)
        box.setWindowTitle("特免数据错误")
        box.setText(msg)
        box.exec()
    def on_elec_error(self, msg: str):
        # 弹窗提示
        box = QMessageBox(self)
        box.setWindowTitle("电表数据错误")
        box.setText(msg)
        box.exec()
    def closeEvent(self, event):
        for worker in self.workers:
            if worker.isRunning():
                worker.quit()
                worker.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    my_app = MyApp()
    my_app.show()
    sys.exit(app.exec())
# 启动主程序入口
if __name__ == "__main__":
    main()

