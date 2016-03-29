default = {
        "GET": ["admin", "service_ocmdb"],
        "POST": ["admin", "service_ocmdb"],
        "PUT": ["admin", "service_ocmdb"],
        "DELETE": ["admin", "service_ocmdb"],
        }

policy = {
        "/ipaddr/([a-zA-Z0-9-]+)$": {},
        "/ipaddr$": {},
        "/assets/([a-zA-Z0-9-]+)$": {},
        "/assets$": {},
        "/query$": {},
        "/query/([a-zA-Z0-9-]+)$": {},
        "/tree/([a-zA-Z0-9-]+)$": {},
        "/tree$": {},
        "/service$": {},
        "/record$": {},
        "/domain$": {},
        "/domain/openapi$": {"GET": ["domain_.mu.g.yx-g.cn","domain_.mu.ate.cn","domain_.game2.ate.cn"], "POST": ["domain_.mu.g.yx-g.cn","domain_.mu.ate.cn","domain_.game2.ate.cn"], "PUT": ["domain_.mu.g.yx-g.cn","domain_.mu.ate.cn","domain_.game2.ate.cn"], "DELETE": ["domain_.mu.g.yx-g.cn","domain_.mu.ate.cn","domain_.game2.ate.cn"]},
        }
