
def header_launcher(raw_request):
    '''
    raw_request: 字符串，从f12直接复制原始值
    返回，dict
        '''
    headers = {}
    lines = raw_header.splitlines()
    for line in lines:
        # 跳过空行
        if line.strip():
            # 将每行按照第一个冒号拆分为键和值
            key, value = line.split(":", 1)
            # 去除键和值的多余空白，并添加到字典中
            headers[key.strip()] = value.strip()
    return headers
