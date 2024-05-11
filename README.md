# FastSerializer - 快速序列化器

用于将 Python 数据类对象序列化为 JSON 数据格式，也可以将JSON字典/字符串反序列化为 Python数据类对象。
原则上来说FastSerializer可以序列化任意对象。

# 注意：当前快速序列化器还未完成，请等此消息没有后再使用，但是可以进行测试。

## ✨ 特点

* **🚀快速**：在Python提供非常高的性能因为它使用了dataclass，并且FastSerializer非常轻量，不占用太多空间。
* **💎优雅**：精心设计，FastSerializer的设计模式可以让你减少冗余的代码。
* **📦简单**：你可以定义合适的数据类结构，其它都交给FastSerializer和自定义的装饰器重写。
* **💪强大**：支持任意复杂的对象（具有深度继承层次结构和泛型类型的）。
* **👍兼容**：FastSerializer原始就支持很多其它的数据类库，比如：Pydantic、Dataclass、SqlalchemyOrm、自定义等。


## 📦 安装
```shell
$ pip install fast-serializer
```

## 💡 一个简单的例子

```python
from typing import List
from fast_serializer import FastDataclass, field

class Address(FastDataclass):
    """地址"""
    detail_address: str
    
    
class User(FastDataclass):
    """用户"""
    nickname: str = field(required=True)
    age: int = None
    address_list: List[Address]


# 数据
data = {'nickname': 'Lao Da', 'address_list': [{'detail_address': 'China'}]}

# JSON字典到Python对象反序列化的用法
user = User(**data)
print(user)  # 提供了Repr

print(user.nickname)
#> 'Lao Da'
```


### 👩‍💻 目录结构

```shell
fast_serializer
│  .gitignore  git忽略文件
│  example.py 实例文件
│  README.md 阅读文件
└─fast_serializer 主包
    │  constants.py 常量定义
    │  dataclass_config.py 数据类的配置
    │  decorators.py 装饰器
    │  exceptions.py 异常
    │  fast_dataclass.py 快速数据类
    │  field.py 字段
    │  getter.py Getter样板生成（待开发Pycharm插件后支持）
    │  json_schema.py 
    │  serializer.py 序列化器
    │  utils.py 工具包
    │  validator.py 验证器
    │  __init__.py
```