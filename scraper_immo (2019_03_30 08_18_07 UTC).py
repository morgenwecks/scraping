import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # let it wait for some time. patience while loading it all
import time
from selenium.webdriver.common.by import By # search for by param
from selenium.webdriver.support import expected_conditions as EC # what am i looking for, has the page loaded?
from selenium.common.exceptions import TimeoutException # handle timeouts
from selenium.webdriver.firefox.options import Options
import re
from IPython.display import clear_output
from selenium.webdriver.firefox.options import Options
import gc
import os
from datetime import datetime

now = str(datetime.now()).replace(':','_').replace(' ','_').replace('-','_')

options = webdriver.ChromeOptions()
options.add_argument('headless') # newer webdriver versions

cities = ['berlin', 'hamburg', 'muenchen', "stuttgart", "duesseldorf","koeln", "frankfurt"]
driver = webdriver.Chrome(chrome_options = options)
area_cluster = {}
print('scraping cities')
for city in cities:

    driver.get('https://www.immobilienscout24.de/neubau/{}.html'.format(city))
    time.sleep(3)
    try:
        driver.find_element_by_id('consent_prompt_submit').click()
    except Exception as e:
        continue
    regions = driver.find_elements_by_css_selector("div.section.region--section.grid.gutter.margin-bottom-l")
    results_raw = [tag for tag in regions]
    bezirke = [result.find_element_by_tag_name('h3').text for result in results_raw]
    for index,bezirk in enumerate(bezirke):
        area_cluster[bezirk] = [results_raw[index],index,city]
        
    caption = [result.find_elements_by_css_selector('h3.font-m.font-semibold.font-ellipsis') for result in results_raw]
    flat_caption = [item for sublist in caption for item in sublist if isinstance(sublist,list)]
    caption = [e.text for e in flat_caption]
    
    price = [result.find_elements_by_css_selector('span.absolute-content.padding-vertical-xs.padding-horizontal.font-ellipsis.font-right.font-m.font-semibold.font-white.projectresultlist__price') for result in results_raw]
    flat_price = [item for sublist in price for item in sublist if isinstance(sublist,list)]
    price = [e.text for e in flat_price]
    
    specs = [result.find_elements_by_css_selector('div.grid-item.one-half.font-right.font-ellipsis') for result in results_raw]
    flat_specs = [item for sublist in specs for item in sublist if isinstance(sublist,list)]
    
    area = [e.text for e in flat_specs[0::3]]
    units = [e.text for e in flat_specs[1::3]]
    availability = [e.text for e in flat_specs[2::3]]
    
    href = [result.find_elements_by_css_selector('a') for result in results_raw]
    flat_href = [item for sublist in href for item in sublist if isinstance(sublist,list)]
    href = [e.get_attribute('href') for e in flat_href]
    
    if city == 'berlin':
        df = pd.DataFrame(data = [caption,price,area,units,availability,href]).transpose()
        df['city'] = city
    else:
        df2 = pd.DataFrame(data = [caption,price,area,units,availability,href]).transpose()
        df2['city'] = city
        df = df.append(df2)
    os.system('pkill firefox')
    os.system('pkill chrome')
    os.system('pkill chromium')

df.columns = ['name', 'price', 'area', 'units', 'availability', 'link', 'city']
df['price_min'] = df['price'].apply(lambda x: re.search(r'(.*) - (.*) €',x)[1].replace('.',''))
df['price_max'] = df['price'].apply(lambda x: re.search(r'(.*) - (.*) €',x)[2].replace('.',''))
df.reset_index(inplace = True)
pickle.dump(df, open('cities_df','wb'))

links = df['link'].tolist()
for index, link in enumerate(links):
    progress = index / len(links)
    clear_output(wait=True)
    print('scraping single projects, progress is {}'.format(progress))
    driver = webdriver.Chrome(options=options)
    driver.get(link)
    WebDriverWait(driver,5)
    df['fineprint'] = 'not found'
    df['images'] = 'not found'
    try:
        driver.find_element_by_id('consent_prompt_submit').click()
    except Exception as e:
        continue
    try:
        name = driver.find_elements_by_tag_name("h1")
        name = [e.text for e in name][0]
        df.at[index, 'Project'] = name
    except Exception as e:
        df.at[index, 'Project'] = 'not found'
        project_names.append('')
        continue
    try:
        driver.find_element_by_css_selector('a.icon-arrow.margin-top-xs').click()
    except:
        continue
    try:
        fineprint = driver.find_elements_by_css_selector("p.fineprint")
        fineprint = [e.text for e in fineprint]
        df.at[index, 'fineprint'] = list(fineprint)
    except:
        df.at[index, 'fineprint'] = 'not found'
        continue
    try:
        text = driver.find_elements_by_tag_name('p')
        text= [e.text for e in text if len(e.text) > 90]
        df.at[index,'text'] = ''.join(text)
    except:
        df.at[index,'text'] = 'not found'      
        continue
    try:    
        images = driver.find_elements_by_tag_name('img')
        images = [e.get_attribute('src') for e in images]
        df.at[index,'images'] = ','.join([str(e) for e in images if 'amazonaws' in str(e)]) 
    except:
        df.at[index,'images'] = 'not found'
        continue
    try:
        df.at[index,'promoter'] = driver.find_element_by_css_selector('a.homepage-url').text
    except:
        df.at[index , 'promoter'] = 'not found'
        continue
    try:
        df.at[index,'hp'] = driver.find_element_by_css_selector('a.homepage-url').get_attribute('href')
    except:
        df.at[index,'hp'] = 'not found'
        continue
    try:
        df.at[index, 'contact_name'] = driver.find_element_by_id('detailsContactFooter').find_elements_by_tag_name('p')[0].text
    except:
        df.at[index, 'contact_name'] = 'not found'
        continue
    driver.close()
    driver.quit()
    gc.collect()
    os.system('pkill firefox')
    os.system('pkill chrome')
    os.system('pkill chromium')
    os.system('pkill nightly')
df.to_csv('dump{}.csv'.format(now), encoding = 'utf-8')
