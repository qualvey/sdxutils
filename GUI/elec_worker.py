from operation import  ElecDataService

from PySide6.QtCore import QThread, Signal
from datetime import datetime
from tools import logger as mylogger
logger = mylogger.get_logger(__name__)


class ElecWorker(QThread):
    finished = Signal(str, float)  
    error = Signal(str)      # 返回错误信息，需要弹窗提示
    status = {} # 用于存储状态信息

    def __init__(self,name:str, date: datetime):
        super().__init__()
        self.date = date
        self.name = name
        

    def run(self):
        try:
            logger.info("ElecWorker run")
            elecservice = ElecDataService(self.date)
            el_data:float = elecservice.get_elecUsage()
            
            self.finished.emit(self.name,el_data)
        except Exception as e:
            self.error.emit(str(e))