from gevent import monkey;

monkey.patch_all()
import gevent
import hashlib
import json
import os
import random
import struct
from db.model import MyServer
from conf.settings import DB_PATH, BASE_PATH,ip,port

current_user = {}

server = MyServer(ip, port)


def login(conn):
    while True:
        data = conn.recv(1024).decode('utf-8')
        # 接收字符串的MD5值进行对比
        if data == 'q':
            return
        with open(DB_PATH) as f:
            user_dict = json.load(f)
        # MD5错误,返回字符串False
        if data not in user_dict:
            conn.send('False'.encode('utf-8'))
            continue
        # MD5正确,返回随机身份字符串
        random_num = str(random.uniform(1, 0))
        m = hashlib.md5(random_num.encode('utf-8'))
        conn.send(m.hexdigest().encode('utf-8'))
        # 添加身份MD5码到当前登陆用户列表中
        current_user[conn] = m.hexdigest()
        return


def register(conn):
    while True:
        data = conn.recv(1024).decode('utf-8')
        dic = json.loads(data)
        with open('user_info.json') as f:
            user_dict = json.load(f)
        usrlist = []
        usrnum = []
        for i in user_dict:
            usrlist.append(user_dict[i]['username'])
            usrnum.append(user_dict[i]['uid'])
        if dic['username'] in usrlist:
            conn.send('False'.encode('utf-8'))
            continue
        m = hashlib.md5((dic['username'] + dic['password']).encode('utf-8'))
        m.update('update'.encode('utf-8'))
        md5_code = m.hexdigest()
        user_num = usrnum[-1] + 1
        user_dict[md5_code] = {'uid': user_num, 'username': dic['username']}
        with open('user_info.json', mode='w', encoding='utf-8') as f:
            json.dump(user_dict, f)
        conn.send('Ture'.encode('utf-8'))
        return


def upload(conn):
    header = conn.recv(4)
    dict_size = struct.unpack('i', header)[0]
    dict_str = conn.recv(dict_size).decode('utf-8')
    header_dict = json.loads(dict_str)
    total_size = 0
    with open('%s%s%s' % (DB_PATH, os.path.sep, header_dict['filename']), mode='wb') as f:
        while total_size < header_dict['size']:
            data = conn.recv(1024)
            total_size += len(data)
            f.write(data)
        return


data_path = os.path.join(BASE_PATH, 'data')
TOP_PATH = data_path  # 设置顶层目录


# 返回文件的路径


def check_dir(conn, i, path=TOP_PATH):
    current_path = path
    top_dir = TOP_PATH
    lis = os.listdir(path)
    # print(lis)
    if i == 0:
        conn.send((json.dumps(lis)).encode('utf-8'))
    # print('has send')
    n_lis = list(enumerate(lis))
    while True:
        choose = conn.recv(1024).decode('utf-8')
        if choose == '0':
            if path == top_dir:
                conn.send(json.dumps(('False', '不能超过顶层目录!')).encode('utf-8'))
                continue
            path_lis = path.split('%s' % os.path.sep)
            path = path[:len(path) - (len(path_lis[-1])) - 1]
            if path.endswith(':'):
                path = path + os.path.sep
                conn.send((json.dumps(('Ture', os.listdir(path))).encode('utf-8')))
                return check_dir(conn, 1, path)
            conn.send((json.dumps(('Ture', os.listdir(path))).encode('utf-8')))
            return check_dir(conn, 1, path)
        path = os.path.join(current_path, n_lis[int(choose) - 1][1])
        if os.path.isfile(path):
            conn.send((json.dumps(('successful', path.split(os.path.sep)[-1])).encode('utf-8')))
            return path
        conn.send((json.dumps(('Ture', os.listdir(path))).encode('utf-8')))
        return check_dir(conn, 1, path)


def download(conn):
    filename = check_dir(conn, 0)
    conn.recv(1024)
    with open(filename, mode='rb') as f:
        total_size = sum(len(line) for line in f)
    header_dict = {
        'size': total_size, 'filename': filename
    }
    header_dict_bytes = json.dumps(header_dict).encode('utf-8')
    dict_size = struct.pack('i', len(header_dict_bytes))
    conn.send(dict_size)
    conn.send(header_dict_bytes)
    with open(filename, mode='rb') as f:
        current_size = 0
        while current_size < total_size:
            conn.send(f.read(1024))
            current_size += 1024
        return


def run(conn):
    try:
        while True:
            list = []
            if current_user:
                for i in current_user:
                    list.append(current_user[i])
                print('\r%s' % list, end='')
            data = conn.recv(1024)
            dict = MyServer.get_dict(data)
            func_dict = {
                'login': login,
                'register': register,
                'upload': upload,
                'download': download
            }
            if dict['func'] == 0:
                conn.close()
                if current_user:
                    current_user.pop(conn)
                    lis = []
                    if current_user:
                        for i in current_user:
                            lis.append(current_user[i])
                        print('\r%s' % lis, end='')
                if not current_user:
                    print('\r', end='')
                return
            func_dict[dict['func']](conn)
    except ConnectionResetError:
        conn.close()
        if current_user:
            current_user.pop(conn)
            lis = []
            if current_user:
                for i in current_user:
                    lis.append(current_user[i])
                print('\r%s' % lis, end='')
        if not current_user:
            print('\r', end='')
        return


def main():
    while True:
        conn, addr = server.activate()
        gevent.spawn(run, conn)
