#!/usr/bin/env python3

# todo:
# check if we're still logged in or not

import time

with open("credentials.txt") as f:
    lines = f.read().split("\n")
email = lines[0]
password = lines[1]


login_url = "https://lobby.ogame.gameforge.com/en_GB/hub"
universe = "Quasar"


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login():
    browser = webdriver.Chrome()
    browser.get(login_url)

    # close ad window
    try:
        ad = browser.find_element_by_class_name("openX_int_closeButton")
        ad.find_element_by_css_selector("a").click()
    except: pass
    
    # log in
    logintabs = browser.find_element_by_id("loginRegisterTabs")
    logintab = logintabs.find_element_by_xpath("//span[text()='Log in']")
    logintab.click()
    loginform = logintabs.find_element_by_id("loginForm")
    loginform.find_element_by_name("email").send_keys(email)
    loginform.find_element_by_name("password").send_keys(password)
    for button in loginform.find_elements_by_class_name("button"):
        if button.text == "Log in": button.click()
    
    
    # enter correct server
    time.sleep(3) # sometimes it cant find the button
    browser.find_element_by_xpath("//span[text()='Play']").click()
    for d in browser.find_elements_by_css_selector("div"):
        if d.text == universe: d.click()
    for box in browser.find_elements_by_class_name("rt-tr-group"):
        if universe in box.text:
            box.find_element_by_css_selector("button").click()
    
    
    # switch to the new tab
    browser.close()
    browser.switch_to.window(browser.window_handles[0])

    return browser

def quit(browser):
    """ log out and close browser """
    time.sleep(3)
    browser.find_element_by_xpath("//a[text()='Log out']").click()
    browser.quit()




#https://s169-en.ogame.gameforge.com/game/index.php?page=ingame&component=supplies&cp=33673921
# start of execution

browser = login()

# do whatever you want now
# in this case we are clicking the solar plant upgrade button
time.sleep(3)
browser.find_element_by_xpath("//span[text()='Resources']").click()
for b in browser.find_elements_by_css_selector("button"):
    #"Solar" in b.get_attribute("aria-label"): b.click()
    if "upgrade" in b.get_attribute("class") and "Solar" in b.get_attribute("aria-label"):
        b.click()

quit(browser)
