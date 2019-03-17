import requests
import sys
from peewee import *
from string import ascii_lowercase
from itertools import product
import datetime
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
import signal


sqlite_db = SqliteDatabase('allo_search_tips.db')


class BaseModel(Model):
    class Meta:
        database = sqlite_db


class Requests(BaseModel):
    set = IntegerField(default=0)
    timestamp = DateTimeField(default=datetime.datetime.utcnow)
    request_string = CharField()
    answer_raw = CharField()
    answer_query = CharField()
    answer_categories = CharField()
    answer_products = CharField()


if not sqlite_db.table_exists('requests'):
    sqlite_db.create_tables([Requests])


def request_data(request_string):
    headers = {
        'Origin': 'https://allo.ua',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 '
                      'Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Referer': 'https://allo.ua/',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }
    params = (
        ('currentTheme', 'main'),
    )

    data = {
        'q': request_string
    }

    response = requests.post('https://allo.ua/ua/catalogsearch/ajax/suggest/',
                             headers=headers, params=params, data=data)

    if response.status_code == 200:
        return response
    else:
        raise Exception


def print_stats(request_set, request_string, request_itter):
    global total_requests
    global start_time
    request_time = datetime.datetime.now()
    print('OK! ', request_set, ' ', request_string, ' ',
          'Progress: ', request_itter, '/', total_requests, ' ',
          'Time: ', request_time - start_time, ' ',
          'Median time: ', (request_time - start_time) / request_itter, ' ',
          'Approx total time: ', ((request_time - start_time) / request_itter) * total_requests)


def do_request(request_set, request_string, request_itter):
    try:
        request_string = request_string
        request_answer = request_data(request_string)
        request_answer_json = request_answer.json()

        new_answer = Requests().create(
            set=request_set,
            request_string=request_string,
            answer_raw=request_answer.text,
            answer_query=request_answer_json['query'] if 'query' in request_answer_json else '',
            answer_categories=request_answer_json['categories'] if 'categories' in request_answer_json else '',
            answer_products=request_answer_json['products'] if 'products' in request_answer_json else ''
        )
        new_answer.save()
        print_stats(request_set, request_string, request_itter)

    except Exception as e:
        print('FAIL!', e)


def request_new_set(threadPool=20):
    reactor.suggestThreadPoolSize(threadPool)
    global start_time
    start_time = datetime.datetime.now()
    try:
        last_request = Requests.select().order_by(Requests.id.desc()).get()
        new_request_set = last_request.set + 1
    except:
        new_request_set = 1
    request_ittr = 0
    for x in range(1, 4):
        for combo in product(ascii_lowercase, repeat=x):
            request_ittr += 1
            deferToThread(do_request, new_request_set, ''.join(combo), request_ittr)
    global total_requests
    total_requests = request_ittr
    reactor.run()
    reactor.stop()


def request_continue_set(threadPool=20):
    reactor.suggestThreadPoolSize(threadPool)
    global start_time
    start_time = datetime.datetime.now()
    try:
        last_request = Requests.select().order_by(Requests.id.desc()).get()
        new_request_set = last_request.set
        request_list = Requests.select(Requests.request_string).where(Requests.set == new_request_set)
        finished_strings_list = []
        for request in request_list:
            finished_strings_list.append(request.request_string)
    except:
        raise Exception
    request_ittr = 0
    for x in range(1, 4):
        for combo in product(ascii_lowercase, repeat=x):
            request_ittr += 1
            if ''.join(combo) not in finished_strings_list:
                deferToThread(do_request, new_request_set, ''.join(combo), request_ittr)
    global total_requests
    total_requests = request_ittr
    reactor.run()
    reactor.stop()


def ctrl_c_handler(signum, *args):
    reactor.removeAll()
    reactor.iterate()
    reactor.stop()
    return


signal.signal(signal.SIGINT, ctrl_c_handler)

total_requests = 0
request_ittr = 0
# request_new_set(50)
# request_continue_set(50)

def main(*args):
    args = args[0]
    if args[1] and isinstance(args[1], str) and (args[1]=='request_continue_set' or args[1]=='request_new_set'):
        function_name = args[1]
    else:
        print('First arg must be "request_new_set" or "request_continue_set" function name')
        return
    if args[2] and isinstance(int(args[2]), int):
        function_param = int(args[2])
    else:
        print('You can additionaly input number of threads for thread pool as second arg, default 10')
        function_param = 10

    def function_call(function_name, function_param):
        function_array = {
            'request_continue_set': request_continue_set,
            'request_new_set': request_new_set
        }
        function_array[function_name](function_param)

    function_call(function_name, function_param)


if __name__ == "__main__":
    main(sys.argv)
