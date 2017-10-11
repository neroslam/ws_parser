import requests
import re
import json
from urllib import parse
from transport import get_ws_data
import os
import warnings
warnings.filterwarnings("ignore")

#todo нет проверки валидности страницы
#todo нет проверки капчи и её обработки
#todo нет валидатора ответа от яши, мало ли что он там в ерроры насыплет

class Account():

    def __init__(self, account_name, password,  cookie_path='cookies', proxy_ip=None, proxy_port=None, proxy_login=None,
                 proxy_pass=None, proxy_type = 'https'):
        self.name = account_name
        self.password = password
        self.cookies_path = os.path.join(os.path.abspath(os.curdir), cookie_path)#'/home/ws_parser/cookies' TODO UNIX
        self.cookies = {}
        # подгрузка прокси
        self.proxy = {'proxy_ip':proxy_ip,
                      'proxy_port': proxy_port,
                      'proxy_login': proxy_login,
                      'proxy_pass': proxy_pass,
                      'proxy_type': proxy_type}
        # self.proxy_ip = proxy_ip
        # self.proxy_port = proxy_port
        # self.proxy_login = proxy_login
        # self.proxy_pass = proxy_pass
        # self.proxy_type = proxy_type

        self.set_cookie()

    def set_cookie(self):
        """фукнция устанавливает куку нашему аккаунту"""
        print(self.cookies_path)
        cookies_files = os.listdir(self.cookies_path)  # список хранимых логинов с куками
        if self.name in cookies_files:  # если логн есть - используем старую куку
            self.load_cookie()
        else:  # если логина нет - подгружаем новые куки и сохраняем их в хранилище
            self.get_cookie()
            self.save_cookie()

    def load_cookie(self):
        """загрузка куков из хранилища"""
        filename = os.path.join(self.cookies_path, self.name)
        with open(filename) as f:
            self.cookies = json.load(f)

    def get_cookie(self):
        '''парсинг куков из директа'''
        from transport import DirectAuth
        _acc = DirectAuth(self.name, self.password, proxy=self.proxy)
        _acc.autorize()
        cookies = _acc.get_cookie()
        self.cookies = cookies

    def save_cookie(self):
        """сохранить куки в хранилище"""
        filename = os.path.join(self.cookies_path, self.name)
        with open(filename, 'w') as f:
            json.dump(self.cookies, f)

    def update_cookie(self):
        """получить новые куки и перезаписать"""
        self.get_cookie()
        self.save_cookie()

    def _prepare_keys(self, list_of_keys, marker=None):
        if marker == '"':
            return '\n'.join(['"{}"'.format(x) for x in list_of_keys])+'\n'
        elif marker == '"!':
            return '\n'.join(['"{}"'.format(' '.join(['!{}'.format(x) for x in z.split()])) for z in list_of_keys])+'\n'
        elif marker == '!':
            return '\n'.join(['{}'.format(' '.join(['!{}'.format(x) for x in z.split()])) for z in list_of_keys])+'\n'
        else:
            return '\n'.join(list_of_keys)+'\n'

    def ws_data(self, list_of_keys, marker=None):
        keys = self._prepare_keys(list_of_keys, marker)

        data = get_ws_data(keys, self.cookies, self.proxy, name = self.name)
        return data

if __name__ == '__main__':
    acc = Account('schniperson.innokenty2018', 'snduptsndupt', proxy_ip='5.8.8.118', proxy_port='24579', proxy_login='lexicon2004', proxy_pass='N7F2Qy7')
    print(acc.ws_data(['котики', 'бытовые холодильники'], '"!'))
