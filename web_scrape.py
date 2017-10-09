import pymongo
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import defaultdict

def retrieve_key(file_path, api):
    with open(file_path) as f:
        for line in f:
            if line.startswith(api):
                api_key = line.split(':')[1].strip()
        return api_key


def single_query(link, payload):
    response = requests.get(link, params=payload)
    if response.status_code != 200:
        print 'WARNING', response.status_code
    else:
        return response.json()

def run_selenium(base_url, topics):
    driver = webdriver('~/.ssh/chromedriver')
    url_dict = defaultdict(list)
    for topic in topics:
        driver.get(base_url + topic)
        driver.find_element_by_css_selector('button.button.load-more-button').click()
        urls = driver.find_elements_by_class_name('story-link')
        for url in urls:
            url_dict[topic].append(str(url.get_attribute('href')))
    return url_dict


def scrape(url_dictionary):
    pass

if __name__ == '__main__':
    # path = '/Users/npng/.ssh/api_keys.txt'
    # api_wanted = "nyt"
    # api_key = retrieve_key(file_path = path, api = api_wanted)
    # link = 'http://api.nytimes.com/svc/search/v2/articlesearch.json'
    # payload = {'api-key': api_key}
    # html_str = single_query(link, payload)

    topics = ['politics', 'business', 'world', 'us', 'science', 'health']
    base_url = 'https://www.nytimes.com/section/'
    url_dict = run_selenium(base_url, topics)



    # req = requests.get('https://www.nytimes.com/section/politics?action=click&pgtype=Homepage&region=TopBar&module=HPMiniNav&contentCollection=Politics&WT.nav=page')
    # soup = BeautifulSoup(req.text, 'html.parser')
    #
    # filter_soup = soup.find_all('a', class_='story-link')
    # for row in filter_soup:
    #     print row['href']
