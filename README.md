#简介
此为OPS的一个基本库, 包含log, 配置, DB, 插件化服务, API, 认证

* log: 基于python的logging
* 配置: 基于tornado的option
* DB: 基于sqlalchemy
* 服务: 基于event,
* API: 基于torando
* 认证: 基本用户认证通过keystone, 关于API的权限组合认证通过keystone的role

#示例:\
##服务
```
from ops.service import manager
class TestManager(manager.Manager):
    def __init__(self, *args, **kwargs):  #初始化
        print "i am init"
    @manager.periodic_task  #周期性执行任务
    def test(self, raise_on_error=True):
        print "perioc\n"
```

##启动脚本
```
"""Starter of service.

Start Test Service

"""

from tornado.options import parse_command_line, options

import eventlet
eventlet.monkey_patch()

import os
import sys


from ops import log as logging
from ops.service import service
from ops import utils
from ops.options import register_opt

test_opts = {
    "name": 'ops_example_manager',
    "default": 'ops.example.manage.TestManager',
    "help": 'manager of example',
    "type": str,
}

register_opt(test_opts)

if __name__ == '__main__':
    parse_command_line()
    logging.setup()
    server = service.Service.create(binary='ops_example', periodic_interval=10)
    service.serve(server)
    service.wait()
```
服务启动后会自动创建log文件, 如果有数据库也会自动创建数据库, 并周期性更新自己的状态


##配置: 
各代码需要用到的配置, 写在各自的配置文件中, 然后注册到option中, 可以在ops的默认配置文件/etc/ops/ops.conf中覆盖默认option
```
from ops.options import get_options

LOG = logging.getLogger(__name__)

service_opts = [
    {
        "name": 'report_interval',
        "default": 30,
        "help": 'seconds between nodes reporting state to datastore',
        "type": int,
    },
    {
        "name": 'periodic_interval',
        "default": 60,
        "help": 'seconds between running periodic tasks',
        "type": int,
    },
    ]

options = get_options(service_opts, 'services')
```
后面就可以通过options.periodic_interval 进行引用

##API
只需要按照tornado的格式(如ops/api/contrib/test1.py), 进行添加, 在tornado启动的时候既可直接加载相应的API
###测试:
####启动服务:
```
[root@localhost api]# python main.py
/usr/lib/python2.6/site-packages/ops-0.1-py2.6.egg/ops/api/contrib/test1.py:1: RuntimeWarning: Parent module 'test1' not found while handling absolute import
  import tornado.web
/usr/lib/python2.6/site-packages/ops-0.1-py2.6.egg/ops/api/contrib/test1.py:3: RuntimeWarning: Parent module 'test1' not found while handling absolute import
  from ops import log as logging
[I 140606 05:13:41 web:1780] 200 GET /helloworld (127.0.0.1) 0.78ms
```
####测试:
```
[root@localhost ops]# curl 127.0.0.1/helloworld
Hello World! I love this world!
```


##log
```
from ops import log as logging
LOG = logging.getLogger(__name__)
LOG.audit('Starting %(topic)s on %(host)s ',
         {'topic': self.binary, 'host': self.host})
```
既可以对log进行试用, 各个服务的log会自动记录到各自的log文件中, 默认是/var/log/ops(可用过options.log_dir配置)下的各服务的名字开头的log文件中

##认证:
```
policy = {
        "contrib.test1.test2": ["admin"],  #只有admin的role可以调用
        "contrib.test1.test2": [],  #通过keystone认证都可以调用
        }
```
