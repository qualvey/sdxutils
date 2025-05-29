#装饰器功能测试
def app(function):
    def wrap():
        print('aaaa')
        function()
        print('vbbbb')
    return wrap

@app
def function():
    print('ccccc')

function()
