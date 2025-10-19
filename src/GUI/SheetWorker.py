from xlutils import Wshandler

class SheetWorker:
    def __init__(self, source_file: str, targetfile: str):
        self.source_file = source_file
        self.targetfile = targetfile
    