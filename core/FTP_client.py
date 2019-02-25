import hashlib
import json
import os
import struct

import conf.settings
from db.model import MyClient

current_user = None

client = MyClient(conf.settings.ip, conf.settings.port)


def show_process(percent, width=50):
    str = '[%%-%ds]' % width % ('>' * int(percent * width))
    print('\r' + str + '进度:%.2f%%' % (percent * 100), end='')


def login():
    global current_user
    while True:
        username = input('username:(用户名密码均填q为退出)')
        password = input('password:')
        if not (username and password):
            print('帐号或密码不能为空!')
            continue
        if username == password == 'q':
            client.send('q')
            return
        # 发送MD5码
        m = hashlib.md5((username + password).encode('utf-8'))
        m.update('update'.encode('utf-8'))
        msg = m.hexdigest()
        client.send(msg)
        # 接收状态码
        msg = client.recv(1024)
        if msg == 'False':
            print('帐号/密码错误!')
            continue
        print('登陆成功!')
        current_user = msg
        return


def register():
    while True:
        username = input('请输入注册用户名:')
        if not username:
            print('用户名不能为空!')
            continue
        password1 = input('请输入注册密码:')
        if not password1:
            print('密码不能为空!')
            continue
        password2 = input('请确认密码:')
        if password1 != password2:
            print('两次密码输入不一致!')
            continue
        client.send_dict({'username': username, 'password': password1})
        data = client.recv(1024)
        if data == 'False':
            print('该用户名已存在!')
            continue
        print('创建成功!')
        return


def upload():
    while True:
        path = input('请输入上传文件路径:')
        if not os.path.exists(path):
            print('路径不存在!')
            continue
        lis = path.split('\\')
        filename = lis[-1]
        with open(path, mode='rb') as f:
            total_size = sum(len(line) for line in f)
        header_dict = {
            'size': total_size, 'filename': filename
        }
        header_dict_bytes = json.dumps(header_dict).encode('utf-8')
        dict_size = struct.pack('i', len(header_dict_bytes))
        client.my_send(dict_size)
        client.my_send(header_dict_bytes)
        with open(path, mode='rb') as f:
            upload_size = 0
            while upload_size < header_dict['size']:
                client.my_send(f.read(1024))
                upload_size += 1024
                show_process(upload_size / header_dict['size'], 30)
            print('\r上传成功！')
            return


def check_dir(lis):
    n_lis = list(enumerate(lis))
    for file in n_lis:
        print('%d.%s' % (file[0] + 1, file[1]))
    print('0.上一层')
    while True:
        choose = input('>>:')
        if not choose:
            print('输入不能为空!')
            continue
        if not choose.isdigit():
            print('输入必须为整数!')
            continue
        l = [index[0] + 1 for index in n_lis]
        l.append(0)
        if int(choose) not in l:
            print('超出索引范围!')
            continue
        client.send(choose)
        response = json.loads(client.recv(2048))
        # reponse=(Ture/False/successful,错误信息或新的列表)
        if response[0] == 'False':
            print(response[1])
            continue
        if response[0] == 'Ture':
            return check_dir(response[1])
        if response[0] == 'successful':
            return (True, response[1])


def download():
    lis = json.loads(client.recv(2048))
    res = check_dir(lis)
    if res[0]:
        while True:
            path = input('请输入文件存放路径:')
            if not os.path.isdir(path):
                print('非法文件夹路径')
                continue
            client.send('ready')
            header = client.my_recv(4)
            dict_size = struct.unpack('i', header)[0]
            dict_str = client.recv(dict_size)
            header_dict = json.loads(dict_str)
            total_size = 0
            with open('%s%s%s' % (path, os.path.sep, res[1]), mode='wb') as f:
                while total_size < header_dict['size']:
                    data = client.my_recv(1024)
                    total_size += len(data)
                    f.write(data)
                    show_process(total_size / header_dict['size'], 30)
                print('\r下载成功！')
            return


func_dict = {
    '1': login,
    '2': register,
    '3': upload,
    '4': download
}


def run():
    while True:
        print('''欢迎使用FTP
    1、登录
    2、注册
    3、上传
    4、下载
    0、退出
    请输入你的操作''')
        choose = input('>>:')
        if choose == '0':
            client.send_dict({'func': 0})
            return
        if choose not in func_dict:
            print('非法输入')
            continue
        if choose == '3' or choose == '4':
            if not current_user:
                print('请先登录！')
                continue
        client.send_dict({'func': func_dict[choose].__name__})
        func_dict[choose]()


if __name__ == '__main__':
    run()
