#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    作者:     Damon 
    日期:     2018/6/28 
    版本:     1.0
    文件:     ora_dbi.py.py 
    功能: 
        
"""

import cx_Oracle
import datetime
import os, sys, re


class ora_eng(object):
    def __init__(self, dsn, user, passwd, arraysize=50, parallel_num=None, log_lvl=0):
        self.dsn = dsn
        self.user = user
        self.passwd = passwd
        self.log_lvl = log_lvl
        try:
            self.dbh = cx_Oracle.connect(dsn=self.dsn, user=self.user, password=self.passwd)
            self.cur = self.dbh.cursor()
            self.cur.execute("alter session set nls_date_format='yyyy-mm-dd hh24:mi:ss'")
        except Exception as err:
            print(err)
            return -1
        if self.cur.arraysize < arraysize: self.cur.arraysize = arraysize

        # DQL操作 select

    # cx_Oracle.paramstyle = qmark|named|numeric  默认: named
    def show_format(self, sql, **kwargs):
        if not re.match('select|with', sql.lstrip(), re.I):
            print('DQL sql definition is wrong..')
            return -1
        begin_time = datetime.datetime.now()
        try:
            self.cur.execute(sql, kwargs)
            colnames = [desc[0] for desc in self.cur.description]
            if self.log_lvl == 0:
                print("\033[36;1m[dburl:" + self.dbh.dsn + ']\n' + sql + "\033[0m")
                print('-' * 38)
            compute_flag, done_flag, first_flag = True, False, True
            max_key_len = max(len(key) for key in colnames)
            key_len = dict((idx, len(col)) for idx, col in enumerate(colnames))
            tmp_rows = []
            row_mode = True
            while True:
                rows = self.cur.fetchmany()
                if not rows:
                    done_flag = True
                if compute_flag:
                    for row in rows:
                        for idx, val in enumerate(row):
                            if key_len[idx] < len(str(val)): key_len[idx] = len(str(val))
                        tmp_rows.append(row)
                    # 计算记录数大于5000 或 记录总数不足5000 后不再作计算 （优化操作）
                    if self.cur.rowcount >= 5000 or (done_flag and self.cur.rowcount < 5000):
                        compute_flag = 0
                        record_width = sum(key_len.values()) + len(key_len) - 1
                        _, terminal_size = os.popen('stty size').read().split()
                        continue
                # 打印记录明细
                else:
                    # 首次打印要加上被计算的记录,打印交互信息
                    if first_flag:
                        tmp_rows.extend(rows)
                        rows = tmp_rows
                        if record_width > int(terminal_size):
                            reply = input(
                                "\033[1m\n→提醒:输出结果长度({})大于终端屏幕宽度({}),启用列模式打印(y/n)?[n] \033[0m".format(record_width,
                                                                                                      terminal_size)).lower()
                            if reply not in ('y', 'yes'):
                                if self.cur.rowcount > 500:
                                    print("\033[1m\n→提醒:查询结果总记录数[5000+]行,默认打印前[20]行,回车刷屏显示,Ctrl+c 中断查询..\n\033[0m")
                            else:
                                row_mode = False
                        first_flag = False
                    have_print_count = 0
                    # 行模式打印
                    if row_mode:
                        for idx, col in enumerate(colnames):
                            print("\033[36;1m%-*s\033[0m" % (key_len[idx], col), end=' ')
                        print()
                        for idx, col in enumerate(colnames):
                            print("%-*s" % (key_len[idx], '-' * key_len[idx]), end=' ')
                        print()
                        for record in rows:
                            for idx, col in enumerate(record):
                                print("%-*s" % (key_len[idx], col), end=' ')
                            print()
                            have_print_count += 1
                            if have_print_count == 20 and self.cur.rowcount > 5000: input().strip()
                    # 列模式打印
                    else:
                        print()
                        for record in rows:
                            for idx, col in enumerate(record):
                                print("%*s :%s" % (max_key_len, colnames[idx], col))
                            have_print_count += 1
                            print('-' * max_key_len + str(have_print_count) + " 按回车继续、Ctrl+c退出..")
                            input()
                    if done_flag: break
                if done_flag: break
        except KeyboardInterrupt as interrupt:
            print(interrupt)
            return -1
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            return -1
        else:
            use_time = (datetime.datetime.now() - begin_time).microseconds / 10 ** 6
            print("\n%d rows selected. Elapsed: %f seconds\n" % (self.cur.rowcount, use_time))
        return 0

    # 分栏打印
    def show_format2(self, sql, cols, **kwargs):
        pass

    # DML
    def ora_dml(self, sql, verbose=True, **kwargs):
        if not re.match('insert|update|delete|merge', sql.lstrip(), re.I):
            print('DML sql definition is wrong..')
            return -1
        try:
            print('Runing sql:[%s]' % sql)
            self.cur.execute(sql, kwargs)
            if input('%d rows affected,going to commit(y/n)?[n] ' % self.cur.rowcount).lower() in ('y', 'yes'):
                self.dbh.commit()
            else:
                self.dbh.rollback()
        except Exception as err:
            print('Got exception: %' % err)
            try:
                self.dbh.rollback()
            except Exception as err:
                print('Got exception: %s Rollback fail..' % err)
            else:
                print('Rollback succ..')
            return -1
        else:
            if verbose: print('Commit done.. %d affected' % self.cur.rowcount)
        return 0

    # DDL
    def ora_ddl(self, sql, verbose=True):
        if re.match('insert|update|delete|merge|select|with', sql.ltrim(), re.I):
            print('DDL sql definition is wrong..')
            return -1
        try:
            self.cur.execute(sql)
        except Exception as err:
            print(err)
            return -1
        else:
            if verbose: print('Call sql:[%s] succ..' % sql)
        return 0

        # disconnect db

    def ora_disconnect(self):
        if self.cur:
            self.cur.close()
        if self.dbh:
            self.dbh.close()
