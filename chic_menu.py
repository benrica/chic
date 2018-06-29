#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    作者:     Damon 
    日期:     2018/6/28 
    版本:     1.0
    文件:     chic_menu.py 
    功能: 
        
"""

__author__ = 'Damon'

import collections

menus = collections.OrderedDict()
menus = {
    'main': [
        [0, 'main', 'main'],
        [1, 'test_sub', '二级子菜单', 'sub_dir'],
        [2, 'test_sql', '测试sql查询', 'sql_example_key'],
    ],
    'sub_dir': [
        [0, 'sub_dir', 'main'],
        [1, 'test_sql2', '测试sql查询', 'sql_example_key2'],
        [2, 'test_sub2', '三级子菜单', 'sub_dir1'],
        [3, 'test_func', '函数调用', 'f:call_test2'],
        [4, 'test_cmd', '远程执行命令', 's:script1'],
        [5, 'test_script', '远程调用脚本', 's:script2'],
    ],
    'sub_dir1': [
        [0, 'sub_dir1', 'sub_dir'],
        [1, 'batch_put', '批量文件上传', 's:batch_put'],
        [2, 'batch_get', '批量文件下载', 's:batch_get'],
        [3, 'ss.key3', 'ss.title3', 'key'],
        [4, 'ss.key4', 'ss.title4', 'key'],
        [5, 'ss.key5', 'ss.title5', 'key'],
    ]
}
