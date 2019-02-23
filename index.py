from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from PIL import Image
from os import rename


class Subject:

    def __init__(self, raw_data: list):
        self.code = raw_data[1]
        self.name = raw_data[2]
        self.type = raw_data[3]
        self.slot = raw_data[4]
        self.present = int(str(raw_data[6]))
        self.total = int(str(raw_data[7]))
        self.percent = raw_data[8]
        self.class_left = self.__calc_skip_class()

    def __str__(self):
        return self.code+" "+self.name + " " + str(self.class_left)

    def __calc_skip_class(self):
        return int((4*self.present - 3*self.total)/3)


def get_captcha(driver,element):
    """
    :param driver: Takes the selenium object
    :return: The captcha as entered by user
    """
    path = 'files/captchas/captcha.png'
    location = element.location
    size = element.size
    driver.save_screenshot(path)
    image = Image.open(path)
    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']
    image = image.crop((left, top, right, bottom))
    # image.show();
    captcha = input("Please enter the captcha code as shown\n")
    image.save('files/captchas/captcha.png', 'png')
    return captcha


STUDENT_URL = "https://academicscc.vit.ac.in/student/stud_login.asp"
ATTENDACE_URL = r'https://academicscc.vit.ac.in/student/attn_report.asp?sem=WS&fmdt=03-Dec-2018&todt=23-Feb-2019'
# todo add function to dwnld the chrome driver
chrome_driver = r'files/chromedriver.exe'
driver = webdriver.Chrome(chrome_driver)
driver.get(STUDENT_URL)

captcha_img = driver.find_element_by_xpath('//*[@id="imgCaptcha"]')
captcha = ""
try:
    captcha = get_captcha(driver, captcha_img).upper()
    rename('files/captchas/captcha.png', 'files/captchas/'+captcha+'.png')
except Exception as e:
    print(e)
data = {
    'regno': '17bec1162',
    'passwd': 'tempPass123@',
    'vrfcd': captcha,
}

regno = driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[2]/td[2]/input')
passwd = driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[3]/td[2]/input')
cap = driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[5]/td/input')

regno.send_keys(data['regno'])
passwd.send_keys(data['passwd'])
cap.send_keys(data['vrfcd'])
driver.find_element_by_xpath("/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[6]/td/input[1]").click()

# todo check whether logged in succesfully
# Logged In succesfully
# todo make a function to generate data and make attendance url

driver.get(ATTENDACE_URL)
soup = BeautifulSoup(driver.page_source, 'lxml')
for tr in soup.find_all('tr', attrs={'onmouseout': "this.bgColor='#E6F2FF'"}):
    raw_data = []
    for td in tr.find_all('td'):
        raw_data.append(td.text)
    temp_sub = Subject(raw_data)
    print(temp_sub)

driver.close()
