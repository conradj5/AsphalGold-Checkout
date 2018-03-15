import bs4
import json
import time
import logging
import requests
from requests.auth import HTTPProxyAuth
import random
from threading import Thread
from bs4 import element

sizes = {'36': '118', '36 2/3': '144', '37 1/3': '143', '38': '126', '38 2/3': '142', '39 1/3': '141', '40': '42', '40 2/3': '140', '41 1/3': '139', '42': '125', '42 2/3': '138', '43 1/3': '137', '44': '111', '44 2/3': '136', '45 1/3': '135', '46': '110', '46 2/3': '134', '47 1/3': '133', '48': '150', '48 2/3': '132', 'COMING SOON': '273', }


def get_time():
    return int(round(time.time() * 1000))


class ATCThread(Thread):
    def __init__(self, queue, url, size=None, proxy=''):
        super(ATCThread, self).__init__()
        print('starting atc')
        self.session = requests.session()

        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'})
        if proxy is not '':
            print(proxy)
            parts = proxy.split(':')
            print(parts)
            proxy = '%s:%s' % (parts[0], parts[1])
            print(proxy)
            proxyDict = {'http': proxy, 'https': proxy}
            # self.session.trust_env = False
            test = self.session.get('https://whatismyipaddress.com/', proxies=proxyDict)
            print(test.content.decode())

        self.url = url
        print("url: " + self.url)
        self.queue = queue
        if not size:
            self.size = size

        self.log = logging.getLogger("ATCThread")
        log_format = logging.Formatter("[%(asctime)s.%(msecs)03d] ATCThread: %(message)s", "%H:%M:%S")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        self.log.addHandler(console_handler)
        self.log.setLevel(logging.DEBUG)

        self.log.info("Created")

        self.run_atc()

    def run_atc(self):
        self.log.info('Starting ATC')
        start = get_time()
        # get product page
        item_page = self.session.get(self.url)
        while not item_page and item_page.status_code is not '200':
            self.log.info("Failed to get item page " + item_page.status_code)
            item_page = self.session.get(self.url)

        self.log.info("Retrieved product page - %dms" % (get_time()-start))

        start = get_time()
        strain = bs4.SoupStrainer(id='product_addtocart_form')
        item_parse = bs4.BeautifulSoup(item_page.content, "lxml", parse_only=strain)
        form = item_parse.find('form')
        select = form.find('select')

        self.log.info("Page parsed - %dms" % (get_time() - start))

        start = get_time()
        # find add url
        action = form['action'].replace("checkout/cart", "ajax/index")
        # form payload
        payload = {'qty': '1', 'isAjax': '1'}
        for item in form.find_all('input'):
            payload[item['name']] = item['value']
        opts = form.find(id='options_502').contents

        if hasattr(self, 'size'):
            size_id = sizes[self.size]
            size = self.size
            for item in form.find(id='options_502').contents:
                if type(item) == element.Tag and item['data-simplesku'].split('-', 1)[-1] == self.size:
                    size = item['data-simplesku'].split('-')[-1]
                    size_id = item['id'].split('_')[-1]
                    break
        else:
            rand = random.choice(opts[:-2])
            size = rand['data-simplesku'].split('-', 1)[-1]
            size_id = rand['id'].split('_')[-1]

        payload[select['name']] = size_id
        self.log.info('Selected size %s' % size)
        print("POST request created - {}ms {}".format((get_time() - start), str(payload)))

        # stdin.readline()

        start = get_time()
        start_atc = get_time()
        atc_resp = self.session.post(action, data=payload)
        while atc_resp.status_code != '200' and json.loads(atc_resp.content)['status'] != 'SUCCESS':
            self.log.info('POST atc failed - {} - {}'.format(atc_resp.status_code, json.loads(atc_resp.content)['status']))
            time.sleep(1)
            start = get_time()
            atc_resp = self.session.post(action, data=payload)

        print("Added - %dms" % (get_time() - start_atc))
        self.queue.put(self.session.cookies['frontend'])
        self.log.info('Added cookie to queue')
