#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    作者:     Damon 
    日期:     2018/6/28 
    版本:     1.0
    文件:     chic_log.py.py 
    功能: 
        
"""

import logging
import logging.handlers
import time
import os

logm = ''


# 常驻程序日志切分函数
def init_log(sid, prefile, pid=os.getpid(), lvl=logging.DEBUG, when='midnight', mode=1):
    file = prefile + '_' + str(pid)
    dirname = os.path.dirname(os.path.abspath(prefile))
    if not os.path.exists(dirname): os.makedirs(dirname)
    # create logger
    logm = logging.getLogger(sid)
    logm.setLevel(lvl)
    # create file handler
    fh = logging.handlers.TimedRotatingFileHandler(file, when, 1, 0)
    # fh.suffix = "%Y%m%d-%H%M.log"
    fh.suffix = "%Y%m%d.log"
    # create formatter
    if mode == 1:
        fmt = "[%(asctime)-15s %(process)d %(levelname)-7s] %(message)s"
    elif mode == 2:
        fmt = "[%(asctime)-15s %(thread)d %(levelname)-7s] %(message)s"
    elif mode == 3:
        fmt = "[%(asctime)-15s %(process)d-%(thread)d %(levelname)-7s] %(message)s"
    else:
        fmt = "[%(asctime)-15s %(levelname)-7s] %(message)s"
    formatter = logging.Formatter(fmt)
    # add handler and formatter to logger
    fh.setFormatter(formatter)
    logm.addHandler(fh)
    return logm


# 非常驻程序日志函数
def init_log2(prefile, date=time.strftime('%Y%m%d'), pid=os.getpid(), lvl=10, mode=1):
    file = prefile + '_' + str(pid) + '_' + date + '.log'
    dirname = os.path.dirname(os.path.abspath(prefile))
    if not os.path.exists(dirname): os.makedirs(dirname)
    if mode == 1:
        fmt = "[%(asctime)-15s %(process)d %(levelname)-7s] %(message)s"
    elif mode == 2:
        fmt = "[%(asctime)-15s %(thread)d %(levelname)-7s] %(message)s"
    elif mode == 3:
        fmt = "[%(asctime)-15s %(process)d-%(thread)d %(levelname)-7s] %(message)s"
    else:
        fmt = "[%(asctime)-15s %(levelname)-7s] %(message)s"
    logging.basicConfig(filename=file, level=lvl, format=fmt, filemode='a')


# 非常驻程序日志函数
def init_log3(sid, prefile, date=time.strftime('%Y%m%d'), pid=os.getpid(), lvl=10, mode=1):
    file = prefile + '_' + str(pid) + '_' + date + '.log'
    dirname = os.path.dirname(os.path.abspath(prefile))
    if not os.path.exists(dirname): os.makedirs(dirname)
    # create logger
    logm = logging.getLogger(sid)
    logm.setLevel(lvl)
    # create file handler
    fh = logging.FileHandler(file)
    # sh = logging.StreamHandler(stream=None)
    # sh.setLevel(logging.DEBUG)
    # create formatter
    if mode == 1:
        fmt = "[%(asctime)-15s %(process)d %(levelname)-7s] %(message)s"
    elif mode == 2:
        fmt = "[%(asctime)-15s %(thread)d %(levelname)-7s] %(message)s"
    elif mode == 3:
        fmt = "[%(asctime)-15s %(process)d-%(thread)d %(levelname)-7s] %(message)s"
    else:
        fmt = "[%(asctime)-15s %(levelname)-7s] %(message)s"
    formatter = logging.Formatter(fmt)
    # add handler and formatter to logger
    fh.setFormatter(formatter)
    logm.addHandler(fh)
    return logm


# 日志装饰器
def logit(func):
    def new_func(*args, **kwargs):
        logm.info(func.__name__ + ' was called..')
        return new_func(*args, **kwargs)

    return new_func

# logm = init_log('sid','test_log',when='M')
# init_log2('test_log')
# logm = init_log3('sid','test_log')
