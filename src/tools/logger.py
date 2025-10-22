import logging
import os
from tools import env
from colorama import init
import coloredlogs

init(autoreset=True)

class TabSuffixFormatter(logging.Formatter):
    def format(self, record):
        # 确保 msg 是字符串，并加一个制表符
        record.msg = str(record.msg).rstrip() + '\t'
        return super().format(record)

class ParentDirFilter(logging.Filter):
    def filter(self, record):
        # 获取父目录名
        parent_dir = os.path.basename(os.path.dirname(record.pathname))
        record.parent_file = f"{parent_dir}/{record.filename}"
        return True

LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
LOG_LEVEL = logging.INFO
#LOG_FMT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(messages"
LOG_FMT = " %(message)s  - %(asctime)s  - %(levelname)s - %(parent_file)s:%(lineno)d "
log_path = f'{env.proj_dir}/log/debug.log'
#TODO OOP 风格重构
class LoggerService:
    def __init__(self, name: str, log_file: str = log_path, level: int = LOG_LEVEL):
        self.name = name
        self.log_file = log_file
        self.level = level
        self.logger = self._get_logger()

    def _get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        logger.propagate = False  # 避免重复打印

        if not any(isinstance(f, ParentDirFilter) for f in logger.filters):
            logger.addFilter(ParentDirFilter())

        # 避免重复添加 FileHandler
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            fh = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
            fh.setLevel(self.level)
            fh.setFormatter(logging.Formatter(LOG_FMT))
            fh.setFormatter(TabSuffixFormatter(LOG_FMT))

            logger.addHandler(fh)

        # 避免重复安装 coloredlogs
        coloredlogs.install(
            level=self.level,
            logger=logger,
            fmt=LOG_FMT,
            level_styles={
                'debug': {'color': 'cyan'},
                'info': {'color': 'green'},
                'warning': {'color': 'yellow'},
                'error': {'color': 'red'},
                'critical': {'color': 'red', 'bold': True},
            }
        )
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(TabSuffixFormatter(LOG_FMT))

        return logger


# 测试代码
if __name__ == "__main__":
    logger = LoggerService(__name__).logger
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.critical("严重错误")
