from selenium import webdriver
import requests
from urllib import parse
import re
import asyncio
import smtplib
from email.mime.text import MIMEText

class DirectAuth():
    def __init__(self, login, password, proxy):
        self.login = login
        self.password = password
        self.proxy = proxy
        self.cookies = {}

    def config_service_args(self):
        """если был указан прокси - конфигурируем фантом для использования с прокси"""
        if self.proxy['proxy_port'] == None:
            raise ValueError(
                'указан адрес прокси, но не указан порт - {}:{}'.format(self.proxy['proxy_ip'], self.proxy['proxy_port']))
        service_args = [
            '--proxy={}:{}'.format(self.proxy['proxy_ip'], self.proxy['proxy_port']),
            '--proxy-type={}'.format(self.proxy['proxy_type'])
        ]
        if self.proxy['proxy_login'] != None:
            if self.proxy['proxy_pass'] == None:
                raise ValueError(
                    'указан логин для прокси, но не указан пароль - {}:{}'.format(self.proxy['proxy_login'], self.proxy['proxy_pass']))
            service_args.append('--proxy-auth={}:{}'.format(self.proxy['proxy_login'], self.proxy['proxy_pass']))
        return service_args

    def autorize(self):
        ''' используем драйвер фантома для получения кук устанавливаемых через JS'''
        if self.proxy['proxy_ip'] == None:
            driver = webdriver.PhantomJS()#(executable_path='./phantom_js/phantomjs.exe')
        else:
            # если указано прокси - конфигурируем с прокси
            driver = webdriver.PhantomJS(executable_path='./phantom_js/phantomjs.exe',
                                         service_args=self.config_service_args())
        driver.get('https://direct.yandex.ru')  # переходим на директ.яндекс и получаем JS куки
        for x in driver.get_cookies():
            self.cookies[x['name']] = x['value']
        # self.cookies.update(driver.get_cookies())  # обновляем наши куки
        driver.close()

        # производим авторизацию в сервисе и обновляем куки
        payload = {
            'from': 'direct',
            'login': self.login,
            'origin': '',
            'passwd': self.password,
            'retpath': 'https://direct.yandex.ru'
            #'timestamp': ''
        }
        if self.proxy['proxy_ip'] ==None:
            auth_r = requests.post('https://passport.yandex.ru/auth', verify=False, cookies=self.cookies, data=payload) #todo завернуть параметры в kwargs
        else:
            auth_r = requests.post('https://passport.yandex.ru/auth', verify=False, cookies=self.cookies, data=payload,
                                   proxies=proxy_requests(self.proxy))
        for r in auth_r.history:
            self.cookies.update(r.cookies.get_dict())

    def get_cookie(self):
        """возвращает свеженькие куки"""
        return self.cookies

def proxy_requests(proxy):
    '''делает прокси подходящие под requsts
    proxies = {
    'http': 'socks5://user:pass@host:port',
    'https': 'socks5://user:pass@host:port'
    }'''
    if proxy['proxy_login']!=None and proxy['proxy_pass']!=None:
        proxies = {'https': '{proxy_type}://{proxy_login}:{proxy_pass}@{proxy_ip}:{proxy_port}'.format(**proxy)}
    else:
        proxies = {'https': '{proxy_type}://{proxy_ip}:{proxy_port}'.format(**proxy)}
    return proxies

def get_ws_data(keys, cookies, proxy, name = None):
    start_url = 'https://direct.yandex.ru/registered/main.pl?cmd=advertize&mediaType=text&csrf_token='
    #todo try except
    #todo add marker of collected
    #todo запилить асинхронную версию функции
    r = requests.get(start_url, verify=False, cookies=cookies, proxies=proxy_requests(proxy)) ##todo завернуть параметры в kwargs
    campain_url = parse.splitquery(r.url)[0]
    token_reg = re.compile('(?<=csrf_token":").*?(?=")')
    #print(r.text)
    csrf_token = token_reg.search(r.text).group(0)
    print(keys)
    params = wordstat_dct(csrf_token, keys)
    r_wordstat = requests.post(campain_url,
                               verify=False,
                               cookies=cookies,
                               data=params,
                               proxies=proxy_requests(proxy), #todo завернуть параметры в kwargs а то если прокси пустые все сыплется
                               headers={'referer': campain_url,
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'})
    results = {}
    try:
        for x in r_wordstat.json()['data_by_positions']:
            results[r_wordstat.json()['key2phrase'][x['md5']].replace('"', '').replace('!', '')] = x['shows']
    except KeyError:
        print(name)
        print(r_wordstat.text)
        return None
    return results

def wordstat_dct(csrf_token, keys):
    wordstat_dct = {
        'csrf_token': csrf_token,
        'cmd': 'ajaxDataForNewBudgetForecast',
        'advanced_forecast': 'yes',
        'period': 'month',
        'period_num': '0',
        'phrases': keys,
        'geo': '0',
        'unglue': '0',
        'fixate_stopwords': '0',
        'currency': 'RUB',
        'json_minus_words':[]
    }
    return parse.urlencode(wordstat_dct)

def send_mail(message, owner, subject = 'Косяки в роботсах'):
    #todo send csv
    # отправитель
    me = 'seo.alarm@rambler-co.ru'
    # получатель
    you = owner
    #print(you)
    # текст письма
    text = message#'Тестовое письмо!\nОтправка письма из python'
    # заголовок письма
    subj = subject

    # SMTP-сервер
    server = "mail.rambler-co.ru"
    port = 587
    user_name = "seo.alarm"
    user_passwd = "eKD6luHsxh5"

    # формирование сообщения
    msg = MIMEText(text, "html", "utf-8")
    msg['Subject'] = subj
    msg['From'] = me
    msg['To'] = you

    # отправка
    s = smtplib.SMTP(server, port)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(user_name, user_passwd)
    s.sendmail(me, you, msg.as_string())
    s.quit()
