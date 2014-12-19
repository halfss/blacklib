# -*- coding:utf-8 -*-
# 角色名支持PYTHON正则表达式

default = {
        "GET": ["service_ocmdb_*"],
        "POST": ["service_ocmdb_*"],
        "PUT": ["service_ocmdb_*"],
        "DELETE": ["service_ocmdb_*"],
        }

policy = {
        "/ipaddr/([a-zA-Z0-9-]+)$": {"GET": ["admin"], "POST": ["admin"], "PUT": ["admin"], "DELETE": ["admin"]},
        }
