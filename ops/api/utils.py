#coding=utf8
import os

import imp

def load_url_map(path, package, log=None):
    url_map = []
    our_dir = path[0]
    for dirpath, dirnames, filenames in os.walk(our_dir):
        for fname in filenames:
            root, ext = os.path.splitext(fname)
            if ext != '.py' or root == '__init__':
                continue
            class_path = os.path.join(path[0], fname)
            handle_class = imp.load_source(fname, class_path)
            _url_map = getattr(handle_class, 'url_map', {})
            if _url_map:
                for _url, _handler in _url_map.items():
                    url_map.append((_url, getattr(handle_class, _handler)))
    if log:
        log.debug('\n'.join['%s\t%' % (_url_map[0], _url_map[1]) for _url_map \
                in url_map])
    return url_map
