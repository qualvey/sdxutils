import requests

url1 = "http://sso.cloudnetcafe.com/api/admin/user/wechatLogin?code=01151Hkl2aQ1uf4lsfol2r7WlD451Hkx"
#headers = {
#    "Host": "sso.cloudnetcafe.com",
#    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
#    "Accept": "application/json, text/plain, */*",
#    "Accept-Language": "zh,en-US;q=0.7,en;q=0.3",
#    "Accept-Encoding": "gzip, deflate",
#    "Authorization": "null",
#    "Origin": "http://sso.cloudnetcafe.com",
#    "Connection": "keep-alive",
#    "Referer": "http://sso.cloudnetcafe.com/",
#    "Content-Length": "0"
#}
#response = requests.post(url=url, headers=headers)
wx_code ="sdkalsjdlksajl"

api_endpoint = f"/api/admin/user/wechatLogin"
param = {
    "code" : f"{wx_code}"
    }
headers = {
"Host" : "sso.cloudnetcafe.com",
"User-Agent" : "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
"Accept" : "application/json, text/plain, */*",
"Accept-Language" : "zh,en-US;q=0.7,en;q=0.3",
"Accept-Encoding" : "gzip, deflate",
"Authorization" : "null",
"Origin" : "http://sso.cloudnetcafe.com",
"Connection" : "keep-alive",
"Referer" : "http://sso.cloudnetcafe.com/",
"Content-Length" : "0",
        }
url2=f"http://{headers['Host']}"
print(url1)
print(url2)

#response_token = send_raw_request(raw_request_token)
#response_token = requests.post(url=url, json=param, headers=headers)
