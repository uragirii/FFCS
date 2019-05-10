import time
import datetime
import sys
import os
import zipfile
from urllib.request import urlretrieve
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import NoAlertPresentException
    from bs4 import BeautifulSoup
    import lxml
    from PIL import Image
    import cv2
    import numpy as np
except ImportError:
    import pip
    try:
        print("Installing Requirements for program.")
        pip.main(['install', 'selenium'])
        pip.main(['install', 'beautifulsoup4'])
        pip.main(['install', 'lxml'])
        pip.main(['install', 'Pillow'])
        pip.main(['install','numpy'])
        pip.main(['install', 'opencv-python'])
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        from bs4 import BeautifulSoup
        from PIL import Image
    except SystemExit as e:
        print("Couldn't install the requirements. Please install selenium and beautifulsoup4 modules manually.")


class Subject:

    def __init__(self, raw_data: list):
        self.code = raw_data[1]
        self.name = raw_data[2]
        self.type = raw_data[3]
        self.slot = raw_data[4]
        self.present = int(str(raw_data[6]))
        self.total = int(str(raw_data[7]))
        self.percent = int(raw_data[8])
        self.debarred = ""
        self.class_need = 0
        if self.percent < 75:
            self.debarred = "DEBARRED RISK"
            self.class_need = self._calc_need_class()
        self.class_left = self._calc_skip_class()

    def show_subject_details(self):
        print("\t---")
        print(self.code, self.name, self.debarred)
        print("Slot", self.slot)
        print("Attended", self.present, "out of", self.total, "(" + str(self.percent) + "%)")
        if self.debarred == "":
            print("Classes you can skip :", self.class_left)
        else:
            print("Classes you need to attend :", self.class_need)

    def __str__(self):
        return self.code

    def _calc_skip_class(self):
        class_skip = int((4 * self.present - 3 * self.total) / 3)
        if 'L' in self.slot:
            class_skip = int(class_skip/2)
        return class_skip

    def _calc_need_class(self):
        return 3 * self.total - 4 * self.present

# path = 'files/unlabelled/'
key_path = 'files/keys/'
# list_of_captcha = os.listdir(path)
list_of_keys = os.listdir(key_path)

def get_random_captcha(img):
    # if img == '':
    #     img = list_of_captcha[randint(0,len(list_of_captcha))]
    #     img = path + img
    image = Image.open(img).convert("L")
    pixel_matrix = np.array(image)
    for col in range(pixel_matrix.shape[1]-1):
        for row in range(pixel_matrix.shape[0]-1):
            if pixel_matrix[row,col] == 250:
                pixel_matrix[row,col] = 0
            if pixel_matrix[row, col] == 86:
                pixel_matrix[row, col] = 255
    changed_image = Image.fromarray(pixel_matrix)
    changed_image.save("test.png")

def remove_noise():
    img = cv2.imread("test.png",0)
    # plt.imshow(img)
    # plt.show()
    kernel_mor = np.ones((2,2),np.uint8)
    kernel_ero = np.ones((1,1), np.uint8)
    morph = cv2.morphologyEx(img,cv2.MORPH_OPEN,kernel_mor)
    ero = cv2.erode(morph,kernel_ero, iterations =1)
    # I'm not showing the morphed image and also not storing that image
    # plt.imshow(ero)
    # plt.show()
    cv2.imwrite("erosion.png", ero)

def detect_letters():
    max_detail = []
    img = cv2.imread('erosion.png', 0)
    for key_file in list_of_keys:
        template = cv2.imread(key_path + key_file, 0)
        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        max_detail.append((key_file, max_val, max_loc))
    # Now sort the files according to max_val and find the top 6
    # TODO: solve for multiple occurances
    raw_letters =  sorted(sorted(max_detail, key=lambda x : x[1], reverse = True)[0:6], key=lambda x:x[2][0])
    captcha_val = ''
    for letter in raw_letters:
        captcha_val = captcha_val + letter[0][0].upper()
    return captcha_val

def get_captcha(driver,element):
    """
    :param driver: Takes the selenium object
    :return: The captcha as entered by user
    """
    path = 'files/captchas/captcha.png'
    if not os.path.exists('files/captchas'):
        os.mkdir('files/captchas')
    location = element.location
    size = element.size
    driver.save_screenshot(path)
    image = Image.open(path)
    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']
    image = image.crop((left, top, right, bottom))
    image.save(path)
    # Now call function
    get_random_captcha(path)
    remove_noise()


    # captcha = input("Please enter the captcha code as shown.(Not Case Sensitive)\nIf there is error while showing "
    #                 "captcha, go to files/captchas folder and open captcha.png, and then enter the code\n")
    # image.save('files/captchas/captcha.png', 'png')
    captcha = detect_letters()
    return captcha


def reporthook(blocknum, blocksize, totalsize):
    """
    function copied from https://stackoverflow.com/questions/13881092/download-progressbar-for-python-3
    """
    global start_time
    if blocknum==0:
        start_time = time.time()
        return
    if totalsize > 0:
        duration = time.time() - start_time
        readsofar = blocknum * blocksize
        if duration == 0:
            duration+=0.001
        speed = int(readsofar / (1024 * duration))
        percent = readsofar * 1e2 / totalsize
        s = '\rPercentage : %5.1f%% (%5.2f MB out of %5.2f MB, Download Speed %d KB/s, %d seconds passed )' % (
            percent, readsofar / 1048576, totalsize / 1048576, speed, duration)
        sys.stderr.write(s)
        if readsofar >= totalsize:  # near the end
            sys.stderr.write("\n")
    else:  # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))


def download_file(url, filename, folder):
    print("Downloading file : ", filename)
    urlretrieve(url, os.path.join(folder, filename), reporthook)
    print("Download Complete")
    return True


def create_date():
    num_to_abbr = {1:'Jan',
                   2:'Feb',
                   3:'March',
                   4:'Apr',
                   5:'May',
                   6:'Jun',
                   7:'Jul',
                   8:'Aug',
                   9:'Sep',
                   10:'Oct',
                   11:'Nov',
                   12:'Dec',}

    d = datetime.datetime.now().day
    m = num_to_abbr[datetime.datetime.now().month]
    y = str(datetime.datetime.now().year)
    if d < 10:
        d = "0" + str(d)
    return str(d) + "-" + str(m) + "-" + str(y)


def get_cred():
    reg_num = input("Enter your register number\n")
    password = input("Enter your FFCS password\n")
    return reg_num, password


def login(driver, reg_num, password):
    driver.get(STUDENT_URL)

    captcha_img = driver.find_element_by_xpath('//*[@id="imgCaptcha"]')
    captcha = ""

    try:
        captcha = get_captcha(driver, captcha_img).upper()
        # todo check whether captcha is correct and then rename it.
        # os.rename('files/captchas/captcha.png', 'files/captchas/'+captcha+'.png')
    except Exception as e:
        print(e)

    data = {
        'regno': reg_num,
        'passwd': password,
        'vrfcd': captcha,
    }
    regno = driver.find_element_by_xpath(
        '/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[2]/td[2]'
        '/input')
    passwd = driver.find_element_by_xpath(
        '/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[3]/td[2]'
        '/input')
    cap = driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[5]/td/'
                                       'input')

    regno.send_keys(data['regno'])
    passwd.send_keys(data['passwd'])
    cap.send_keys(data['vrfcd'])
    driver.find_element_by_xpath("/html/body/table[3]/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[6]/td/"
                                 "input[1]").click()
    return captcha





reg_num, password = get_cred()
STUDENT_URL = "https://academicscc.vit.ac.in/student/stud_login.asp"
ATTENDACE_URL = r'https://academicscc.vit.ac.in/student/attn_report.asp?sem=WS&fmdt=03-Dec-2018&todt='+create_date()


# -------------------------------INITIALISE CHROME DRIVER--------------------------------
options = Options()
options.add_argument('log-level=3')
options.headless = True
chrome_driver = r'files/chromedriver.exe'

if not os.path.exists(chrome_driver):   # Checking and downloading chrome driver
    print("Chrome driver does not exist. Downloading it and saving in {files} folder")
    # TODO Download chrome driver for platform specific
    # check using sys.platform, win32, linux, darwin
    os.mkdir('files')
    download_file("https://chromedriver.storage.googleapis.com/2.44/chromedriver_win32.zip", "chromedriver.zip",
                  "files")
    print("Extracting components")
    with zipfile.ZipFile(os.path.join("files", "chromedriver.zip"), "r") as zip_ref:
        zip_ref.extractall("./files")
    print("Complete.")


driver = webdriver.Chrome(chrome_driver, options = options)
flag = True

while flag:
    captc = login(driver, reg_num, password)

    try:
        alert = driver.switch_to.alert
        alert_text =alert.text
        # Check for illegal credentials
        if 'Password' in alert_text:
            print("You have entered wrong Registration Number or Password. Please Enter again")
            reg_num, password = get_cred()
            alert.accept()
        # Check for capctha
        if 'Verification' in alert_text:
            print("Generated Wrong Value of Captcha. Trying again")
            alert.accept()
    except NoAlertPresentException as e:
        os.rename('files/captchas/captcha.png', "files/captchas/"+captc+".png")
        flag = False

# todo check whether logged in succesfully
# Logged In successfully
print('\nGetting Attendance Details.Please wait')
driver.get(ATTENDACE_URL)
soup = BeautifulSoup(driver.page_source, 'lxml')
all_subjects = []
for tr in soup.find_all('tr', attrs={'onmouseout': "this.bgColor='#E6F2FF'"}):
    raw_data = []
    for td in tr.find_all('td'):
        raw_data.append(td.text)
    temp_sub = Subject(raw_data)
    temp_sub.show_subject_details()
    all_subjects.append(temp_sub)
# print("Got details of all the subjects from date 3-Dec-2018 to", create_date(), "\n")
print("-----------------------\n")
print("Found error in code? Want to suggest something? Email me at : mldata.apoorv@gmail.com\n")
print("Want to know how I calculate this stuff? Check calc file on github.com/uragirii/ffcs")
print("This script doesn't check whether future classes will be held or not.")
print("-----------------------")


driver.close()
