# -*- coding: utf-8 -*-
from account import Account
import asyncio
import datetime
import random
import time
from concurrent.futures import FIRST_COMPLETED


#todo обвязать логгером и комментариями

class WordStatParser():
    def __init__(self, path_to_accounts, timeout=(3,15), cookie_path='cookies'):
        self.timeout = timeout
        self.cookie_path = cookie_path#'/home/ws_parser/cookies' #todo unix
        self.tasks = []
        # self.path_to_accounts = path_to_accounts
        self.accounts = []
        # self._accounts = []
        self.load_accounts(path_to_accounts)#('/home/ws_parser/proxy.txt') #todo unix
        self.lock = asyncio.Lock()
        self.results = {}

    def load_accounts(self, path_to_accounts):
        #todo количество аккаунтов для загрузки
        for line in open(path_to_accounts):
            proxy_ip, proxy_port, proxy_login, proxy_pass, login, password =line.rstrip().strip('#').split(':')
            if login =='schniperson.innokenty2018' or login =='pupkin.vasya1234561': #todo костыль для теста
                continue

            # self._accounts.append({'proxy_ip': proxy_ip,
            #                        'proxy_port': proxy_port,
            #                        'proxy_login': proxy_login,
            #                        'proxy_pass': proxy_pass,
            #                        'login': login,
            #                        'password': password})

            # acc = Account(acc_value['login'], acc_value['password'], proxy_ip=acc_value['proxy_ip'],
            #               proxy_port=acc_value['proxy_port'], proxy_login=acc_value['proxy_login'],
            #               proxy_pass=acc_value['proxy_pass'])

            #todo сделать подгрузку аккаунтов асинхронной
            acc = Account(login, password, proxy_ip=proxy_ip,
                          proxy_port=proxy_port, proxy_login=proxy_login,
                          proxy_pass=proxy_pass)
            acc.inwork = False
            acc.next_start_time = datetime.datetime.now()
            self.accounts.append(acc)

    def wordstat(self, list_of_keys, marker = '"!'):
        self.tasks = []
        self.marker = marker
        keys = {self._clear_key(key) for key in list_of_keys}
        keys = {x for x in keys if len(x.split())<=7} #ключевая фраза не может состоять больше чем из 7 слов
        self._make_tasks(keys)
        # надо аккаунты подгрузить кстати тоже можно асинхронно
        self.start()

    def _make_tasks(self, keys, limit = 20):
        task = []
        for key in keys:
            task.append(key)
            if len(task)==20:
                self.tasks.append(task)
                task = []
        if len(task)!=0:
            self.tasks.append(task)

    def _clear_key(self, key, delete='!,+/\|;:їі,&#="«»', replace='-.'):
        delete = {x for x in delete}
        replace = {x for x in replace}
        key = key.rstrip()
        result = []
        for letter in key:
            if letter in delete:
                continue
            elif letter in replace:
                result.append(' ')
                continue
            else:
                result.append(letter)
        wrd = ''.join(result)
        while '  ' in wrd:
            wrd = wrd.replace('  ', ' ')
        return wrd

    @asyncio.coroutine
    def _run(self): #async

        tasks = [asyncio.ensure_future(
            self._task(t)) for t in self.tasks]
        for x in asyncio.as_completed(tasks):
            task_dct = yield from x
            #res = self._loop.create_task(task_dct)
            #task_dct = yield from res
            print(task_dct)
            self.results.update(task_dct)

    #@asyncio.coroutine
    async def free_account(self):
        #with (yield from self.lock):
        while True:
            if len([x for x in self.accounts if x.inwork == False]) ==0:
                #(yield from asyncio.sleep(2))
                await asyncio.sleep(2)
                #time.sleep(2)
            else:
                acc = [x for x in self.accounts if x.inwork == False][0]
                acc.inwork = True
                print(acc.name, 'accured')
                return acc
            # while True:
            #     acc = self.accounts.pop(0)
            #     self.accounts.append(acc)
            #     if not acc.inwork:# and datetime.datetime.now() >= acc.next_start_time:
            #         acc.inwork = True
            #         print(acc.name, 'accured')
            #         return acc.name
            #     yield from asyncio.sleep(2)

    @asyncio.coroutine
    def _task(self, task):

        result = self._loop.create_task(self.free_account())
        acc = yield from result
        timeout = random.randint(self.timeout[0], self.timeout[1])
        print(acc.name, timeout)
        task_dct = acc.ws_data(task, self.marker)
        yield from asyncio.sleep(timeout, loop=self._loop)
        print(acc.name, 'released', timeout)
        acc.inwork = False

        return task_dct

    def start(self):
        _loop = asyncio.new_event_loop()#get_event_loop()
        asyncio.set_event_loop(_loop)
        self._loop = asyncio.get_event_loop()
        self._loop.run_until_complete(self._run())
        # self._loop.close()


if __name__ == '__main__':
    parser = WordStatParser(path_to_accounts='proxy.txt')
    #todo listen for task
    #parser.wordstat([x.rstrip() for x in open(r'C:\Users\m.zhukovets\Desktop\price.ru\сезонная пачка пресетов\слова с вордстатом\детские назальные аспираторы.txt', encoding='utf8')])
    parser.wordstat(['"!ideЯ! !- !Челябинск"'])
    print(parser.results)