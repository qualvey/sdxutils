from specialFee import SpecialFee
from PySide6.QtCore import QThread, Signal
from datetime import datetime

class SpecialFeeWorker(QThread):
    finished = Signal(str, object)  # 返回处理后的数据
    error = Signal(str)      # 返回错误信息，需要弹窗提示

    def __init__(self, name:str, date: datetime,token:str):
        super().__init__()
        self.name = name
        self.date = date
        self.token = token

    def run(self):
        try:
            sfservice = SpecialFee(self.date, token=self.token)
            self.finished.emit(self.name,sfservice.data)
        except Exception as e:
            self.error.emit(str(e))