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
            class_path = os.path.join(dirpath, fname)
            handle_class = imp.load_source(fname, class_path)
            _url_map = getattr(handle_class, 'url_map', {})
            if _url_map:
                for _url, _handler in _url_map.items():
                    url_map.append((_url, getattr(handle_class, _handler)))
    log.info('url map:\n'+'\n'.join([ '%20s\t%s' % (_url_map[0], _url_map[1])\
            for _url_map in url_map]))
    return url_map

def pageNation(request, page_list, page_name='result', count=None):
    print page_name
    if not isinstance(page_list, list):
        return "page_list must be a list"
    start = int(request.get_argument('start', 0))
    length = int(request.get_argument('length', 10))
    if start > len(page_list) or start < 0 : start = 0
    _page_list = page_list[start:(start+length)]
    if _page_list and (not isinstance(_page_list[0], str)):
        try:
            _page_list = [dict(q) for q in _page_list]
        except:
            return 'object of list must be dictable'
    if count:
        return {page_name: _page_list, "count": count}
    else:
        return {page_name: _page_list, "count": len(page_list)}
