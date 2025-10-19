from douyin import DouyinService
from PySide6.QtCore import QThread, Signal
from datetime import datetime

#cookies搜索verify

#dy_total
#dy_count
#dy_good

#
class DouyinWorker(QThread):
    finished = Signal(str, object)  # 返回处理后的数据
    error = Signal(str)      # 返回错误信息，需要弹窗提示

    def __init__(self, name:str, date):
        super().__init__()
        self.name = name
        self.date = date
        self.data = {}

    def run(self):
        try:
            dyservice = DouyinService(self.date)

            self.finished.emit(self.name,dyservice.data)
        except Exception as e:
            self.error.emit(str(e))

if __name__ == "__main__":
    from datetime import datetime
    worker = DouyinWorker("douyin",datetime(2025,9,11))
    def print_result(name, data):
        print(f"任务 {name} 完成，数据: {data}")
    def print_error(error_msg):
        print(f"任务出错: {error_msg}")
    worker.finished.connect(print_result)
    worker.error.connect(print_error)
    worker.start()
    worker.wait()  # 等待线程完成