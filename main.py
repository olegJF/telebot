# -*- coding: utf-8 -*-
import re
import os
import requests
from flask import Flask
from flask import request
from flask import jsonify
# from dotenv import load_dotenv

# from flask_sslify import SSLify
# load_dotenv()

TOKEN = os.environ.get('TOKEN')
URL = 'https://api.telegram.org/bot{}/'.format(TOKEN)
headers = {'user-agent': 'my-app/0.0.1'}
API_URL = os.environ.get('API_URL')
app = Flask(__name__)
app.config['DEBUG'] = False
# sslify = SSLify(app)

# https://api.telegram.org/botTOKEN/setWebhook?url=https://b9f92555.ngrok.io
# https://api.telegram.org/botTOKEN/deleteWebhook

    
def send_message(chat_id, text='Empty'):
    session = requests.Session()
    url = URL + 'sendMessage'
    r = session.get(url, headers=headers, 
                    params=dict(chat_id = chat_id, 
                                text = text, 
                                parse_mode = 'Markdown',)) # parse_mode = 'HTML'
    
    # print(r.json())
    return r.json()
    

def parse_text(text):
    command_pattern = r'/\w+'
    vacancy_pattern = r'@\w+' # @\w+\+\w+
    
    if '/' in text:
        addresses = {'cities': '/cities', 'sp': '/specialties'}
        if '/start' in text or '/help' in text:
            message = '''
            Для того, чтобы узнать, какие города доступны, отправьте в сообщении `/cities`. 
            Чтобы узнать о доступных специальностях - отправьте `/sp` 
            Чтобы сделать запрос на сохраненные вакансии, отправьте в сообщении через пробел - @город @специальность. 
            Например так - `@kyiv @python` 
            '''
            return message
        command = re.search(command_pattern, text).group().replace('/', '')
        return addresses.get(command, None)
    elif '@' in text:
        # @kyiv @python
        v_search = re.findall(vacancy_pattern, text)
        commands = [x.replace('@', '') for x in v_search]
        return commands
    else:
        return None


def get_api_response(addr):
    session = requests.Session()
    url= API_URL + addr
    r = session.get(url, headers=headers).json()
    # print(r)
    return r
    

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        r = request.get_json()
        chat_id = r['message']['chat']['id']
        text_msg = r['message']['text']
        tmp = parse_text(text_msg)
        # print('tmp', tmp, 'text_msg', text_msg)
        text_msg = 'Неверный запрос'
        if tmp:
            # print('TMP!')
            if len(tmp) == 2:
                address = '/vacancies/?city={}&specialty={}'.format(*tmp)
                print(address)
                resp = get_api_response(address)
                if resp:
                    pices = []
                    size_of_resp = len(resp)
                    extra = len(resp)%10
                    if size_of_resp < 11:
                        pices.append(resp)
                    else:
                        for i in range(size_of_resp//10):
                            y = i*10
                            pices.append(resp[y:y+10])
                        if extra:
                            pices.append(resp[y+10:])
                        
                    # if len(resp) >20:
                    #     resp = resp[:20]
                    text_msg = '''Больше сведений на сайте\n https://jobfinderapp.herokuapp.com \n Результаты поиска, согласно Вашего запроса:\n'''
                    send_message(chat_id, text_msg)
                    for part in pices:
                        message = ''
                        for v in part:
                            message +=  v['title'] + '\n'
                            # message +=  v['description'] + '\n'
                            # message +=  'Company:' + v['company'] + '\n'
                            # message +=  'Date:' + v['timestamp'] + '\n'
                            message +=  v['url'] + '\n'
                            message +=  '-'*5 + '\n\n'
                        send_message(chat_id, message)
                else:
                    text_msg = 'По Вашему запросу ничего не найдено.'
                    send_message(chat_id, text_msg)
            elif len(tmp) >= 20:
                send_message(chat_id, tmp)
            else:
                resp = get_api_response(tmp)
                if resp:
                    message = ''
                    for d in resp:
                         
                        message += '#' + d['slug'] + '\n'
                    if '/cities' == tmp:
                        text_msg = 'Доступные города: \n'
                    else:
                        text_msg = 'Доступные специальности: \n'
                    text_msg += message
                # print(text_msg)
                # send_message(chat_id, text_msg)
                send_message(chat_id, text_msg)
        else:
            send_message(chat_id, text_msg)
        return jsonify(r)
    return '<h1> HI Bot <h1>'

if __name__ == '__main__':
    app.run()
    # main()
