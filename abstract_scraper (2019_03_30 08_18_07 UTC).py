from selenium import webdriver #instantiate and open a browser
from selenium.webdriver.support.ui import WebDriverWait # let it wait for some time. patience while loading it all
from selenium.webdriver.common.by import By # search for by param
from selenium.webdriver.common.keys import Keys # we want to press enter at some stage
from selenium.webdriver.support import expected_conditions as EC # what am i looking for, has the page loaded?
from selenium.common.exceptions import TimeoutException # handle timeouts
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import pickle

# we should please use the unittest framework in combination to clean this up and make some sense with classes
#instantiate ff

options = Options()
options.add_argument("--headless")

browser = driver = webdriver.Firefox(firefox_options = options, executable_path = r"/usr/local/bin/geckodriver") #it does need a driver executable

with open('numlist.pickle', 'rb') as pcl:
	pat_numbers = pickle.load(pcl)
pcl.close()

for number in pat_numbers:
	#pass in the desired URL, implement exception handling

	browser.get("http://patentscope.wipo.int/search/en/search.jsf") #which page?

	timeout = 20 #how much time until timeout ex is raised

	try:
		WebDriverWait(browser,timeout).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="simpleSearchSearchForm:fpSearch"]'))) #see that our sought element is loaded before you do something else

	except TimeoutException: #if its not there, do tell.
		print("Timeout")
		browser.quit()

	#find the elements by expath gives an array of sel objects, but since there's only one, we only want one
	searchElement = browser.find_elements_by_xpath('//*[@id="simpleSearchSearchForm:fpSearch"]')[0] #readability, mostly. the xpath is good for hidden stuff. ff has that inbuilt
	searchElementEntry = '{}'.format(number) #found per ff

	print('I am headlessly trying to get the description for patent {}:'.format(searchElementEntry))


	searchElement.clear() #empty the field
	searchElement.send_keys(searchElementEntry, Keys.RETURN) #send what i defined above, and we shall press return to send the form

	try:
		WebDriverWait(browser,timeout).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div[1]/table[2]/tbody[1]/tr[6]/td/div'))) #see that our sought element is loaded before you do something else

	except TimeoutException: #if its not there, do tell.
		print("Timeout")
		browser.quit()
		
	pat_description = browser.find_elements_by_xpath('/html/body/div[1]/div[1]/table[2]/tbody[1]/tr[6]/td/div')[0] #this only finds the second occurence which is the wpo correspondent. will have to add an exception to get the more garbled one if that dont check out
	print(pat_description.text, '\n', 'Extraction successful. Attempting to save now')

	payload = pat_description.text
	filename = searchElementEntry.replace('/','_') #the patent classifcation contains slashes which naturally does some shenanigans with our OS
	text_file = open('texts/desc_{}.txt'.format(filename), 'w')
	text_file.write(payload)
	text_file.close()
	print("file saved. moving on...")


	browser.quit() # this ends the entire app and the driver -- alternatively close the tab / browser, but keep the driver running: browser.close()
