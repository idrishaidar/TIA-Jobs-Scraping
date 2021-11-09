from bs4 import BeautifulSoup
from pandas.core.algorithms import mode
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import pandas as pd
import csv
import time

# get html text from the search result page

# https://stackoverflow.com/questions/63388521/response-code-418-when-trying-to-web-scrape-the-api
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0'
}

# prevent selenium to automatically opens a browser
# https://stackoverflow.com/questions/5370762/how-to-hide-firefox-window-selenium-webdriver
opts = webdriver.FirefoxOptions()
# opts.headless = True

# initialize selenium firefox webdriver
driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver', options=opts)
driver.get("https://www.techinasia.com/jobs/search?query=data%20analyst&country_name[]=Indonesia")

# automate scroll until the page bottom
# https://stackoverflow.com/questions/21006940/how-to-load-all-entries-in-an-infinite-scroll-at-once-to-parse-the-html-in-pytho
time.sleep(1)

body_element = driver.find_element_by_tag_name('body')

no_of_pagedowns = 50

while no_of_pagedowns > 0:
    body_element.send_keys(Keys.PAGE_DOWN)
    time.sleep(0.2)
    no_of_pagedowns -= 1

# retrieve the html text
html_text = driver.page_source

# initialize soup object
soup = BeautifulSoup(html_text, 'lxml')

# to store the job posts
col_names = [
    'URL', 'Title', 'Company', 'Industry', 'Size', 'Posted at', 
    'Location', 'Job Type', 'Experience Required',
    'Responsibilities', 'Requirements', 'Skills Required', 'Raw Details'
    ]
df_job_posts = pd.DataFrame(columns=col_names)

# get job posts
job_posts = soup.find_all('article', {'data-cy': 'job-result'})

# initialize/read csv file
csv_file = open('jobs.csv', mode='w')
csv_writer = csv.DictWriter(csv_file, fieldnames=col_names)
csv_writer.writeheader()

# for each job post
for job_post in job_posts:
    # get the job post detail page URL
    job_post_element = job_post.find('a', {'data-cy': 'job-title'})
    job_post_url = job_post_element['href']
    job_title = job_post_element.text

    # get html text from the job post detail page
    # sometimes the job header info can't be found
    # retry until the job header is retrieved
    # TODO: assess complexity
    try_request = True
    while try_request:
        current_post_url = 'https://www.techinasia.com' + job_post_url
        driver.get(current_post_url)
        time.sleep(1)
        current_post_html_text = driver.page_source
        current_post_soup = BeautifulSoup(current_post_html_text, 'lxml')

        # get current job header info
        current_job_header = current_post_soup.find('div', {'class': 'header-content'})
        if current_job_header == None:
            continue

        company_name = current_job_header.find('a').text
        company_name_url = current_job_header.find('a')['href']
        company_location = current_job_header.find_all('div')[1].text
        post_created_date = current_job_header.find('span', {'class': 'dates__created'})

        # get current job meta
        job_post_meta = current_post_soup.find(
            'div', {'class': 'meta'}
            ).find_all('div', {'class': 'jsx-3446601365'})
        job_type = job_post_meta[1].find('b').text
        experience_required = job_post_meta[2].find('b').text

        # exit the loop if no need to retry
        try_request = False

    # get current job description
    current_job_details = current_post_soup.find('div', {'class': 'jsx-3475296548'})
    current_job_details_raw = current_job_details.find('div', {'class': 'jsx-3475296548'})

    # get responsibilities list
    responsibilities_element = current_job_details.find('strong')
    responsibilities_raw = responsibilities_element.find_next(['ol', 'ul']).find_all('li')
    responsibilities_list = []
    for item in responsibilities_raw:
        responsibilities_list.append(item.text)

    # get requirements list
    requirements_element = responsibilities_element.find_next(['strong', 'p'])
    requirements_raw = requirements_element.find_next(['ol', 'ul']).find_all('li')
    requirements_list = []
    for item in requirements_raw:
        requirements_list.append(item.text)   

    # get required skills
    required_skills_raw = current_post_soup.find(
        'div', {'class': 'jsx-3475296548'}
        ).find_all('span', {'class': 'jsx-3713767817'})
    required_skills_list = []
    for item in required_skills_raw:
        required_skills_list.append(item.text)

    # get about company info
    company_info = current_post_soup.find('dl', {'class': 'jsx-3475296548'}).find_all('dd')
    company_industry = company_info[1].text
    company_size = company_info[2].text

    # append dataframe
    new_row = {
        'URL': current_post_url, 'Title': job_title,
        'Company': company_name, 'Industry': company_industry,
        'Size': company_size, 'Posted at': post_created_date, 
        'Location': company_location, 'Job Type': job_type,
        'Experience Required': experience_required,
        'Responsibilities': responsibilities_list, 
        'Requirements': requirements_list,
        'Skills Required': required_skills_list,
        'Raw Details': current_job_details_raw
    }
    df_job_posts = df_job_posts.append(new_row, ignore_index=True)

    csv_writer.writerow(new_row)
    # print(current_job_details.find('div', {'class': 'jsx-3475296548'}))


csv_file.close()