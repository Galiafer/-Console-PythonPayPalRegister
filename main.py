from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
from config import SMS_KEY, DEFAULT_PASSWORD, DEFAULT_ADDRESS, DEFAULT_CITY, DEFAULT_REGION, DEFAULT_ZIP
from tabula import read_pdf

import time
import pyperclip
import re
import requests
import time
import os
import json
import glob
import random

class PayPal(object):
    # Make some essential settings for selenium
    options = webdriver.FirefoxOptions()
    profile = webdriver.FirefoxProfile()
    # Set user agent
    options.set_preference('general.useragent.override', UserAgent().chrome)
    # Disable web-self.driver mode
    options.set_preference('dom.webdriver.enabled', False)
    # Automatic download files
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk","application/pdf");
    profile.set_preference("browser.download.folderList", 2);
    profile.set_preference("browser.download.manager.showWhenStarting", False);
    profile.set_preference("browser.download.dir", os.getcwd());
    profile.set_preference("plugin.scan.plid.all",False);
    profile.set_preference("plugin.scan.Acrobat","99.0");
    profile.set_preference("pdfjs.disabled",True);
    # Proxy Settings
    r_proxy = random.choice(open("proxy.txt").readlines()).split(':')
    proxy_id = r_proxy[0]
    proxy_port = r_proxy[1]
    options.set_preference('network.proxy.type', 1)
    # options.add_argument("--headless")
    options.set_preference('network.proxy.http', proxy_id)
    options.set_preference('network.proxy.http_port', proxy_port)
    options.set_preference('network.proxy.https', proxy_id)
    options.set_preference('network.proxy.https_port', proxy_port)
    options.set_preference('network.proxy.ssl', proxy_id)
    options.set_preference('network.proxy.ssl_port', proxy_port)

    def __init__(self, driver_path):
        self.driver = webdriver.Firefox(executable_path=driver_path, options=self.options, firefox_profile =self.profile)

    def data_confirm(self):
        print('\n\nПерехожу на страницу следующий этап')
        self.driver.find_element_by_id('/appData/action').click()
        self.driver.set_page_load_timeout(10)
        print('Переход был удачно сделан!\n\n')
    def create_database(self, *data):
        """
        [Create DATABASE for accounts]

        Arguments:
            *data -- [name, surname, middlename, mail, password, inn]
        """

        name, surname, middlename, mail, passport, inn = data
        if not os.path.exists('/home/galiaf/Python/Paypal Register/database.txt'):
            with open('database.txt', 'w') as database:
                database.write(f'{inn}:{passport}:{surname}:{name}:{middlename}:{mail}:{DEFAULT_PASSWORD}\n')
        else:
            with open('database.txt', 'a') as database:
                database.write(f'{inn}:{passport}:{surname}:{name}:{middlename}:{mail}:{DEFAULT_PASSWORD}\n')
    def go_to(self, url:str, name:str):
        """[summary]

        [Go to a certain web-site]

        Arguments:
            url {str} -- [Give url (e.x: https://www.python.org/) ]
            name {str} -- [Give website name (e.x: Python.org)]
        """
        print(f'\n\nПерехожу на сайт: {name}')
        self.driver.get(url)
        self.driver.implicitly_wait(15)

        if url == 'https://service.nalog.ru/inn.do':
            # Click on checkbox
            self.driver.find_element_by_id('unichk_0').click()
            # Click on button 'Продолжить'
            self.driver.find_element_by_id('btnContinue').click()

        print('Переход был удачно сделан!\n\n')
    def get_data_from_pdf(self):
        """
        [Download PDF file and get data from it]
        """
        try:
            pdf_file = glob.glob('*.pdf')[0]
        except IndexError:
            raise print('Не удалось найти файл...')

        print('Читаю PDF файл...')
        data = read_pdf(pdf_file, pages=1, output_format="json")

        print('Получаю данные...')
        surname = data[1]['data'][0][2]['text'].capitalize()
        name = data[1]['data'][1][2]['text'].capitalize()
        middlename = data[1]['data'][2][2]['text'].capitalize()
        bdate = data[1]['data'][9][2]['text']
        passport =  ''.join(re.findall('\d+', data[1]['data'][10][2]['text']))

        os.remove(pdf_file)

        print('Данные получены! \n\n')
        return (surname, name, middlename, bdate, passport)
    def get_mail(self):
        url = "https://temp-mail22.p.rapidapi.com/get"
        querystring = {"domain": "teahog.com"}
        headers = {
            'x-rapidapi-key': "69b97f1229msh6a46ceabb205dacp1972a5jsnec04eec73bcc",
            'x-rapidapi-host': "temp-mail22.p.rapidapi.com"
        }
        response = requests.request(
            "GET", url, headers=headers, params=querystring).json()['items']
        # Get mail name and mail key from api
        mail_name = response['username']
        mail_key = response['key']

        print(f'Имя почты: {mail_name}')
        print(f'Mail key: {mail_key}\n\n')

        return (mail_name, mail_key)
    def get_phone(self):
        url = {
            'getBalance': f'https://sms-activate.ru/stubs/handler_api.php?api_key=${SMS_KEY}&action=getBalance',
            'getNumber': f'https://sms-activate.ru/stubs/handler_api.php?api_key=${SMS_KEY}&action=getNumber&service=$ts&country=$0',
        }
        # GET BALANCE
        balance = requests.get(url['getBalance']).text.split(':')[1]
        print(f'\nВаш баланс: {balance} руб')
        # GET NUMBER
        try:
            print('Получаю номер...')
            number = requests.get(url['getNumber']).text.split(':')
            # GET RESPONSE AND NUMBER DATA
            answer, phone_id, phone_number = number[0], number[1], number[2]
        except IndexError:
            print('Ну удалось получить номер, попробуйте снова...')
            return
        print('Номер получен!')

        if 'ACCESS_NUMBER' in answer:
            print(f'Ваш номер телефона: {phone_number} \nPHONE ID: {phone_id} \n ')
            return (phone_id, phone_number)
        elif 'NO_NUMBERS' in answer:
            print('Нет номеров, попробуйте позже...')
            return
        elif 'NO_BALANCE' in answer:
            print('Пополните баланс...')
            return
    def get_code(self, phone_id: str):
        url = {'getStatus': f'https://sms-activate.ru/stubs/handler_api.php?api_key=${SMS_KEY}&action=getStatus&id=${phone_id}'}

        # REFRESH STATUS CODE
        loop = True
        while loop:
            # GET STATUS CODE
            status_code = requests.get(url['getStatus']).text.split(':')

            if 'STATUS_OK' in status_code[0]:
                print(f'Успешно, код получен!!! \n\nВаш код: {status_code[1]}')
                # EXIT FROM LOOP
                loop = False
            elif 'STATUS_CANCEL' in status_code[0]:
                print('Активация отменена...')
                return
            elif 'STATUS_WAIT_CODE' in status_code[0]:
                print('Ожидаю смс...')
                time.sleep(5)
        return status_code[1] # RETURN AUTHENTIFICATION CODE
    def captcha_check(self):
        try:
            googleCaptcha = self.driver.find_element_by_xpath('//*[@id="captcha-standalone"]')
            if googleCaptcha:
                print('Пожалуйста решите капчу, у вас есть 45 сек\n')
                time.sleep(45)
        except:
            pass
    def finish(self):
        self.driver.close()
        self.driver.quit()

    def search_data(self):
        """
        [Looking for Person`s name,surname,middlename,birthday date,passport number]
        """

        # GET NAME AND SURNAME FROM USER:
        name = str(input('Введите имя (на русском): ')).capitalize()
        surname = str(input('Введите фамилию (на русском): ')).capitalize()

        # REDIRCTING TO https: www.reestr-zalogov.ru:
        self.go_to('https://www.reestr-zalogov.ru/search/index', 'Reestr Zalogov')

        # CLICK ON 'По информации залогодатели':
        print('Перехожу во вкладку "По информации залогодатели"')
        path = '/html/body/div[3]/div[4]/div[2]/div/div[1]/ul/li[2]/a'
        self.driver.find_element_by_xpath(path).click()

        # MANIPULATIN WITH DATA:
        name_input = self.driver.find_element_by_id('privatePerson.firstName')
        surname_input = self.driver.find_element_by_id('privatePerson.lastName')
        # FILLING DATA IN INPUTS:
        print('Заполняю данные...')
        name_input.send_keys(name)
        surname_input.send_keys(surname)
        print('Заполнение прошло успешно! \n\n')
        # SEARCHING FOR DATA:
        print('Ищу данные...')
        self.driver.find_element_by_id('find-btn').click()
        self.driver.implicitly_wait(5)
        try:
            # GET LAST ITEM AND PAGE FROM RESULT:
            last_item = '.table > tbody:nth-child(3) > tr:last-child > td:nth-child(3) > span'
            try:
                # IF THERE IS LAST PAGE -> CLICK:
                last_page = self.driver.find_element_by_id('last-page')
                last_page.click()
                self.driver.implicitly_wait(5)
                self.driver.find_element_by_css_selector(last_item).click()
                time.sleep(2)
            except:
                # ELSE IF THERE IS NO LAST PAGE JUST FIND LAST ITEM FROM LIST:
                self.driver.find_element_by_css_selector(last_item).click()
                time.sleep(2)

            surname, name, middlename, bdate, passport = self.get_data_from_pdf()
            print(f'Полученые данные: {surname, name, middlename, bdate, passport}')
            return (surname, name, middlename, bdate, passport)
        except Exception:
            raise NoSuchElementException('Не удалось найти человека...')

    def search_inn(self, data):
        """

        [Get number of user`s INN]

        Arguments:
            data -- [surname, name, middlename, bdate, passport]

        Returns:
            [INN] -- [Return Person`s INN if success]
        """

        # REDIRCTING TO https: service.nalog.ru:
        self.go_to('https://service.nalog.ru/inn.do', 'Service Nalogov')
        self.driver.set_page_load_timeout(10)

        # GET DATA
        surname, name, middlename, bdate, passport = data
        # GET INPUTS
        inputs = [
            {
                'id': self.driver.find_element_by_id('nam'),
                'text': name
            },
            {
                'id': self.driver.find_element_by_id('fam'),
                'text': surname
            },
            {
                'id': self.driver.find_element_by_id('otch'),
                'text': middlename
            },
            {
                'id': self.driver.find_element_by_id('bdate'),
                'text': bdate
            },
            {
                'id': self.driver.find_element_by_id('docno'),
                'text': passport
            },
        ]
        # FILL DATA
        print('Заполняю данные...')
        for input in inputs:
            pyperclip.copy(input['text'])
            input['id'].send_keys(Keys.CONTROL, 'v')

        # SEND RESPONSE FOR INN
        print('Отправляю запрос на поиск "ИНН"...')
        self.driver.find_element_by_id('btn_send').click()
        time.sleep(1)

        try:
            success = self.driver.find_element_by_class_name('pane-success')
            if success:
                # Get INN
                inn = self.driver.find_element_by_id('resultInn').text
                print('ИНН успешно найден...')
                print('Номер ИНН: {}\n\n'.format(inn))
                return inn
        except:
            print('Не удалось найти ИНН, попробуйте снова...')
            return

    def paypal_registration(self, *data):
        """

        [PayPal registration]

        Arguments:
            *data -- [name, surname, middlename, bdate, passport, inn]
        """
        # REDIRECTING TO www.paypal.com:
        self.go_to('https://www.paypal.com/ru/welcome/signup/', 'PayPal')
        # Expecting captcha
        self.captcha_check()

        # GET PHONE DATA
        print('Получаю номер телефона...\n')
        phone_id, phone_number = self.get_phone()
        phone_field = self.driver.find_element_by_id('paypalAccountData_phone')
        # COPY PHONE NUMBER
        pyperclip.copy(re.split('^[7]', str(phone_number))[1])
        # PASTE PHONE NUMBER
        phone_field.send_keys(pyperclip.paste())

        # GET AUTHENTIFICATION CODE
        self.data_confirm() # CONFIRM DATA AND REDIRECTING TO THE NEXT STAGE
        print('Процесс получения смс, ожидайте...')
        code = self.get_code(phone_id)
        print('Процесс получения смс завершен!\n\n')
        auth_code_field = self.driver.find_element_by_id('text-input-SecurityCodeInput_0')
        # SEND CODE IN THE FIELD
        print('Отправляю код в поле с кодом...')
        auth_code_field.click()
        auth_code_field.clear()
        auth_code_field.send_keys(code)
        print('Код успешно отправлен...\n\n')

        # REGISTRATION - STAGE-1: MAIL AND PASSWORD CONFIRM
        print('Получаю почту...')
        # GET INPUTS
        mail_input = self.driver.find_element_by_id('paypalAccountData_email')
        password_input = self.driver.find_element_by_id('paypalAccountData_password')
        password_confirm_input = self.driver.find_element_by_id('paypalAccountData_confirmPassword')
        # GET MAIL
        mail, *_ = self.get_mail()
        # FILL DATA
        print('Набираю данные в поля...')
        mail_input.send_keys(mail)
        password_input.send_keys(DEFAULT_PASSWORD)
        password_confirm_input.send_keys(DEFAULT_PASSWORD)
        print('Успешно!\n\n')
        # CONFIRM DATA
        self.data_confirm()
        # Expecting captcha
        self.captcha_check()

        # REGISTRATION - STAGE-2: FILL PERSON DATA
        # GET INPUTS
        surname_input = self.driver.find_element_by_id('paypalAccountData_lastName')
        name_input = self.driver.find_element_by_id('paypalAccountData_firstName')
        middlename_input = self.driver.find_element_by_id(
            'paypalAccountData_middleName')
        bdate_input = self.driver.find_element_by_id('paypalAccountData_dob')
        passport_input = self.driver.find_element_by_id('paypalAccountData_passport')
        document_input = self.driver.find_element_by_id('paypalAccountData_idNumType')
        document_serial_number_input = self.driver.find_element_by_id(
            'paypalAccountData_identificationNum')
        street_input = self.driver.find_element_by_id('paypalAccountData_address1')
        city_input = self.driver.find_element_by_id('paypalAccountData_city')
        region_input = self.driver.find_element_by_id('paypalAccountData_state')
        zip_input = self.driver.find_element_by_id('paypalAccountData_zip')
        checkbox_button = self.driver.find_element_by_xpath(
            '/html/body/div[1]/div/div/div/div/div/main/div/div/form/fieldset/div/div[15]/div/div/label/span[1]')
        # GET DATA
        name, surname, middlename, bdate, passport, inn = data
        # FILL DATA
        print('Набираю данные в поля...')
        surname_input.send_keys(surname)
        name_input.send_keys(name)
        middlename_input.send_keys(middlename)
        bdate_input.send_keys(bdate)
        passport_input.send_keys(passport)
        street_input.send_keys(DEFAULT_ADDRESS)
        city_input.send_keys(DEFAULT_CITY)
        region_input.send_keys(DEFAULT_REGION)
        zip_input.send_keys(DEFAULT_ZIP)
        checkbox_button.click()
        # CHOOSE CORRECT DOCUMENT TYPE
        select = Select(document_input)
        select.select_by_value('INN')
        time.sleep(1)
        document_serial_number_input.send_keys(inn)
        print('Упешно!\n\n')
        # CREATE DATABASE
        self.create_database(name, surname, middlename, mail, passport, inn)
        # CONFIRM DATA
        self.data_confirm()
        # EXCPECTING CAPTCHA
        self.captcha_check()

        # Back to paypal.com
        return self.driver.get('https://www.paypal.com')
    def start_registration(self):
        """
        [Main function which start the process of registration]
        """

        # FIRST STEP -> GET NECCESSARY INFO ABOUT PERSON:
        surname, name, middlename, bdate, passport = self.search_data()
        # time.sleep(2)
        # SECOND STEP -> GET PERSON`S INN:
        data = surname, name, middlename, bdate, passport
        inn = self.search_inn(data)
        # time.sleep(10)
        # THIRD STEP -> PAYPAL REGISTRATION:
        self.paypal_registration(name, surname, middlename, bdate, passport, inn)

if __name__ == '__main__':
    pp = PayPal('/home/galiaf/Python/Paypal Register/geckodriver')

    pp.start_registration()
    time.sleep(2)
    pp.finish()