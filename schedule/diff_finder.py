
import json
from deepdiff import DeepDiff  # pip install deepdiff

with open("./schedule/data.json", "r", encoding="utf-8") as f1, open("./schedule/right_data.json", "r", encoding="utf-8") as f2:
    data1 = json.load(f1)
    data2 = json.load(f2)

diff = DeepDiff(data1, data2, ignore_order=True)

print(diff if diff else "两个文件内容一致")
