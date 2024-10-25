s = """
<dl class="layui-anim layui-anim-upbit" style=""><dd lay-value="" class="layui-select-tips">请选择商品分类</dd><dd lay-value="1" class="">米面粮油</dd><dd lay-value="5" class="">食品零食</dd><dd lay-value="8" class="">生鲜水果</dd><dd lay-value="10" class="">精致礼盒</dd><dd lay-value="18" class="">五谷杂粮</dd><dd lay-value="26" class="">滋补保健</dd><dd lay-value="27" class="">个护清洁</dd><dd lay-value="39" class="layui-this" style="">日用百货</dd><dd lay-value="51" class="">本地生活</dd><dd lay-value="52" class="">家用电器</dd><dd lay-value="62" class="">厨房小电</dd><dd lay-value="96" class="">手机数码</dd><dd lay-value="138" class="">美妆护肤</dd><dd lay-value="243" class="">母婴亲子</dd><dd lay-value="300221" class="">酒水饮料</dd><dd lay-value="300230" class="">运动户外</dd><dd lay-value="300246" class="">文具用品</dd><dd lay-value="300258" class="">测试二级分类</dd><dd lay-value="300259" class="">1234</dd><dd lay-value="300266" class="">面粉挂面</dd><dd lay-value="300270" class="">水饮冲调</dd></dl>
"""

from bs4 import BeautifulSoup

soup = BeautifulSoup(s, 'lxml')
options = soup.find_all('dd')
result = {}
for option in options:
    value = option.get('lay-value')
    if not value:
        continue

    text = option.text.strip()
    result[text] = {
        'level': value,
        'children': []
    }

print(result)
