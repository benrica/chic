#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    作者:     Damon 
    日期:     2018/6/28 
    版本:     1.0



    文件:     chic.py 
    功能: 
        
"""

__author__ = 'Damon'

import collections
import time
import datetime
import sys
import os
import re
import getpass
import chic_log

# custom module
from chic_menu import menus
import chic_func
from ora_dbi import ora_eng
from ssh_sftp import bastin, Myssh

# 全局配置初始化
from configparser import ConfigParser

config = ConfigParser()
config.read('chic.ini')
can_call_func_list = config.get('comm', 'can_call_func_list')
show_key = config.getboolean('comm', 'show_key')
if can_call_func_list: mark_func = {x: 1 for x in can_call_func_list.split('|')}
tree = lambda: collections.defaultdict(tree)
# show_key = True
# cur_module = sys.modules[__name__]
# print(cur_module)

# 加载脚本命令配置
sconf = ConfigParser()
sconf.read('chic_cmds.ini')


# 加载配置文件
def init_sql(file):
    mark_sql = collections.defaultdict(list)
    tmp_list = list()
    sql_key = ''
    p = re.compile('^\[(\S+)\]\s*$', re.I)
    # 跳过空行，注释行
    p_next = re.compile('^(?:\s*#|\-\-|\s*$)')
    with open(file, 'r') as fh:
        for line in fh:
            if p_next.match(line): continue
            if p.match(line):
                if sql_key and tmp_list:
                    # ora,title,args,cols
                    # sqls
                    if tmp_list[0].count('|') - 3 < 0:
                        tmp_list[0] += '|' * abs(tmp_list[0].count('|') - 3)
                    ora, title, args, cols = str(tmp_list[0]).strip().split('|', 4)
                    sqls = ''.join(tmp_list[1:])
                    mark_sql[sql_key] = [ora, title, args, cols, sqls]
                    tmp_list = list()
                sql_key = p.match(line).group(1)
            else:
                if sql_key:
                    tmp_list.append(line)
    return mark_sql


mark_sql = init_sql('chic_sql.ini')


# test
# for i in mark_sql:print(i,mark_sql[i])

# 加载配置自定义配置文件
# def load_custom_cfg(file):


##菜单初始化
def init_menu(menus=menus):
    map_key = collections.defaultdict(list)
    map_par = dict()
    map_cnt = collections.defaultdict(int)
    for menu in menus:
        # 'sub_dir': [
        #    [0, 'sub_dir', 'main'],
        if menu != menus[menu][0][1]:
            raise SystemExit('The menu config_file has wrong,please check..')
        par_menu = menus[menu][0][2]
        for cfg in menus[menu]:
            map_cnt[cfg[1]] += 1
            map_par[cfg[1]] = par_menu
            if cfg[0] != 0:
                map_key[cfg[1]] = cfg
                if str(cfg[-1]).startswith('sub_'): map_key[cfg[-1]] = map_key[cfg[1]]
        dup_key = [(i, map_cnt[i]) for i in map_cnt if map_cnt[i] > 1]
        if len(dup_key) > 0:
            raise SystemExit('Duplicate config: {} ,please check..'.format(dup_key))
    # del map_cnt,dup_key
    return [map_key, map_par]


(map_key, map_par) = init_menu()


##菜单PPrint (格式化打印)
def show_menu(menu='main', show_key=show_key, columns=3):
    if not menus.get(menu):
        print('There have no menu:{},please check the config file..'.format(menu))
        return -1
    if len(menus[menu]) - 1 < columns: columns = len(menus[menu]) - 1
    col_size = dict((i, [0, 0]) for i in range(columns))
    # 分组计算
    new_list = [menus[menu][i:i + columns] for i in range(1, len(menus[menu]), columns)]
    map_seq = {}
    # [[[1, 'test_sub', '二级子菜单', 'sub_dir'], [2, 'test_sql', '测试sql查询', 'sql_example_key']]]
    for grp in new_list:
        for seq, cfg in enumerate(grp):
            map_seq[str(cfg[0])] = cfg[1]
            if len(cfg[1]) > col_size[seq][0]: col_size[seq][0] = len(cfg[1])
            # unicode编码后中文汉字只占 1 个字节,转 gbk 后让占 2 个字节
            if len(cfg[2].encode('gbk')) > col_size[seq][1]: col_size[seq][1] = len(cfg[2].encode('gbk'))
            # 计算格式化打印的最大长度
    fmt_size = 0
    for i in col_size:
        if show_key:
            fmt_size += (4 + col_size[i][0] + col_size[i][1] + 2)
        else:
            fmt_size += (4 + col_size[i][1] + 1)
    # 标题打印
    print()
    if menu == 'main':
        title = '♪Y(^_^)Y Main_menu {}'.format(time.ctime())
        print(title)
    else:
        menu_path = list()
        loop_cnt = 0
        menu_path.append(menu)
        while map_par[menu] != 'main' and loop_cnt < 6:
            menu = map_par[menu]
            menu_path.append(menu)
            loop_cnt += 1
        title = '♪Main→{}'.format('→'.join(reversed(["%02d)%s" % (map_key[i][0], map_key[i][2]) for i in menu_path])))
        print(title)
    if len(title) > fmt_size: fmt_size = len(title) + 1
    # 菜单PPrint (漂漂拳打印)
    print('+{}'.format('-' * fmt_size))
    for grp in new_list:
        print('|', end='')
        for seq, cfg in enumerate(grp):
            '''
            中文打印时只占1个字节，故打印含中文的值时实际格式化打印长度为 算到的总长度-字符串含有中文的个数
            使用 unicode 范围 \u4e00 - \u9fff 来判别汉字
            以下为计算字符串含有多少个中文字符
            '''
            chinese_word_count = len([s for s in cfg[2] if '\u4e00' <= s <= '\u9fff'])
            val_len = col_size[seq][1] - chinese_word_count if chinese_word_count > 0 else col_size[seq][1]
            if show_key:
                print(" {:0>2}) {:<{}s} {:<{}s}".format(cfg[0], cfg[1], col_size[seq][0], cfg[2], val_len), end='')
            else:
                print(" {:0>2}) {:<{}s}".format(cfg[0], cfg[2], val_len), end='')
        print()
    print('+{}'.format('-' * fmt_size))
    # 末标题打印
    if menu == 'main':
        help_info = "{:>{}s}".format("x|q)退出 h|H)帮助", fmt_size - 4)
    else:
        help_info = "{:>{}s}".format("b)返回 x|q)退出 h|H)帮助", fmt_size - 6)
    print(help_info)
    return (map_seq, menu)


'''
[1,'s.key1','s.title1','key'],
key格式说明
'[k:]key1,key2,key3,f:func^args^desc,...,s:script1,...'
args = 'agr1~arg2~...'
'''


def call_sql(key):
    ora, title, args, cols, sqls = mark_sql[key]
    if title: print('\n\033[31;1m♪{}\033[0m'.format(title.strip()))
    print('-' * 38)
    kwargs = parser_args(args) if args else None
    for sql in re.split(';', str(sqls), flags=re.M):
        sql = sql.strip()
        if sql:
            if cols:
                dbo.show_format2(sql, True, cols, kwargs)
            else:
                dbo.show_format(sql)


# 调用命令或脚本
def call_scripts(section):
    # 入参初始化
    cmd_info = dict()
    if sconf.has_section(section):
        for option in (
                'host', 'user', 'passwd', 'auth_key', 'cmds', 'args', 'get_local_file', 'get_local_dir',
                'get_remote_file',
                'put_local_file', 'put_remote_dir', 'put_remote_file', 'get_remote_match'):
            if sconf.has_option(section, option):
                cmd_info[option] = sconf.get(section, option)
                if option == 'auth_key':
                    if cmd_info[option] == 'True':
                        for pkey in (os.path.join(os.environ['HOME'], '.ssh', 'id_rsa'),
                                     os.path.join(os.environ['HOME'], '.ssh', 'id_dsa')):
                            if os.path.exists(pkey):
                                cmd_info[option] = pkey
                                break
                            else:
                                print(
                                    '*** The config_file: chic_cmds.ini has wrong, don\'t set value for the option auth_key if there is no private key exists')
                                sys.exit(-1)
            else:
                cmd_info[option] = None
        cmd_info['user'] = cmd_info['user'] or getpass.getuser()
    else:
        print('*** The config_file: chic_cmds.ini has wrong, section %s do not exists.' % section)
        sys.exit(-1)
    # 调用封装函数
    for host in cmd_info['host'].split(','):
        cmdo = Myssh(host=host, user=cmd_info['user'], passwd=cmd_info['passwd'], pkey=cmd_info['auth_key'])
        # 如有FTP配置信息,调用SFTP指上传或下载
        # 批量FTP上传
        if cmd_info['put_local_file']:
            remote_dir = cmd_info['put_remote_dir'] or os.environ['HOME'] + '/_tmp_put_dir'
            if cmd_info['put_local_file'].find(',') > 0:
                files = cmd_info['put_local_file'].split(',')
                cmdo.batch_put(*files, remote_dir=remote_dir)
            else:
                if cmd_info['put_remote_file']:
                    rfile = cmd_info['put_remote_file'] if cmd_info['put_remote_file'].find(
                        os.sep) >= 0 else os.path.join(remote_dir, cmd_info['put_remote_file'])
                    cmdo.put(cmd_info['put_local_file'], rfile)
                else:
                    rfile = os.path.join(remote_dir, os.path.basename(cmd_info['put_local_file']))
                    cmdo.batch_put(cmd_info['put_local_file'], remote_dir=remote_dir)

        # 批量文件下载
        local_dir = cmd_info['get_local_dir'] or os.getcwd()
        if cmd_info['get_remote_file']:
            if cmd_info['get_remote_file'].find(',') > 0:
                cmdo.batch_get(cmd_info['get_remote_file'], local_dir=local_dir)
            else:
                lfile = cmd_info['get_local_file'] or os.path.join(local_dir,
                                                                   os.path.basename(cmd_info['get_remote_file']))
                if lfile.find(os.sep) < 0:
                    lfile = os.path.join(local_dir, lfile)
                cmdo.get(cmd_info['get_remote_file'], lfile)
        # 模糊查找批量下载
        if cmd_info['get_remote_match']:
            cmdo.batch_get(cmd_info['get_remote_match'], local_dir=local_dir)

        # cmdo.read_flag = 0
        # for cmd in cmd_info['cmds'].split(';'):
        #    cmdo.call_cmds(cmd)
        if cmd_info['cmds']:
            cmdo.call_cmds(*cmd_info['cmds'].split(';'))


def parser_args(args):
    return None


def call_title(key_str=None):
    if not key_str: return -1
    for key in key_str.split(','):
        match_result = re.match('^([kfs]):', key)
        type_flag = match_result.group(1) if match_result else None
        key = re.sub('^[kfs]:', '', key)
        # 数据库调用
        if not match_result or type_flag == 'k':
            call_sql(key)
        # 函数，接口调用
        elif type_flag == 'f':
            call_func_str = str(key).split('^', 3)
            call_func = call_func_str[0]
            args = call_func_str[1] if len(call_func_str) > 1 else None
            desc = call_func_str[2] if len(call_func_str) > 2 else None
            args = parser_args(args)
            if desc: print("♪Call_func: {}".format(desc))
            if hasattr(chic_func, call_func):
                getattr(chic_func, call_func)(*args) if args else getattr(chic_func, call_func)()
            else:
                print('There is no function: {} in chic_func moudle.'.format(call_func))
        elif type_flag == 's':
            call_scripts(key)
        else:
            print('The title config_file has wrong,please check..')
            return -1


def call_test(a=1, b=2):
    print('call_test %s %s' % (a, b))


def search_menu(key):
    print('search menu')
    pass


def call_main():
    map_seq, cur_menu = show_menu('main', show_key=show_key, columns=2)
    while True:
        choose = input('Choose:').strip()
        # choose = re.sub('^\s+|\s+$','',choose)
        if not choose: continue
        mkey = map_seq.get(choose, choose)
        # print(mkey,map_key[mkey])
        if mkey.lower() == 'b':
            map_seq, cur_menu = show_menu(map_par[map_seq['1']], show_key=show_key)
            continue
        elif mkey.lower() == 's':
            map_seq, cur_menu = show_menu(cur_menu, show_key=show_key)
            continue
        elif mkey.lower() == 'main':
            map_seq, cur_menu = show_menu('main', show_key=show_key)
            continue
        elif re.search('^(?:q|quit|bye|x)$', mkey, re.I):
            sys.exit(0)
        elif map_key.get(mkey) and map_key[mkey][-1].startswith('sub_'):
            map_seq, cur_menu = show_menu(map_key[mkey][-1])
        elif map_key[mkey]:
            # [1, 'lvl1_key1', 'lvl1_title1', 'key'],
            call_title(map_key[mkey][-1])
        else:
            func, *args = mkey.split()
            if hasattr(cur_module, func) and mark_func.get(func):
                getattr(cur_module, func)(*args)
            elif hasattr(chic_func, func):
                getattr(chic_func, func)(*args)
            else:
                search_menu(mkey)


if __name__ == "__main__":
    try:
        ora_dsn = config.get('database', 'ora_dsn')
        ora_user = config.get('database', 'ora_user')
        ora_passwd = config.get('database', 'ora_passwd')
        ora_parallel_num = config.get('database', 'ora_parallel_num')
        dbo = ora_eng(ora_dsn, ora_user, ora_passwd, 50, ora_parallel_num)
        call_main()
    except KeyboardInterrupt as err:
        pass
    except Exception as err:
        print(err)
    finally:
        # print("\nquit:{}".format(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())))
        print("\nQuit at {}".format(datetime.datetime.today()))
