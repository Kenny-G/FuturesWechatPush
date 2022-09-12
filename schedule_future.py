import os
import string
import time
import schedule
from time import sleep
import datetime
import math
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import hashlib
import base64
import requests

Config_data = {} 
Config_data['url'] = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=803dfd9b-a8c6-400a-94e7-daf2b7b53458"
Config_data['products'] = ["IC", "IF", "IH", "IM"]
Config_data['file_day_size'] = (750, 200)
Config_data['file_week_size'] = (750, 400)


# timestr="2022-09-10", strName = "IC"
def CalcDayData(driver, timestr, strName):
    select = Select(driver.find_element_by_id('selectSec'))
    select.select_by_visible_text(strName)
    driver.find_element_by_class_name('btn-query').click()
    sleep(0.5)
    tbs = driver.find_elements_by_class_name('IF_if_table')

    num = 0
    total_delta = 0
    for tb in tbs:
        num += 1
        tdall = tb.find_elements_by_tag_name('td')
        buy = 0
        sell = 0
        for i in range(1, len(tdall)):
            if tdall[i].text == '中信期货':
                if i % 12 == 8:
                    buy = int(tdall[i+2].text)
                elif i % 12 == 0:
                    sell = int(tdall[i+2].text)

                if buy != 0 and sell != 0:
                    break

        total_delta += (buy - sell)

    return "{} {} 合约净多变化量:  {}\n".format(timestr, strName, total_delta)

def CalcWeekData(driver, timestr, strName):
    select = Select(driver.find_element_by_id('selectSec'))
    select.select_by_visible_text(strName)
    driver.find_element_by_class_name('btn-query').click()
    sleep(0.5)
    tbs = driver.find_elements_by_class_name('IF_if_table')

    num = 0
    total_delta = 0
    for tb in tbs:
        num += 1
        tdall = tb.find_elements_by_tag_name('td')
        buy = 0
        sell = 0
        for i in range(1, len(tdall)):
            if tdall[i].text == '中信期货':
                if i % 12 == 8:
                    buy = int(tdall[i+1].text)
                elif i % 12 == 0:
                    sell = int(tdall[i+1].text)

                if buy != 0 and sell != 0:
                    break

        total_delta += (buy - sell)

    return "{} {} 合约交易量净多:  {}\n".format(timestr, strName, total_delta)

# 保存textstr 到图片 filename 中
def SaveImage(filename, textstr, filesize):
    fontname = "simhei.ttf"
    fontsize = 30   
    
    colorText = "white"
    colorOutline = "white"
    colorBackground = "#121212"

    font = ImageFont.truetype(fontname, fontsize)
    #img = Image.new('RGB', (750, 300), colorBackground)
    img = Image.new('RGB', filesize, colorBackground)
    d = ImageDraw.Draw(img)

    d.multiline_text((10, 10), textstr , fill=colorText, font=font)
    #img.save("./image.png")
    img.save(filename)

def SendImage(url, image):
    tries = 5
    while tries > 0:
        try:
            with open(image, 'rb') as file:  # 转换图片成base64格式
                data = file.read()
                encodestr = base64.b64encode(data)
                base64_data = str(encodestr, 'utf-8')

            with open(image, 'rb') as file:  # 图片的MD5值
                md = hashlib.md5()
                md.update(file.read())
                image_md5 = md.hexdigest()
            # 调用消息生成器
            headers = {"Content-Type": 'text/plain'}
            imdata = {
                "msgtype": "image",
                "image": {
                    "base64": base64_data,
                    "md5": image_md5
                }
            }
            r = requests.post(url=url, json=imdata)
            print(r)
            break
        except Exception as e:
            tries -= 1
            print(e)

def PushData(use_time='', use_friday=False):
    # 周末不推送
    week_day = datetime.datetime.now().weekday() + 1
    if week_day > 5 and len(use_time) == 0:
        return

    isFriday = False
    if week_day == 5 or use_friday:
        isFriday = True

    timestr = datetime.datetime.now().strftime('%Y-%m-%d')
    if len(use_time) > 0:
        timestr = use_time

    filename = "./" + timestr + ".png"
    print(filename)
    tries = 5

    while tries > 0:
        try:
            driver = webdriver.PhantomJS()
            driver.get('http://www.cffex.com.cn/ccpm/')
            driver.find_element_by_id('actualDate').clear()
            driver.find_element_by_id('actualDate').send_keys(timestr)

            print("计算数据中 ... ")
            message_ret = "\n"
            for product in Config_data['products']:
                message_ret += CalcDayData(driver, timestr, product)

            if isFriday:
                message_ret += "\n"
                for product in Config_data['products']:
                    message_ret += CalcWeekData(driver, timestr, product)

            print("处理图片中 ... ")
            if isFriday:
                SaveImage(filename, message_ret, Config_data['file_week_size'])
            else:
                SaveImage(filename, message_ret, Config_data['file_day_size'])
            SendImage(Config_data['url'], filename)
            break
        except Exception as e:
            # 发生异常, 等待1秒重试
            tries -= 1
            print(e)
            sleep(1)

#PushData(False, '2022-08-26')
#PushData('2022-08-26', True)
schedule.every().day.at("17:30").do(PushData)
while True:
    schedule.run_pending()
    time.sleep(1)

