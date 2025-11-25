# gui_main.py

import os,sys, json, subprocess,threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime               import datetime,  timedelta 
# from meituan.main       import get_meituanSum,  get_mtgood_rates

from operation import OTAUpdater
from tools import LoggerService
logger = LoggerService(__name__).logger

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QLineEdit,QMessageBox
)
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QDateEdit
from PySide6.QtCore import QDate
from PySide6.QtCore import QTimer, Qt
import time
from PySide6.QtGui import QPixmap, QImage
import signal
#这种导入方式在pyinstall打包后会报错
# from . import OperationWorker,SpecialFeeWorker,ElecWorker,DouyinWorker
from GUI.operation_worker import OperationWorker
from GUI.specialFee_worker import SpecialFeeWorker
from GUI.elec_worker import ElecWorker
from GUI.douyinWorker import DouyinWorker

from GUI.meituanWorker import MeituanWorker
from xlutils import Wshandler
from tools.login import loginservice

CONFIG_PATH = os.path.expanduser("~/.myapp_config.json")

#点击开始，根据UI层面的参数，调用各个模块的接口，完成业务逻辑

from PySide6.QtCore import Signal

class MyApp(QWidget):
    working_datetime = datetime.combine(datetime.today() - timedelta(days=1), datetime.min.time())
    show_signal = Signal(object)  # 用于显示二维码的信号
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数呆熊报表自动化工具")
        # 连接信号到槽
        self.show_signal.connect(self._show_qr)
        self.setGeometry(100, 100, 400, 180)
        self.last_dir = os.path.expanduser("~")  # 默认初始目录为用户主目录
        self.selected_file = "~/Documents/日报表模板.xlsx"  # 用户选择的输入文件路径
        self.output_dir = self.last_dir  # 默认输出目录同上次目录
        self.save_name = "a.xlsx"
        self.output_file = os.path.join(self.output_dir,self.save_name) # 用户选择的保存文件路径
        #这里还是反斜杠
        # 默认工作日期为昨天（午夜）
        self.working_date = datetime.combine(datetime.today() - timedelta(days=1), datetime.min.time())
        # keep a QDate-based datetime used by workers
        self.working_datetime = self.working_date
        self.results = {}
        self.token = ""
        self.workers = []
        self.completed_count = 0
        self.electric_meter_value = 0
        self.machine_sum = 76
        self.login_service = loginservice()
        self.load_config()
        self.init_ui()
        self.start_login()

    def handle_finished(self, name, data):
        self.results[name] = data   # 按 name 存储每个任务的数据
        self.results['machine_count'] = self.machine_sum
        self.completed_count += 1
        print(f"任务 {name} 完成，当前完成数: {self.completed_count}/{len(self.workers)}")
        if self.completed_count == len(self.workers):
            self.all_done()
    
    def all_done(self):
        self.completed_count = 0
        infomation = json.dumps(self.results, indent=4, ensure_ascii=False)
        logger.info(f"所有任务完成，结果: {infomation}")
        
        otaworker = OTAUpdater(self.results, self.working_date,self.token)
        thread_ota  = threading.Thread(target=otaworker.run, daemon=True)
        thread_ota.start()
        genws = Wshandler(self.working_date, self.selected_file , self.output_file, self.results)
        genws.run()
        self.results = {}
        self.workers = []   
        # 如果是批量模式，继续下一个日期
        if getattr(self, 'batch_mode', False):
            # pop next date from pending list
            if hasattr(self, 'batch_dates') and self.batch_dates:
                next_date = self.batch_dates.pop(0)
                self.set_date_and_run(next_date)
                return
            else:
                # 批量完成，清理
                self.batch_mode = False
                QMessageBox.information(self, "完成", "所有数据处理完成，报表已生成！")
        QMessageBox.information(self, "完成", "所有数据处理完成，报表已生成！")


    def start_douyin(self):
        self.douyin_worker = DouyinWorker("douyin",self.working_datetime)
        self.douyin_worker.finished.connect(self.handle_finished)
        self.douyin_worker.error.connect(self.on_douyin_error)
        self.douyin_worker.start()  
        self.workers.append(self.douyin_worker)    
                                                 
    def start_meituan_fetch(self):  
        self.meituan_worker = MeituanWorker("meituan",self.working_datetime)
        self.meituan_worker.finished.connect(self.handle_finished)
        self.meituan_worker.error.connect(self.on_meituan_error)
        self.meituan_worker.start()
        self.workers.append(self.meituan_worker)

    def get_special_data(self):
        self.special_worker = SpecialFeeWorker('specialfee',self.working_datetime,self.token)
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
        self.worker = OperationWorker('operation', self.working_datetime,self.token)
        self.worker.finished.connect(self.handle_finished)
        self.worker.error.connect(self.on_op_error)
        self.worker.start()
        self.workers.append(self.worker)

    def run_report(self):

        # 如果是批量模式，先构建日期列表并开始第一个日期
        if getattr(self, 'batch_mode', False):
            # build date list from start_date to end_date inclusive
            start_q = self.start_date_edit.date()
            end_q = self.end_date_edit.date()
            start_dt = datetime(start_q.year(), start_q.month(), start_q.day())
            end_dt = datetime(end_q.year(), end_q.month(), end_q.day())
            if start_dt > end_dt:
                QMessageBox.warning(self, "日期错误", "开始日期必须早于或等于结束日期")
                return
            days = (end_dt - start_dt).days + 1
            self.batch_dates = [start_dt + timedelta(days=i) for i in range(days)]
            # mark batch_mode and start first
            self.batch_mode = True
            first = self.batch_dates.pop(0)
            self.set_date_and_run(first)
            return

        # 单日模式：获取美团、抖音、运营等数据
        self.start_meituan_fetch()  # 启动美团数据获取线程
        self.get_op_data()          # 启动运营数据获取线程
        self.get_special_data()     # 获取特免数据
        self.start_douyin()         # 获取抖音数据
        self.start_elec_fetch()      # 获取电表数据

    def set_date_and_run(self, date_dt: datetime):
        """Set working_date/workers and adjust output filename, then start workers for this date."""
        # set working date (datetime at midnight)
        self.working_date = datetime.combine(date_dt.date(), datetime.min.time())
        self.working_datetime = self.working_date
        # adjust output file name to include date suffix before extension
        base, ext = os.path.splitext(self.save_name or "日报表.xlsx")
        date_suffix = self.working_date.strftime("%Y%m%d")
        filename = f"{base}_{date_suffix}{ext}"
        self.output_file = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.join(self.output_dir, filename))))
        self.save_file_label.setText(self.output_file)
        # start the normal workers
        self.start_meituan_fetch()
        self.get_op_data()
        self.get_special_data()
        self.start_douyin()
        self.start_elec_fetch()

    def on_batch_toggled(self, state):
        enabled = state == 2 or state == True
        self.batch_mode = enabled
        # enable/disable start/end date editors
        self.start_date_edit.setEnabled(enabled)
        self.end_date_edit.setEnabled(enabled)

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
                # normalize paths from config to platform-native format
                outpath = os.path.join(self.output_dir, self.save_name)
                self.output_file = os.path.normpath(os.path.abspath(os.path.expanduser(outpath)))
                logger.info(f'outputfile   kf{self.output_file}')   
                self.electric_meter_value = config.get("electric_meter_value", self.electric_meter_value)
                self.machine_sum = config.get("machine_sum", self.machine_sum)
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
            "machine_sum": self.machine_sum,
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

        # 日期选择控件（默认昨天）
        date_layout = QHBoxLayout()
        date_label = QLabel("选择日期：")
        date_label.setStyleSheet("font-size: 15px; color: #333;")
        date_layout.addWidget(date_label)

        # 单日选择
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        try:
            qd = QDate(self.working_date.year, self.working_date.month, self.working_date.day)
        except Exception:
            qd = QDate.currentDate().addDays(-1)
        self.date_edit.setDate(qd)
        self.date_edit.dateChanged.connect(self.update_working_date)
        date_layout.addWidget(self.date_edit)

        # 批量选择开关
        self.batch_checkbox = QCheckBox("批量生成")
        self.batch_checkbox.stateChanged.connect(self.on_batch_toggled)
        date_layout.addWidget(self.batch_checkbox)

        # 批量开始/结束日期（默认昨天），初始禁用
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(qd)
        self.start_date_edit.setEnabled(False)
        date_layout.addWidget(QLabel("开始："))
        date_layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(qd)
        self.end_date_edit.setEnabled(False)
        date_layout.addWidget(QLabel("结束："))
        date_layout.addWidget(self.end_date_edit)

        layout.addLayout(date_layout)

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
            logger.debug("filepath"+file_path)
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

        # --- 登录区域（显示二维码 + 登录按钮）
        login_layout = QHBoxLayout()
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(200, 200)
        self.qr_label.setStyleSheet("border: 1px solid #ccc; background: #fff;")
        login_layout.addWidget(self.qr_label)

        login_btn_layout = QVBoxLayout()
        self.login_btn = QPushButton("扫码登录")
        self.login_btn.setFixedSize(120, 36)
        self.login_btn.clicked.connect(self.start_login)
        login_btn_layout.addWidget(self.login_btn)
        login_btn_layout.addStretch()
        login_layout.addLayout(login_btn_layout)
        layout.addLayout(login_layout)

        # 创建开始按钮
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setFixedSize(120, 40)
        self.start_btn.clicked.connect(self.run_report)  # 点击连接方法
        layout.addWidget(self.start_btn)
        self.start_btn.setEnabled(False)

        self.setLayout(layout)

    def update_working_date(self, qdate: QDate):
        """Slot: update self.working_date and self.working_datetime when user picks a date."""
        try:
            year = qdate.year()
            month = qdate.month()
            day = qdate.day()
            self.working_date = datetime.combine(datetime(year, month, day), datetime.min.time())
            self.working_datetime = self.working_date
            logger.info(f"工作日期设置为: {self.working_date}")
        except Exception as e:
            logger.warning(f"更新工作日期失败: {e}")

    def update_save_name(self, text):
        self.save_name = self.save_name_edit.text().strip()
        # ensure platform-native path
        self.output_file = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.join(self.output_dir, self.save_name))))

        self.save_config()
        self.save_file_label.setText(self.output_file)
        if self.output_dir:
            self.save_dir_label.setText(self.output_file)
        
    def select_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录", self.last_dir)
        if dir_path:
            # handle file:// URLs or POSIX-style leading slash on Windows like '/C:/...'
            try:
                # strip file:// scheme if present
                if dir_path.startswith('file://'):
                    # url -> path
                    from urllib.parse import urlparse, unquote
                    p = urlparse(dir_path)
                    dir_path = unquote(p.path or '')
                # if path looks like '/C:/...' on Windows, remove leading '/'
                if os.name == 'nt' and len(dir_path) >= 3 and dir_path[0] == '/' and dir_path[2] == ':' :
                    dir_path = dir_path[1:]
            except Exception:
                pass

            # normalize and expand user (~)
            dir_path = os.path.normpath(os.path.abspath(os.path.expanduser(dir_path)))
            logger.info(f"选择保存目录(原始): {dir_path}")

            self.output_dir = dir_path
            self.save_dir_label.setText(dir_path)

            self.output_file = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.join(self.output_dir, self.save_name_edit.text().strip() or "日报表.xlsx"))))
            self.save_config()
            self.save_file_label.setText(self.output_file)
        else:
            self.save_dir_label.setText("未选择保存目录")

    def on_machine_changed(self, value):
        self.machine_sum = int(value)
        print(f"机器数量变为: {self.machine_sum}")

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
            # normalize selected file path
            file_path = os.path.normpath(os.path.abspath(os.path.expanduser(file_path)))
            self.selected_file = file_path
            self.file_label.setText(file_path)
            # 更新 last_dir 为当前选择文件所在目录
            self.last_dir = os.path.dirname(file_path)
            self.save_config()
        else:
            self.file_label.setText("未选择文件")
            self.selected_file = os.path.expanduser("~/Documents/日报表模板.xlsx")
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

    # ---- 登录相关的 GUI 回调与启动 ----
    def _show_qr(self, qr_bytes: bytes):
        """在主线程中把二维码字节显示到 self.qr_label 中。"""
        logger.debug("进入_show_qr方法")
        try:
            logger.debug("显示二维码")
            if not qr_bytes:
                self.qr_label.setText("二维码数据为空")
                return

            image = QImage.fromData(qr_bytes)
            # 如果解码失败，保存到临时文件以便调试
            if image.isNull():
                try:
                    temp_dir = os.path.join(os.getcwd(), 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    dump_path = os.path.join(temp_dir, f'qr_debug_{int(time.time())}.png')
                    with open(dump_path, 'wb') as f:
                        f.write(qr_bytes)
                    logger.warning(f"解码二维码失败，已写入: {dump_path}")
                    self.qr_label.setText("无法解析二维码，已保存到临时文件")
                except Exception as e:
                    logger.warning(f"保存失败: {e}")
                    self.qr_label.setText("无法解析二维码")
                return

            pix = QPixmap.fromImage(image).scaled(self.qr_label.width(), self.qr_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
            self.qr_label.setPixmap(pix)
            self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            logger.warning(f"显示二维码失败: {e}")

    def _close_qr(self):
        try:
            self.qr_label.clear()
        except Exception:
            pass

    def start_login(self):
        """启动后台线程执行 login main_flow，并提供回调到 GUI。"""
        class SafeCallback:
            def __init__(self, app, method):
                self.app = app
                self.method = method
                logger.debug(f"创建回调: {method.__name__}")
                
            def __call__(self, *args, **kwargs):
                logger.debug(f"调用回调 {self.method.__name__}")
                try:
                    self.app.show_signal.emit(args[0] if args else None)
                    logger.debug("信号已发出")
                except Exception as e:
                    logger.error(f"发送信号失败: {e}")

        def worker():
            try:
                logger.debug("工作线程开始")
                token = self.login_service.main_flow(
                    show_qr_callback=SafeCallback(self, self._show_qr),
                    close_qr_callback=SafeCallback(self, self._close_qr)
                )

                if token:
                    logger.info("登录成功")
                    self.token = token  
                    self.start_btn.setEnabled(True)
                else:
                    logger.warning("登录未完成或失败")
            except Exception as e:
                logger.warning(f"登录线程出错: {e}")
            finally:
                # 无论成功或失败，都在主线程恢复按钮状态
                try:
                    QTimer.singleShot(0, lambda: self.login_btn.setEnabled(True))
                except Exception:
                    pass
        if self.login_service.cache_check():
            logger.info("已有有效登录状态，无需扫码")
            self.token = self.login_service.token
            self.start_btn.setEnabled(True)
        else:
            logger.info("启动登录线程，等待扫码...")
            t = threading.Thread(target=worker, daemon=True)
            t.start()
        # 禁用按钮直到流程结束，防止重复启动
        try:
            self.login_btn.setEnabled(False)
            self.qr_label.setText("等待二维码...")
            self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception:
            pass

    def on_douyin_error(self, msg: str):
        # 弹窗提示
        box = QMessageBox(self)
        box.setWindowTitle("抖音数据错误")
        box.setText(msg)
        box.exec()
    
    def on_meituan_error(self, msg: str):
        # 弹窗提示
        box = QMessageBox(self)
        box.setWindowTitle("美团错误")
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
        # Ensure a graceful shutdown when the window is closed
        self.shutdown()
        event.accept()

    def shutdown(self, timeout_ms: int = 3000):
        """Request all running workers stop and wait briefly for them to finish.

        This method is safe to call multiple times.
        """
        # Request workers to stop
        for worker in list(self.workers):
            try:
                if hasattr(worker, "isRunning") and worker.isRunning():
                    # Prefer a polite quit(), fallback to terminate() if available
                    try:
                        worker.quit()
                    except Exception:
                        try:
                            worker.terminate()
                        except Exception:
                            pass
            except Exception:
                pass

        # Wait for workers to finish, but don't block the UI thread too long
        deadline = QTimer()
        # Use a simple polling loop with a short sleep via processEvents
        import time
        start = time.time()
        while True:
            all_done = True
            for worker in list(self.workers):
                try:
                    if hasattr(worker, "isRunning") and worker.isRunning():
                        all_done = False
                        break
                except Exception:
                    continue
            if all_done:
                break
            if (time.time() - start) * 1000 > timeout_ms:
                # give up waiting after timeout
                break
            # allow Qt to process pending events so UI remains responsive
            QApplication.processEvents()
            time.sleep(0.05)

        # Best-effort cleanup
        for worker in list(self.workers):
            try:
                if hasattr(worker, "isRunning") and worker.isRunning():
                    try:
                        worker.terminate()
                    except Exception:
                        pass
            except Exception:
                pass
        self.workers = []

def main():
    app = QApplication(sys.argv)
    my_app = MyApp()
    my_app.show()

    # When running from CLI, allow Ctrl+C to quit the Qt application gracefully.
    def _handle_sigint(sig, frame):
        # If caller requests an immediate force-kill, do a hard exit
        try:
            force_kill = os.environ.get("SDX_FORCE_KILL", "0")
        except Exception:
            force_kill = "0"

        if force_kill == "1":
            # Forcefully terminate the process without running cleanup handlers
            try:
                os._exit(1)
            except Exception:
                # fallback to normal exit
                try:
                    sys.exit(1)
                except Exception:
                    pass
            return

        # Use QTimer.singleShot to ensure shutdown runs in the Qt main loop
        try:
            QTimer.singleShot(0, lambda: my_app.shutdown())
            QTimer.singleShot(0, app.quit)
        except Exception:
            try:
                app.quit()
            except Exception:
                pass

    try:
        # Register the handler only if Python supports signal (non-Windows GUI may ignore)
        signal.signal(signal.SIGINT, _handle_sigint)
    except Exception:
        # Some environments (e.g., frozen Windows GUI) may not allow resetting signal handlers
        pass

    # Start a small QTimer to allow Python signal handlers (like SIGINT) to run
    # while the Qt event loop is active. Without this, on some platforms the
    # Python-level signal handlers won't be invoked when Qt has control.
    def _timer_pump():
        # no-op, exists to yield control to Python's signal handling
        return

    pump_timer = QTimer()
    pump_timer.timeout.connect(_timer_pump)
    pump_timer.start(100)

    # Start the Qt event loop. If Ctrl+C is pressed in terminal, _handle_sigint will call app.quit()
    sys.exit(app.exec())
# 启动主程序入口
if __name__ == "__main__":
    main()

