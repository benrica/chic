#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    作者:     Damon 
    日期:     2018/6/28 
    版本:     1.0
    文件:     ssh_sftp.py.py 
    功能: 
        
"""

"""
模块功能
1.堡垒机功能实现
2.远程命令，脚本调用，支持批量操作
3.SFTP上传下载实现，支持批量
"""

import paramiko
import getpass
import os, sys
import select
import socket
import traceback
import termios
import tty
import re

# 堡垒机功能
# 远程shell交互

war = "\033[5;7mWarning\033[0m"


def interactive_shell(chan):
    # 保存旧的终端信息
    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)
        # select 监控 socket 连接句柄
        while True:
            r, w, e = select.select([chan, sys.stdin], [], [], 1)
            if chan in r:  # 收
                try:
                    x = u(chan.recv(1024))
                    if len(x) == 0:
                        sys.stdout.write('\r\n*** EOF\r\n')
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:  # 发
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                chan.send(x)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


# 堡垒机验证登录及交互
def bastin(hostname, port, username=getpass.getuser()):
    # now connect
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))
    except Exception as e:
        print('*** Connect failed: ' + str(e))
        traceback.print_exc()
        return -1
    try:
        t = paramiko.Transport(sock)
        try:
            t.start_client()
        except paramiko.SSHException:
            print('*** SSH negotiation failed.')
            return -1
        try:
            keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
            except IOError:
                print('*** Unable to open host keys file')
                keys = {}
        # check server's host key -- this is important.
        key = t.get_remote_server_key()
        if hostname not in keys:
            print('*** WARNING: Unknown host key!')
        elif key.get_name() not in keys[hostname]:
            print('*** WARNING: Unknown host key!')
        elif keys[hostname][key.get_name()] != key:
            print('*** WARNING: Host key has changed!!!')
            return -1
        else:
            print('*** Host key OK.')
            # get username
        default_username = input('Username [%s]: ' % username).strip()
        if len(default_username) > 0:
            username = default_username

        default_auth = 'p'
        auth = input('Auth by (p)assword or (r)sa key? [%s] ' % default_auth)
        if len(auth) == 0:
            auth = default_auth
        if auth == 'r':
            default_path = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
            path = input('RSA key [%s]: ' % default_path)
            if len(path) == 0:
                path = default_path
            try:
                key = paramiko.RSAKey.from_private_key_file(path)
            except paramiko.PasswordRequiredException:
                password = getpass.getpass('RSA key password: ')
                key = paramiko.RSAKey.from_private_key_file(path, password)
            t.auth_publickey(username, key)
        else:
            pw = getpass.getpass('Password for %s@%s: ' % (username, hostname))
            t.auth_password(username, pw)

        if not t.is_authenticated():
            print('*** Authentication failed. :(')
            t.close()
            return -1

        chan = t.open_session()  # 打开会话通道
        chan.get_pty()  # 获取终端
        chan.invoke_shell()  # 激活shell终端
        print('*** Here we go!\n')
        interactive_shell(chan)
        chan.close()
        t.close()
    except Exception as e:
        print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
        traceback.print_exc()
        return -1
        try:
            t.close()
        except:
            pass


# 远程cmd调用,sftp
class Myssh(object):
    def __init__(self, host, user=getpass.getuser(), passwd=None, pkey=None, port=22, flag=1):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.pkey = pkey
        self.port = port
        self.ssh = None
        self.read_flag = flag
        self.tran = None
        self.sftp = None

    # 获取连接
    def conn(self, type='ssh'):
        try:
            # get user -> self.user
            # get host -> self.host
            auth_type = ''
            private_key = ''
            #        for key in (self.pkey,os.path.join(os.environ['HOME'], '.ssh','id_rsa'),os.path.join(os.environ['HOME'], '.ssh','id_dsa')):
            if self.pkey and os.path.exists(self.pkey):
                auth_type = 'rsa' if self.pkey.endswith('rsa') else 'dsa'
            if not self.passwd:
                if not self.pkey:
                    self.passwd = getpass.getpass('Password for %s@%s: ' % (self.user, self.host)).strip()
                else:
                    if auth_type == 'rsa':
                        try:
                            private_key = paramiko.RSAKey.from_private_key_file(self.pkey)
                        except paramiko.PasswordRequiredException:
                            password = getpass.getpass('RSA key password: ')
                            private_key = paramiko.RSAKey.from_private_key_file(self.pkey, password)
                    elif auty_type == 'dsa':
                        try:
                            private_key = paramiko.DSSKey.from_private_key_file(self.pkey)
                        except paramiko.PasswordRequiredException:
                            password = getpass.getpass('DSS key password: ')
                            private_key = paramiko.DSSKey.from_private_key_file(self.pkey, password)
                    else:
                        print('private_key: [%s] format err.' % self.pkey)
                        return -1
            if type == 'ssh':
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if self.passwd:
                    self.ssh.connect(hostname=self.host, port=self.port, username=self.user, password=self.passwd)
                else:
                    self.ssh.connect(hostname=self.host, port=self.port, username=self.user, pkey=private_key)
            else:
                self.tran = paramiko.Transport((self.host, self.port))
                if self.passwd:
                    self.tran.connect(username=self.user, password=self.passwd)
                else:
                    self.tran.connect(username=self.user, pkey=private_key)
                self.sftp = paramiko.SFTPClient.from_transport(self.tran)
        except Exception as e:
            print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
            traceback.print_exc()
            return -1
        else:
            conn_type = 'SSH' if type == 'ssh' else 'SFTP'
            print('\033[41m*** %s Connect %s@%s succ.\033[0m' % (conn_type, self.user, self.host))

    # 远程执行命令并获取结果
    def do_cmds(self, *cmds):
        for cmd in cmds:
            print('\033[1m*** Excute cmd [%s] and the out_result is below.\033[0m\n' % cmd)
            try:
                stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=60 * 60)
            except socket.timeout:
                print('***,Time out for 1 hour,next..')
                continue
            except Exception as e:
                print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
                traceback.print_exc()
                continue
            if self.read_flag:  # 正常模式收取数据
                for line in stdout: print(line, end='')
            else:  # 利用 select 监听收取数据
                while not stdout.channel.exit_status_ready():
                    if stdout.channel.recv_ready():
                        rl, wl, xl = select.select([stdout.channel], [], [], 1)
                        if len(rl) > 0:
                            # print(stdout.channel.recv(1024))
                            data = stdout.channel.recv(1024)
                            while data:
                                print(data, end='')
                                data = stdout.channel.recv(1024)
                stdin.channel.close()
                stdout.channel.close()
                stderr.channel.close()
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print('*** %s Excute cmd [%s] failed. err_msg: %s' % (war, cmd, stderr.read().strip()))
            print()

    # 关闭连接
    def disconn(self, type='ssh'):
        try:
            if type == 'ssh':
                self.ssh.colse()
            else:
                self.tran.close()
        except:
            pass

    # 批量执行命令
    def call_cmds(self, *cmds):
        if not self.conn():
            self.do_cmds(*cmds)
            self.disconn()

    # 文件上传
    def put(self, local_file, remote_file):
        if not self.sftp: self.conn('sftp')
        if remote_file.find(os.sep) >= 0:
            try:
                self.sftp.mkdir(os.path.dirname(remote_file))
            except:
                pass
        try:
            r = self.sftp.put(local_file, remote_file)
        except Exception as e:
            print('*** %s Caught exception: ' % war + str(e.__class__) + ': ' + str(e))
            print('*** Put %s to %s:%s failed.' % (local_file, self.host, remote_file))
            print(os.path.dirname(remote_file))
            return -1
        else:
            print('*** Put %s to %s:%s success.' % (local_file, self.host, remote_file))

    # 文件下载
    def get(self, remote_file, local_file):
        if not self.sftp: self.conn('sftp')
        try:
            r = self.sftp.get(remote_file, local_file)
        except Exception as e:
            print('*** %s Caught exception: ' % war + str(e.__class__) + ': ' + str(e))
            print('*** Get %s from %s failed.' % (remote_file, self.host))
            return -1
        else:
            if os.path.basename(remote_file) == os.path.basename(local_file):
                print('*** Get %s from %s and put to %s success.' % (remote_file, self.host, local_file))
            else:
                print('*** Get %s from %s and rename to %s success.' % (remote_file, self.host, local_file))

    # 批量文件上传
    def batch_put(self, *args, **kwargs):
        try:
            if not self.sftp: self.conn('sftp')
            remote_dir = kwargs['remote_dir']
            remote_dir = remote_dir or os.environ['HOME'] + '/_tmp_put_dir'
            try:
                self.sftp.mkdir(remote_dir)
            except Exception as e:
                pass
            succ_count, fail_count = 0, 0
            for obj in args:
                if os.path.exists(obj) and os.path.isfile(obj):
                    if obj.find('~') >= 0:
                        obj = os.path.expanduser(obj)
                    lfile = os.path.abspath(obj)
                    filename = os.path.basename(lfile)
                    rfile = os.path.join(remote_dir, filename)
                    rtn = self.put(lfile, rfile)
                    if not rtn:
                        succ_count += 1
                    else:
                        fail_count += 1
        except Exception as e:
            print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
            return -1
        finally:
            print('*** Batch Put success: %d failed: %d ' % (succ_count, fail_count))

    # 批量文件下载
    def batch_get(self, remote_file, local_dir=os.getcwd()):
        try:
            if not self.sftp: self.conn('sftp')
            if not os.path.isdir(local_dir):
                print('%s not a directory' % local_dir)
                return -1
            if not os.path.exists(local_dir):
                os.mkdir(local_dir)
            if remote_file.find(',') > 0:
                rfile_list = remote_file.split(',')
            else:
                remote_dir = os.path.dirname(remote_file)
                if not remote_dir: remote_dir = '.'
                self.sftp.chdir(remote_dir)
                pattern = '.' + os.path.basename(remote_file) if os.path.basename(remote_file).startswith(
                    '*') else os.path.basename(remote_file)
                reg_file = re.compile(os.path.basename(pattern))
                rfile_list = [file for file in self.sftp.listdir(remote_dir) if reg_file.search(file)]
                print('--' + rfile_list)
                for file in rfile_list:
                    try:
                        self.sftp.stat(file)
                    except:
                        rfile_list.remove(file)
            os.chdir(local_dir)
            succ_count, fail_count = 0, 0
            for rfile in rfile_list:
                rtn = self.get(rfile, rfile)
                if not rtn:
                    succ_count += 1
                else:
                    fail_count += 1
        except Exception as e:
            print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
            return -1
        finally:
            print('*** Batch Get success: %d failed: %d ' % (succ_count, fail_count))