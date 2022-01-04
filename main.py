import argparse
import phonenumbers
import re, csv, dateparser
from typing import Text
from time import sleep
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome import options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from rich.console import Console
from rich.table import Table

from getpass import getpass


FACEBOOK_AUTH_URL = 'https://www.facebook.com'
chrome_options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications" : 2}
chrome_options.add_experimental_option("prefs",prefs)
driver = webdriver.Chrome(options=chrome_options)
PARSE_RESULT = []
contact_search_list = ['telegram', 't.me', 'телеграм', 'tg', 'тг', 'viber', 'вайбер', 'почта', 'почту', 'email', 'e-mail', '@', 'и-мейл', 'имейл', 'пошту']
console = Console()
class SingleMetavarHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            parts.extend(action.option_strings)
            return ', '.join(parts)

class Parser(object): 
    def init_parser():
        """[summary]
        Инициализируем модуль argparse
        Возвращает:
            [list]: [Список доступных аргументов командной строки]
        """
        parser = argparse.ArgumentParser(description='Process some integers.', usage = 'main.py -g [groups.txt] -k [keys.txt] -pl [UA PL] -f [result.txt]', formatter_class=SingleMetavarHelpFormatter)
        parser.add_argument('-pl', '--phone-location', metavar="", type=str, nargs='*', default='UA',
                    help='Буквенный код страны в формате iso2 (по-умолчанию только UA)')
        parser.add_argument('-g', '--group-list', metavar='', type=str,
                    help='Путь к файлу со списком групп которые нужно спарсить')
        parser.add_argument('-k', '--key-list', metavar='', type=str,
                    help='Путь к файлу со списком ключей поиска')
        parser.add_argument('-f', '--file', metavar='', type=str,
                    help='Имя файла в который вносятся результаты парсинга')
        parser.add_argument('-t', '--table', metavar='', type=bool, nargs='?',
                    help='Выводить результаты парсинга в консоль', default=False, const=True)
        parser.add_argument('-d', '--deep', metavar='', type=bool, nargs='?',
                    help='Расширенный парсинг, искать объявления в которых не указан номер телефона', default=False, const=True)
        parser.add_argument('--scroll', metavar='', type=int, default=5,
                    help='Количество экранов на которое программа опустит экран браузера')
        parser.add_argument('--pause', metavar='', type=float, default=3,
                    help='Количество секунд между скроллом')
        args = parser.parse_args()
        return args

    def check_contacts(text, contact_list):
        for contact in contact_list:
            x = re.search(contact, text)
            if x:
                return True
            else:
                continue

    def check_keys(body, keys):
        """[summary]
        Функция которая с помощью перебора проверяет есть ли заданый элемент списка в строке
        Args:
            body ([str]): [строка]
            keys ([list]): [список]

        Returns:
            [bool]: [Возвращает True если найдено совпадение]
        """
        for key in keys:
            x = re.search(key.lower(), body)
            if x:
                return True
            else:
                continue

    def generate_console_table(table):
        """[summary]
        Функция которая рисует таблицу
        Args:
            table ([bool]): [Если True - отрисовать таблицу в консоли]
        """
        if table:
            console.print("[magenta] Создаю таблицу... [/magenta]")
            table = Table(title="Результаты парсинга", show_lines=True)
            table.add_column("Id", justify="left", style="cyan", no_wrap=True)
            table.add_column("Дата публикации", justify="left", style="cyan", no_wrap=True)
            table.add_column("Текст поста", style="white")
            table.add_column("Автор", justify="left", style="green")
            table.add_column("Номер телефона", justify="left", style="tan", no_wrap=False)
            table.add_column("Ссылка на профиль", justify="left", style="green")
            if PARSE_RESULT:
                for item in PARSE_RESULT:
                    if Parser.check_keys(item[2].lower(), contact_search_list):
                        table.add_row(item[0], item[1], "[dark_orange3]{}[/dark_orange3]".format(item[2]), item[3], item[4], Parser.cleaned_href(item[5]))
                    else:
                        table.add_row(item[0], item[1], item[2], item[3], item[4], Parser.cleaned_href(item[5]))   
            else:
                console.print("[red] Подходящих записей не найдено [/red]")
            console.print(table)
        else:
            return

    def fb_authentication():
        """[summary]
            Функция авторизации на Facebook
        """
        login = input('Login: ')
        try:
            password = getpass()
            console.print("[yellow] Выполняется авторизация... [/yellow]")
            driver.get(FACEBOOK_AUTH_URL)
            sleep(0.3)
            driver.find_element_by_id('email').send_keys(login)
            sleep(0.5)
            driver.find_element_by_id('pass').send_keys(password)
            sleep(2)
            driver.find_element_by_name('login').click()
            sleep(3)
            if driver.find_element_by_id('pass'):
                console.print("[red] Логин или пароль неверный! [/red]")
                Parser.fb_authentication()
        except NoSuchElementException:
            console.print("[green] Авторизация прошла успешно [/green]")

    def get_group_list(group_list_name):
        """[summary]
        Функция которая находит список групп по которым осуществлять парсинг
        Args:
            group_list_name ([str]): [Название файла в котором нужно искать список групп]

        Returns:
            [list]: [Возвращает список строк(одна строка = одна ссылка на группу)]
        """
        groups = []
        try:
            with open(group_list_name, 'r') as file:
                lines = file.read().splitlines() 
            if len(lines) == 0:
                console.print("[yellow] Файл {} пустой [/yellow]".format(group_list_name))
            else:
                for line in lines:
                    group_href = groups.append(line.strip())
                return groups
        except FileNotFoundError:
            return console.print("[red] Файла {} не существует [/red]".format(group_list_name))

    def get_key_list(key_list_name):
        """[summary]
        Функция которая находит список ключей по которым осуществлять парсинг
        Args:
            key_list_name ([str]): [Название файла в котором нужно искать список ключей]

        Returns:
            [list]: [Возвращает список строк(одна строка = один ключ)]
        """
        keys = []
        try:
            with open(key_list_name, 'r') as file:
                lines = file.read().splitlines() 
            if len(lines) == 0:
                console.print("[yellow] Файл {} пустой [/yellow]".format(key_list_name))
            else:
                for line in lines:
                    group_href = keys.append(line.strip())
                return keys
        except FileNotFoundError:
            return console.print("[red] Файла {} не существует [/red]".format(key_list_name))

    def get_html(url, scroll, pause):
        """[summary]
        Функция которая выполняет переход по url, скроллит страницу и получает её код
        Args:
            url ([str]): [Сссылка на одну группу]
            scroll ([int]): [Целочисленное которое равно количеству раз которое браузер должен проскролить страницу]
            pause ([int]): [Целочисленное которое равно задержке между скролами]

        Returns:
            [str]: [Возвращает код страницы]
        """
        console.print("[magenta] Выполняю поиск постов... [/magenta]")
        driver.get(url)
        SCROLL_PAUSE_TIME = scroll
        for item in range(scroll):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(pause)
        return driver.page_source

    def parse_url(html, locations, keys, deep):
        """[summary]
        Функция которая парсит полученный html
        Args:
            html ([type]): [HTML код страницы]
            locations ([list]): [Список стран по которым осуществлять поиск номера телефона]
            keys ([list]): [Список параметров по которым осуществляется поиск]
        """
        i = 0
        soup = BeautifulSoup(html, 'html.parser')
        adverts = soup.select('.du4w35lb.k4urcfbm.l9j0dhe7.sjgh65i0')
        for item in adverts:
            date = item.select('.j1lvzwm4.stjgntxs.ni8dbmo4.q9uorilb.gpro0wi8')
            body = item.select('.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.c1et5uql')
            _id = i   
            author = item.select('.gmql0nx0.l94mrbxd.p1ri9a11.lzcic4wl.aahdfvyu.hzawbc8m strong span')
            if item and body and author and date:
                if not deep:
                    phone_num = Parser.get_phone_number(body[0].text, locations)
                    if phone_num:
                        # id pub_date body author link phonenum
                        link = item.select('.gmql0nx0.l94mrbxd.p1ri9a11.lzcic4wl.aahdfvyu.hzawbc8m  a')
                        tpl = ()
                        tpl_id = str(_id)
                        tpl_date = str(dateparser.parse(date[0].text.replace('=', '').strip(), languages=['ru']) )
                        tpl_body = str(body[0].text)
                        tpl_author = str(author[0].text)
                        tpl_phone = str(phone_num).replace('[]\'', '') 
                        if Parser.check_keys(body[0].text.lower(), keys):
                            if link:
                                tpl_link = link[0].attrs['href']
                                tpl = (tpl_id, tpl_date, tpl_body,tpl_author, tpl_phone, tpl_link)
                                PARSE_RESULT.append(tpl)    
                            else:
                                tpl = (tpl_id, tpl_date, tpl_body,tpl_author, tpl_phone, 'Профиль заблокирован')       
                                PARSE_RESULT.append(tpl)
                else:
                    phone_num = Parser.get_phone_number(body[0].text, locations)
                    if phone_num:
                        link = item.select('.gmql0nx0.l94mrbxd.p1ri9a11.lzcic4wl.aahdfvyu.hzawbc8m  a')
                        tpl = ()
                        tpl_id = str(_id)
                        tpl_date = str(dateparser.parse(date[0].text.replace('=', '').strip(), languages=['ru']) )
                        tpl_body = str(body[0].text)
                        tpl_author = str(author[0].text)
                        tpl_phone = str(phone_num).replace('[]\'', '')
                        if Parser.check_keys(body[0].text.lower(), keys):
                            if link:
                                tpl_link = link[0].attrs['href']
                                tpl = (tpl_id, tpl_date, tpl_body,tpl_author, tpl_phone, tpl_link)
                                PARSE_RESULT.append(tpl)    
                            else:
                                tpl = (tpl_id, tpl_date, tpl_body,tpl_author, tpl_phone, 'Профиль заблокирован')       
                                PARSE_RESULT.append(tpl)
                        else:
                            pass
                    else:
                        link = item.select('.gmql0nx0.l94mrbxd.p1ri9a11.lzcic4wl.aahdfvyu.hzawbc8m  a')
                        tpl = ()
                        tpl_id = str(_id)
                        tpl_date = str(dateparser.parse(date[0].text.replace('=', '').strip(), languages=['ru']) )
                        tpl_body = str(body[0].text)
                        tpl_author = str(author[0].text)
                        tpl_phone = 'Пользователь не оставил номер телефона'
                        if Parser.check_keys(body[0].text.lower(), keys):
                            if link:
                                tpl_link = link[0].attrs['href']
                                tpl = (tpl_id, tpl_date, tpl_body,tpl_author, tpl_phone, tpl_link)
                                PARSE_RESULT.append(tpl)    
                            else:
                                tpl = (tpl_id, tpl_date, tpl_body,tpl_author, tpl_phone, 'Профиль заблокирован')       
                                PARSE_RESULT.append(tpl)
                        else:
                            pass

            i += 1

    def cleaned_href(attribute):
        """[summary]
        Функция которая создает обёртку для ссылки, для её подальшего вывода в консоль
        Args:
            attribute ([str]): [Ссылка]

        Returns:
            [str]: [Возвращает обёртку]
        """
        href = attribute.replace(']', "%5D").replace('[', '%5B')
        link_wrap = "[link={}]Аккаунт_пользователя[/link]!".format(href)
        return link_wrap

    def get_phone_number(body, locations):
        """[summary]
            Функция которая ищет номера телефонов в body которые соответствуют заданой locations
        Args:
            body ([str]): [Текст в котором функция ищет телефоны]
            locations ([list]): [Список стран]

        Returns:
            [type]: [description]
        """
        locations = locations
        phones_arr = []
        for location in locations:
            for match in phonenumbers.PhoneNumberMatcher(body, location):
                phones_arr.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164))
        return phones_arr

    def save_output_file(filename, arr):
        """[summary]
        Функция которая сохраняет результат парсинга в файле
        Args:
            filename ([type]): [название файла]
            arr ([list]): [список]
        """
        with open(filename, 'a', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            for item in arr:
                writer.writerow(item)
				
    def main():
        '''
        Функция которая запускает программу
        '''
        # Получаем список параметров
        args = Parser.init_parser()
        # Авторизируемся на Facebook
        Parser.fb_authentication()

        locations = args.phone_location
        groups = Parser.get_group_list(args.group_list)
        scroll = args.scroll
        pause = args.pause
        deep = args.deep
        keys = Parser.get_key_list(args.key_list)
        output_file = args.file
        with open(output_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(('Id', 'Дата публикации','Текст поста', 'Автор', 'Номер телефона', 'Ссылка на профиль'))
        for url in groups:
            console.print('[bold tan]URL: {} [/bold tan]'.format(url))
            Parser.parse_url(Parser.get_html(url, scroll, pause), locations, keys, deep)
            Parser.generate_console_table(args.table)
            Parser.save_output_file(output_file, PARSE_RESULT)
            PARSE_RESULT.clear()
        driver.quit();
if __name__ == '__main__':
    Parser.main()
