文档生成步骤
==============
``PS: 按照以下结构具体说明``

    ├── bin
    │   └── opsclient
    ├── etc
    ├── opsclient
    │   ├── exceptions.py
    │   ├── __init__.py
    │   ├── shell.py
    │   ├── utils.py
    │   └── api
    │       ├── __init__.py
    │       ├── shell.py
    └── setup.py


```
1. 安装sphinx

    pip install sphinx

2. 创建文档目录

    mkdir docs

3. 生成API目录下面模块的文档

    sphinx-apidoc -F -o docs opsclient/api

4. 编辑docs/config.py，添加PYTHONPATH

    vim docs/config.py
    添加下面代码至config.py
    sys.path.insert(0, os.path.abspath('../opsclient/api/'))

5. 安装主题
    pip install sphinx_rtd_theme

6. 配置主题

    vim docs/config.py
    添加/修改下面代码至config.py
    import sphinx_rtd_theme
    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

7. 生成文档

    cd docs && mkdir html
    sphinx-build . html
```

html目录里面即为生成的文档。

常用语法
===========
具体详细可参考 [reStructuredText](http://zh-sphinx-doc.readthedocs.org/en/latest/rest.html)

*斜体加粗*

    *斜体加粗*

**加粗**

    **加粗**

超链接 [百度](http://www.baidu.com)

    超链接 百度_.

    .. _百度: http://www.baidu.com

`引用`

    `引用`

参数列表:
* gameid: 游戏ID
* version: 版本

    参数列表:

    :gameid: 游戏ID
    :version: 版本

代码块:

    代码块:
    ::
        
        for i in xrange(10):
            print i
