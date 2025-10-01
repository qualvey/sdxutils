from .. import DouyinService
from datetime import datetime, timedelta

if __name__ == "__main__":
    date = datetime.now() - timedelta(days=1)
    service = DouyinService(date)
    print(service.data)