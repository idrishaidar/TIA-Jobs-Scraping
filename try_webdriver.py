import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

browser = webdriver.Firefox()

browser.get("https://www.techinasia.com/jobs/search?query=data%20analyst&country_name[]=Indonesia")
time.sleep(1)

elem = browser.find_element_by_tag_name("body")

no_of_pagedowns = 50

while no_of_pagedowns:
    elem.send_keys(Keys.PAGE_DOWN)
    time.sleep(0.2)
    no_of_pagedowns-=1

post_elems = browser.find_elements_by_class_name("jsx-1749311545")

for post in post_elems:
    print(post.text)