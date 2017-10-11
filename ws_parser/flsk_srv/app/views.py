from flsk_srv.app import app
from flask import render_template, jsonify, request, redirect
import random
import string
import json
import socket
from transport import  send_mail

tasks = []

def check_tasks():
    if len(tasks)==0:
        pass
    elif len([x for x in tasks if x['status']=='added'])>=1:
        #todo надо чистить историю реквестов
        #todo размер буфера в сокете
        tsk = [x for x in tasks if x['status'] == 'added'][0]
        tsk['status'] = 'pending'
        conn = socket.socket()
        conn.connect(('localhost', 5050))
        conn.send(json.dumps({'keys':tsk['keywords'],
                              'quote':tsk['quote'],
                              'vskl':tsk['vskl']}).encode())
        conn.send(b'\x04')
        print('push')
        answer = socket_rcv(conn)
        #answer = conn.recv(8000).decode()
        print(answer)
        answer = json.loads(answer)
        conn.close()
        if answer['status'] =='Busy':
            tsk['status'] = 'added'
        else:
            tsk['results'] = answer
            tsk['status'] = 'done'
            print(tsk)
            if not tsk['mail'] == 'PriceSeo':
                send_mail('<br/>'.join(['{}\t{}'.format(x[0], x[1]) for x in tsk['results']['keys']]), owner=tsk['mail'], subject='отчет по вордстату - {} - {}{}'.format(tsk['id'], tsk['quote'], tsk['vskl']))

def socket_rcv(_socket):
    data =[]
    while True:
        d = _socket.recv(1024).decode()
        if not d: break
        data.append(d)
    return ''.join(data)

from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler(max_instances=50)
scheduler.start()
scheduler.add_job(check_tasks, trigger='interval', seconds=5)


from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    keywords_field = TextAreaField('keywords_field', validators = [DataRequired()])
    mail = TextAreaField('mail', validators = [DataRequired()])
    quote = BooleanField('quote', default = True)
    vskl = BooleanField('vskl', default = False)

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
def index():
    """форма для простых смертных"""
    form = LoginForm()
    return render_template('index.html', form = form, title = 'вордстат')#'\n'.join(os.listdir('../flsk_srv/templates/'))

@app.route('/handle_data', methods=['POST'])
def handle_data():
    '''обработка формы с вебморды'''
    keywords = [x for x in request.form['keywords_field'].split('\r\n') if len(x)>2]
    mail = request.form['mail']
    if 'quote' in request.form:
        quote = True
    else:
        quote = False
    if 'vskl' in request.form:
        vskl = True
    else:
        vskl = False
    add_task(keywords, quote, vskl, mail)
    return redirect('status')

@app.route('/status')
def status():
    """страница с рендером задач"""
    return render_template('status.html', tasks = tasks, title = 'Статус вордстата')

def add_task(keywords, quote, vskl, mail,  isPrice = 0):
    """добавляет задачу в тасклист"""

    def get_new_id():
        return "".join(
            random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(20))

    _id = get_new_id()
    if isPrice:
        tasks.insert(0,
                     {'id':_id,
                      'keywords': keywords,
                      'keywords_cnt': len(keywords),
                      'quote': quote,
                      'vskl': vskl,
                      'mail': 'PriceSeo',
                      'status': 'added',
                      'link': ''
                      })
    else:
        tasks.append({'id':_id,
                      'mail': mail,
                      'keywords': keywords,
                      'keywords_cnt': len(keywords),
                      'quote': quote,
                      'vskl': vskl,
                      'status': 'added',
                      'link': ''})
    return _id

@app.route('/api/send', methods = ['GET', 'POST'])
def api_post_words():
    """апи метод для отправки запроса с сервера"""
    #todo добавить обработку отсутствия ключей
    token = add_task(keywords=[x for x in request.json['keys'] if len(x)>2],
             quote=request.json['quote'],
             vskl=request.json['vskl'],
             mail = 'PriceSeo',
             isPrice =1)
    return json.dumps({'status':'success','token':token})
    #return redirect('/')

@app.route('/api/tasks')
def get_tasks():
    """апи метод со статусом задач"""
    return json.dumps({'tasks': tasks})

#todo надо добавить обработку маркеров


