from specialFee import SpecialFee
from PySide6.QtCore import QThread, Signal
from datetime import datetime

class SpecialFeeWorker(QThread):
    finished = Signal(str, object)  # 返回处理后的数据
    error = Signal(str)      # 返回错误信息，需要弹窗提示

    def __init__(self, name:str, date: datetime):
        super().__init__()
        self.name = name
        self.date = date

    def run(self):
        try:
            sfservice = SpecialFee(self.date)
            sf_data = sfservice.fetch_specialFee()
            resolved_data = sfservice.resolve_data(sf_data)
            total_fee = sfservice.get_specialFee(resolved_data)
            self.finished.emit(self.name,(resolved_data, total_fee))
        except Exception as e:
            self.error.emit(str(e))