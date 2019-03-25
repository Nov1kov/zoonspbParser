# coding utf-8

import logging
import csv
import re

from grab import Grab
from grab.spider import Spider, Task


class ZoonSpider(Spider):
    def prepare(self):
        self.result_file = csv.writer(open('result.txt', 'w'))
        self.reTelnumber = re.compile(r'href="tel:(\+\d+)"')

    def task_generator(self):
        categories = {'Рестораны': 'restaurants',
                      'ночные клубы': 'night_clubs',
                      'Салоны красоты': 'beauty',
                      'Одежда и обувь': 'stores'}
        city_domens = {'Санкт-Петербург': 'spb.',
                       'Москва': ''}
        for cityName, city in city_domens.items():
            for company_line, category in categories.items():
                city2 = ''
                if city == '':
                    city2 = 'msk/'
                url = 'http://' + city + 'zoon.ru/' + city2 + category + '/?action=list&type=service'

                grab = Grab()
                grab.setup(url=url, post=self.get_post(1), method='POST')
                yield Task('category', grab=grab, numberPage=1, cityName=cityName, company_line=company_line)

    def get_post(self, numberPage):
        return {'need[]': 'items',
                'search_query_form': '1',
                'page': str(numberPage)}

    def task_category(self, grab, task):
        logging.info(task.url + ' page = [' + str(task.numberPage) + ']')

        for company in grab.doc.select('//div[@class="js-results-group"]/ul/li/div/div/a'):
            companyName = company.text()
            yield Task('company',
                       url=company.node().attrib['href'],
                       companyName=companyName,
                       cityName=task.cityName,
                       company_line=task.company_line)

        elemsList = grab.doc.select('//span[@class="js-next-page button button40 button-block button-showMore"]')
        if len(elemsList) > 0:
            elem = elemsList[0]
            if elem:
                nextGrab = Grab()
                nextPage = task.numberPage + 1
                nextGrab.setup(url=task.url, post=self.get_post(nextPage), method='POST')
                yield Task('category',
                           grab=nextGrab,
                           numberPage=nextPage,
                           cityName=task.cityName,
                           company_line=task.company_line)

    def task_company(self, grab, task):
        tel_number = ''

        email = ''
        website = ''
        adress = ''

        for elem in grab.doc.select('//div[@class="params-list params-list-default"]/dl/dd'):
            if elem.node().attrib.get('class', '') == 'simple-text invisible-links':
                addressText = elem.text()
                adress = addressText.replace('Адрес: ', '')
                adress = adress.replace(task.cityName + ', ', '')

        websiteList = grab.doc.select('//strong/following-sibling::a')
        if len(websiteList) > 0:
            websiteElem = websiteList[0]
            if websiteElem:
                website = websiteElem.text()

        elemlist = grab.doc.select('//div[@class="service-phones-box"]')
        if len(elemlist) > 0:
            elem = elemlist[0]
            if elem:
                match = self.reTelnumber.search(elem.html())
                if match:
                    tel_number = match.group(1)

        result_list = [task.companyName,
                       task.company_line,
                       tel_number,
                       # email,
                       website,
                       task.cityName,
                       adress,
                       ]
        logging.info('add ' + ", ".join(result_list))
        self.result_file.writerow(result_list)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        datefmt='%H:%M:%S')

    bot = ZoonSpider()  # thread_number=2
    bot.run()
