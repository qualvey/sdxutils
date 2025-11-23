import json
import requests,os
with open("src/meituan/meituan_comments.json", 'r', encoding="utf-8") as f:
            # print(f.read())
            f = json.load(f)
            a =  f.get("msg", {}).get("reviewDetailDTOs", [])[1].get("star")
            print(a)

# print(os.getcwd()  )
            