from selenium import webdriver
from time import sleep, mktime, strptime
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import datetime
from configparser import ConfigParser
import os
import json





''' 參數設定 '''
cfg = ConfigParser()
cfg.read('./config.ini', encoding='utf-8')

st_id        = cfg['ID']['account']                         # 帳號
st_pwd       = cfg['ID']['password']                        # 密碼

select_class = cfg['class'].getint('select_class')          # 資結==1 計概==2 英文==3(按照網頁上順序)
snap_up      = cfg['class'].getboolean('snap_up')           # True：忽略欲上課日期，搶七天後的課 False：搶欲上課日期的課
select_date  = cfg['class']['select_date']                  # 欲上課日期
select_branch= cfg['class']['select_branch']                # 嘉義場==WA
session_time = json.loads(cfg.get('class', 'session_time')) # 場次(TKB規定最多3個)

dev          = cfg['options'].getboolean('dev')             # 是否在開發階段(是否送出選課)
EnterPoint   = cfg['options']['EnterPoint']                 # 選課網址

'''
* 場次：
* 1 09:30~12:50(200分鐘, 3:20)
* 2 13:00~16:20(200分鐘, 3:20)
* 3 16:30~18:10(100分鐘, 1:40)
* 4 18:20~20:00(100分鐘, 1:40)
'''

#修改select_date
if snap_up == True:
    today = datetime.date.today()
    if datetime.datetime.now().time() < datetime.datetime.strptime("12:00:00", "%H:%M:%S").time():
        select_date = str(today + datetime.timedelta(days = 6))
    else:
        select_date = str(today + datetime.timedelta(days = 7))

#開啟瀏覽器
options = webdriver.ChromeOptions() 
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(options=options, executable_path='./chromedriver.exe')

''' 開啟登入網頁 '''
def open_chrome(timeout = 900):
    try:
        driver.set_page_load_timeout(timeout)
        driver.set_script_timeout(timeout)      #https://blog.csdn.net/ginynu/article/details/63697559
        driver.get(EnterPoint)                  #https://stackoverflow.com/questions/36026676/python-selenium-timeout-exception-catch
    except TimeoutException as ex:
        print("Exception has been thrown. " + str(ex))
        driver.close()

''' 0：當週上課  1,2：搶課  -1：輸入錯誤 '''
def rush():
    #今天日期
    today = datetime.date.today()
    #上課日期
    other_day = datetime.datetime.strptime(select_date, "%Y-%m-%d").date()
    #相差幾天
    result = (other_day - today).days

    if result==7:
        print("*****搶課模式*****")
        print ("今天是 " + str(today))
        print("等待00:00開始搶課")
        return 1
    elif result==6 and (datetime.datetime.now().time() < datetime.datetime.strptime("12:00:00", "%H:%M:%S").time()) and (datetime.datetime.now().time() > datetime.datetime.strptime("00:10:00", "%H:%M:%S").time()):
        print("*****搶課模式*****")
        print ("今天是 " + str(today))
        print("等待12:00開始搶課")
        return 2
    elif result < 7 and result >= 0:
        print ("不須搶課，當週上課" + str(result))
        return 0
    else:
        print("日期輸入錯誤")
        return -1

''' 登入 '''
def login():
    username = driver.find_element_by_id("id")  #找帳號框
    password = driver.find_element_by_id("pwd") #找密碼框
    username.send_keys(st_id)                   #填入帳號
    password.send_keys(st_pwd)                  #填入密碼
    driver.find_elements_by_xpath("//div[@class='login_btn']/a")[0].click() #按下確認
    #reference : https://stackoverflow.com/questions/33466853/switch-to-alert-text-not-working
    
    try:
        element = WebDriverWait(driver, 900).until(
           EC.alert_is_present()
        )
    except TimeoutException as ex:
        print("登入失敗！")
        print("Exception has been thrown. " + str(ex))
        driver.close()

    driver.switch_to.alert.accept()             #彈出視窗 按下確認

''' 檢查日期是否出現 '''
def date_exist():
    #先選課才能看日期
    class_selector = Select(driver.find_element_by_id("class_selector"))
    class_selector.select_by_index(select_class)
    #遍歷日期選項
    for data in driver.find_elements_by_xpath("//select[@id='date_selector']/option"):
        #若找到了想選的日期(代表可以搶課了)
        if data.text.startswith(select_date):
            return True
    return False

''' 檢查(第一波座位已滿)是否消失 '''
def enable_book():
    class_selector = Select(driver.find_element_by_id("class_selector"))
    date_selector = Select(driver.find_element_by_id("date_selector"))
    branch_selector = Select(driver.find_element_by_id("branch_selector"))  

    class_selector.select_by_index(select_class)    #選課程
    date_selector.select_by_value(select_date)      #選日期
    branch_selector.select_by_value(select_branch)  #選地點

    checkbox = driver.find_elements_by_xpath("//input[@name='session_time' and @value='noSeat']")
    if len(checkbox) == 0:
        return True
    else:
        return False

''' 選場次時間 '''
def select_session():
    for i in session_time:
        checkbox = driver.find_elements_by_xpath("//input[@name='session_time' and @value='" + i + "']")
        if len(checkbox) != 0:
            print("場次 " + i + "： 已選擇！")
            checkbox[0].click()
        else:
            print("場次 " + i + "： 已滿！")
    submit()

''' 送出選課 '''
def submit():
    #送出選課
    driver.find_elements_by_xpath("//div[@class='btn']/a")[0].click()

    #確認選課(目前是取消選課)
    try:
        element = WebDriverWait(driver, 900).until(
           EC.alert_is_present()
        )
    except TimeoutException as ex:
        print("選課失敗！")
        print("Exception has been thrown. " + str(ex))
        driver.close()
    else:
        alert_accept() #確定預約第1、2場次?

    again = False
    while True:
        try:
            element = WebDriverWait(driver, 30).until(
                EC.alert_is_present()
            )

            #tmp = 0
            #while not is_alert_present():
            #    sleep(0.1)
            #    tmp+=0.1
            #    if tmp >= 10:
            #        break
            #element = WebDriverWait(driver, 10).until(
            #    is_alert_present()
            #)
        except TimeoutException as ex:
            print("選課結束！")
            print("Timeout!Exception has been thrown. " + str(ex))
            break
        else:
            alert_txt = driver.switch_to.alert.text
            print(alert_txt)
            if alert_txt.startswith("本次進場課程預約，無相同座位"):
                print("確認不同座位")
                driver.switch_to.alert.accept()
            elif alert_txt.startswith("預約失敗"):
                driver.switch_to.alert.dismiss()
                run()
                return -1
            elif alert_txt.startswith("網路發生異常,請重新整理") or alert_txt.startswith("該場次座位已滿，請重新預約，謝謝") or alert_txt.startswith(" 網路發生異常,請重新整理"):
                again = True
                break
            elif alert_txt.startswith("預約成功"):
                print("預約成功")
                break
    if again == True:
        driver.switch_to.alert.accept()
        driver.refresh()
        run()

''' 執行完整選課 '''
def run(time = 'null'):
    try:
        element = WebDriverWait(driver, 900).until(
            EC.visibility_of_element_located((By.ID,'class_selector'))
        )
    except TimeoutException as ex:
        print("未找到元素")
        print("Exception has been thrown. " + str(ex))
    else:
        #reference : https://huilansame.github.io/huilansame.github.io/archivers/drop-down-select
        class_selector = Select(driver.find_element_by_id("class_selector"))
        date_selector = Select(driver.find_element_by_id("date_selector"))
        branch_selector = Select(driver.find_element_by_id("branch_selector"))  

    class_selector.select_by_index(select_class)    #選課程
    if time == 'night':
        change_value()
    date_selector.select_by_value(select_date)      #選日期
    branch_selector.select_by_value(select_branch)  #選地點
    if time == 'noon':
        change_value_session()
    select_session()             #選場次時間

''' 等待特定時間到 '''
def act(x):
    return x+10

def wait_start(runTime, action, interval=1):
    startTime = datetime.time(*(map(int, runTime.split(':'))))
    while startTime > datetime.datetime.today().time(): # you can add here any additional variable to break loop if necessary
        sleep(interval)# you can change 1 sec interval to any other
    return action

''' 是否有alert出現 '''
def is_alert_present():
    try:
        driver.switch_to.alert
    except NoAlertPresentException:
        print("錯誤：沒有alert")
        return False
    return True

''' 判斷開發模式(alert取消)與上線模式(alert確認) '''
def alert_accept():
    if dev == True:
        driver.switch_to.alert.dismiss()
    elif dev == False:
        driver.switch_to.alert.accept()

#沒用到
def update_time(dateString):
    dateFormatter = "%H:%M:%S:%f"
    delay = getserverdelay()
    timeprint("Delay為:{:.5f}s.".format(delay))
    dt = datetime.datetime.strptime(dateString, dateFormatter) #dateString(str)轉datetime
    dt -= datetime.timedelta(seconds = delay)                  #datetime做修正
    dt_str = dt.strftime(dateFormatter)                        #night_dt轉string
    print("觸發時間修正為："+dt_str)
    return dt_str

def night_stamp():
    targetdate = datetime.datetime.utcnow() + datetime.timedelta(days=7, hours=8)
    sleepstamp = (targetdate.replace(hour=0, minute=0, second=0, microsecond=0)
                - datetime.timedelta(days=6)).timestamp()

    delay = getserverdelay()
    timeprint("Delay為:{:.5f}s.".format(delay))
    sleepstamp -= delay
    sleepstr = datetime.datetime.fromtimestamp(sleepstamp).strftime('%Y-%m-%d %H:%M:%S.%f')
    timeprint("觸發時間修正為：{:s} UTC+8.".format(sleepstr))
    return sleepstamp

def day_stamp():
    targetdate = datetime.datetime.utcnow() + datetime.timedelta(days=6, hours=8)
    sleepstamp = (targetdate.replace(hour=12, minute=0, second=0, microsecond=0)
                - datetime.timedelta(days=6)).timestamp()

    delay = getserverdelay()
    timeprint("Delay為:{:.5f}s.".format(delay))
    sleepstamp -= delay
    sleepstr = datetime.datetime.fromtimestamp(sleepstamp).strftime('%Y-%m-%d %H:%M:%S.%f')
    timeprint("觸發時間修正為：{:s} UTC+8.".format(sleepstr))
    return sleepstamp

''' 選課主程式 '''
def main():  
    open_chrome()
    print("------------------------網頁改value模式------------------------")
    print('''
  _____ _                             __      __   _            
 / ____| |                            \ \    / /  | |           
| |    | |__   __ _ _ __   __ _  ___   \ \  / /_ _| |_   _  ___ 
| |    | '_ \ / _` | '_ \ / _` |/ _ \   \ \/ / _` | | | | |/ _ \\
| |____| | | | (_| | | | | (_| |  __/    \  / (_| | | |_| |  __/
 \_____|_| |_|\__,_|_| |_|\__, |\___|     \/ \__,_|_|\__,_|\___|
                           __/ |                                
                          |___/                                 
''')
    print()
    if_rush = rush()#看是不是要搶課
    
    #night_dateString = "00:00:00:00"
    #day_dateString = "12:00:00:00"

    #不須搶課，立即選課
    if if_rush == 0:    
        login()     #登入
        run()       #選課

    #要搶課，等待00:00
    elif if_rush == 1:
        #23:50先登入
        wait_start('23:50:00', lambda: act(100))
        driver.refresh()
        login()

        try:
            element = WebDriverWait(driver, 900).until(
            EC.visibility_of_element_located((By.ID,'class_selector'))
            )
        except TimeoutException as ex:
            print("未找到元素")
            print("Exception has been thrown. " + str(ex))
        else:
            #reference : https://huilansame.github.io/huilansame.github.io/archivers/drop-down-select
            class_selector = Select(driver.find_element_by_id("class_selector"))
            date_selector = Select(driver.find_element_by_id("date_selector"))
            branch_selector = Select(driver.find_element_by_id("branch_selector")) 
        
        class_selector.select_by_index(select_class)    #選課程
        change_value()
        date_selector.select_by_value(select_date)      #選日期
        branch_selector.select_by_value(select_branch)  #選地點

        #修正觸發時間
        #night_dateString = update_time(night_dateString)
        #開始等待
        sleepstamp = night_stamp()
        while True:  # sleep until time up
            stampnow = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).timestamp()
            if (sleepstamp - stampnow) <= 0:
                break
            else:
                sleep(0.1)
        select_session()             #選場次時間
        
    #要搶課，等待12:00
    elif if_rush == 2:  
        wait_start('11:50', lambda: act(100)) 
        driver.refresh()
        login()                         #登入

        sleepstamp = day_stamp()
        while True:  # sleep until time up
            stampnow = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).timestamp()
            if (sleepstamp - stampnow) <= 0:
                break
            else:
                sleep(0.1)


        #wait_start('12:00', lambda: act(100),0.01)
        #driver.refresh()
        #while not enable_book():
        #    driver.refresh()
        run('noon')


    #保留頁面10分鐘
    sleep(600)
    driver.close()

''' 2 sever慢兩秒 -2 快兩秒'''
def getserverdelay():
    try:
        nowstamp = datetime.datetime.utcnow().timestamp()
        serverdate = requests.get('http://bookseat.tkblearning.com.tw/book-seat/student/bookSeat/index').headers['Date']
        serverstamp = mktime(strptime(serverdate, "%a, %d %b %Y %H:%M:%S %Z"))
        return serverstamp-nowstamp
    except:
        return 0

def timeprint(text):
    print("({:s}) {:s}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text), flush=True)


#將最後一個選項改為select_date
def change_value():
    element = driver.find_elements_by_xpath("//select[@id='date_selector']/option")
    element_attribute_value = element[7].get_attribute('value')
    #print(element_attribute_value) 
    driver.execute_script("arguments[0].setAttribute('value','"+select_date+"')", element[7])
    #element_attribute_value = element[7].get_attribute('value')
    #print(element_attribute_value)

#場次時間更改與可以打勾
def change_value_session():
    element = driver.find_elements_by_xpath("//div[@id='session_time_div']/input")
    #element_attribute_value = element[0].get_attribute('value')
    #print(element_attribute_value) 
    driver.execute_script("arguments[0].setAttribute('value','1')", element[0])
    driver.execute_script("arguments[0].setAttribute('value','2')", element[1])
    driver.execute_script("arguments[0].setAttribute('value','3')", element[2])
    driver.execute_script("arguments[0].setAttribute('value','4')", element[3])
    driver.execute_script("arguments[0].disabled=false", element[0])
    driver.execute_script("arguments[0].disabled=false", element[1])
    driver.execute_script("arguments[0].disabled=false", element[2])
    driver.execute_script("arguments[0].disabled=false", element[3])
    #element_attribute_value = element[7].get_attribute('value')
    #print(element_attribute_value)

if __name__ == '__main__':
    main()
