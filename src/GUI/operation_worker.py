from operation import OperationService

from PySide6.QtCore import QThread, Signal
from datetime import datetime

class OperationWorker(QThread):
    finished = Signal(str,object)  
    error = Signal(str)      # 返回错误信息，需要弹窗提示

    def __init__(self, name:str, date: datetime,token:str):
        super().__init__()
        self.name = name
        self.date = date
        self.token = token

    def run(self):
        try:
            opservice = OperationService(self.date,token=self.token)
            # op_data = opservice.resolve_operation_data(opservice.fetch_data())
            self.finished.emit(self.name,opservice.data)
        except Exception as e:
            self.error.emit(str(e))