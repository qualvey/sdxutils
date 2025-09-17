from operation import OperationService

from PySide6.QtCore import QThread, Signal
from datetime import datetime

class OperationWorker(QThread):
    finished = Signal(dict)  
    error = Signal(str)      # 返回错误信息，需要弹窗提示

    def __init__(self,  date: datetime):
        super().__init__()
       
        self.date = date

    def run(self):
        try:
            opservice = OperationService(self.date)
            op_data = opservice.resolve_operation_data(opservice.fetch_data())
            self.finished.emit(op_data)
        except Exception as e:
            self.error.emit(str(e))