import asyncio
import concurrent.futures
import logging
import sys
import os
import json
import re
sys.path.append(os.path.abspath(os.curdir))
from wordstat import WordStatParser

# logging.basicConfig(filename = '/var/log/ws_serv.service.log', level = logging.DEBUG, filemode='a', format = u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# invalid_escape = re.compile(r'\\[0-7]{1,3}')  # up to 3 digits for byte values up to FF
#
# def replace_with_byte(match):
#     return chr(int(match.group(0)[1:], 8))
#
# def repair(brokenjson):
#     return invalid_escape.sub(replace_with_byte, brokenjson)

def socket_rcv(_socket):

    data =[]
    while True:
        d = _socket.read(1024).decode()
        if not d: break
        data.append(d)
    return ''.join(data)

def marker(resp):
    print(resp)
    if resp['quote'] and resp['vskl']:
        return '"!'
    elif resp['quote']:
        return '"'
    elif resp['vskl']:
        return '!'
    return ''

def other_try(_ws_parser, keys_to_collect, marker):
    ws_parser.wordstat(keys_to_collect, marker=marker)
    results = {}
    for x in keys_to_collect:
        cleared_key = ws_parser._clear_key(x)
        if cleared_key in ws_parser.results:
            results[x] = ws_parser.results[cleared_key]
        else:
            results[x] = 'NA'
    return results

@asyncio.coroutine
def handle_request(client_reader, client_writer):
    while True:
        try:
            logging.info('connection from client')
            print(type(client_reader))
            #todo json не дожевывает цука!
            # request_link = yield from asyncio.wait_for(client_reader.read(), timeout=10, loop=serv_loop)#client_reader.read(8000), timeout=20, loop=serv_loop)
            data = bytearray()
            while True:
                chunk = yield from client_reader.read(1024)
                data += chunk
                if b'\x04' in chunk:
                    break
                elif chunk == b'':
                    break
            data = data.replace(b'\x04',b'')


            #request_link = yield from client_reader.read(-1)

            # print(request_link)
            if data == b'':
                break
            if ws_parser.busy:

                answer = {'status':'Busy'}
            else:
                ws_parser.busy = True
                in_str = data.decode()#request_link.decode()
                resp = json.loads(in_str, strict=False)
                #todo добавить обработку маркера
                #todo добавить проверку на размер шрифта и недопустимые символы для последюущего сопоставления списка
                #todo обработка данных без вордстата
                keys_to_collect = resp['keys']
                results = other_try(ws_parser, keys_to_collect, marker(resp))
                for i in range(3): # 3 попытки сбора
                    if 'NA' in results.values():
                        other_keys = [x for x in results if results[x]=='NA']
                        other_res  = other_try(ws_parser, other_keys, marker(resp))
                        for k in other_res:
                            results[k] = other_res[k]
                    else:
                        break


                # ws_parser.wordstat(keys_to_collect, marker=marker(resp))
                # results = {}
                # for x in keys_to_collect:
                #     if x in ws_parser.results:
                #         results[x] = ws_parser.results[x]
                #     else:
                #         results[x] = 'NA'
                # results = {x:ws_parser.results[x] for x in keys_to_collect if x in ws_parser.results}#

                answer = {}
                for x in keys_to_collect:
                    if x in results:
                        answer[x] = results[x]
                    else:
                        answer[x] = 'NA2'
                # answer = [(x, results[x]) for x in keys_to_collect if x in results]
                ws_parser.busy = False
                answer = {'status':'Done',
                          'keys':answer}
            logging.info('sending answer')
            client_writer.write(json.dumps(answer).encode('utf8'))

        except concurrent.futures.TimeoutError:
            logging.warning('timeout error')
            break
        finally:
            logging.info('connection closed')
            client_writer.close()



#def init(port = 5050):
if __name__ == '__main__':
    port = 5050
    logging.info('create geo-server')

    ws_parser = WordStatParser(path_to_accounts='/home/ws_parser/proxy.txt')
    ws_parser.busy = False

    try:
        serv_loop = asyncio.new_event_loop()#asyncio.get_event_loop()
        asyncio.set_event_loop(serv_loop)
        coro = asyncio.start_server(handle_request, '', port, loop=serv_loop, limit=10000000000)
        server = serv_loop.run_until_complete(coro)
    except Exception as e:
        logging.exception("server dont't created")
        sys.exit(1)
    logging.info('start geo-server')
    try:
        serv_loop.run_forever()
    except Exception:
        logging.exception("server don't started")
    finally:
        logging.info('stop server')
        server.close()
        serv_loop.close()