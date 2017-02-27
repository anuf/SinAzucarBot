# -*- coding: utf-8 -*-

import telebot as tb
import requests

from sin_azucar_token import TOKEN
from bs4 import BeautifulSoup
import random

bot = tb.TeleBot(TOKEN)

MAIN_URL = "http://www.sinazucar.org"
products = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    '''This handlert shows a welcome message.'''
    '''
    Display the commands and what are they intended for.
    '''
    bot.reply_to(message, help_message())
    
'''
@bot.message_handler(func=lambda message: True)
def echo_all(message):
	#This handler echoes all incoming text messages back to the sender.
	bot.reply_to(message, message.text)
'''
@bot.message_handler(commands=['products'])
def get_products(message):
    '''
    Retrieve product info & photo.
    '''
    chat_id = message.chat.id
    load_data()
    parameters = ' '.join(message.text.split(' ')[1:]).lower()
    if len(parameters) != 0:
        if parameters in products.keys():
            bot.send_message(chat_id, '<b>'+products[parameters]['info']+':</b> '+info, parse_mode= 'html')
            bot.send_photo(chat_id, products[parameters]['image'])
        else:
            bot.send_message(chat_id,"A message")
    else: # no parameters
        bot.send_message(chat_id, "No product available. Try /product_list command.")

@bot.message_handler(commands=['product'])
def get_product(message):
    '''
    Retrieve product info & photo.
    '''

    chat_id = message.chat.id
    
    # extract arguments from message
    arguments = tb.util.extract_arguments(message.text).lower()
    
    if len(arguments) != 0:
        info, image, title = findMe(arguments)
        if info is not None and image is not None:
            bot.send_message(chat_id, '<b>'+title+':</b> '+info, parse_mode= 'html')
            bot.send_photo(chat_id, image)
        else:
            bot.send_message(chat_id,info)
    else: # no arguments
        get_random_product(message)
        #bot.send_message(chat_id, "No product available. Try /product_list command.")

@bot.message_handler(commands=['product_list'])
def get_product_list(message):
    '''
    Retrieve product info.
    '''
    chat_id = message.chat.id
    # get incoming's page, parse it and cache it
    incoming_info = download_locations_incoming()
    bot.send_message(chat_id, incoming_info)    
    #send_message_splitting_if_necessary(chat_id, incoming_info)
    photo = 'http://www.sinazucar.org/wp-content/uploads/2017/02/093_bimananCrema-705x705.jpg'
    bot.send_photo(chat_id, photo)

@bot.message_handler(commands=['random'])
def get_random_product(message):
    chat_id = message.chat.id
    r = requests.get(MAIN_URL)
    if r.status_code == 200:
        npages  = get_num_pages(r.text)
        random_page_index = random.randint(1, npages)
        random_page_URL = MAIN_URL + "/page/" + str(random_page_index) +"/"
        r2 = requests.get(random_page_URL)
        if r2.status_code == 200: 
            soup = BeautifulSoup(r2.text, "lxml")
            entries = soup.find_all("a",{'class':'av-masonry-entry'})
            random_product_index = random.randint(0, len(entries)-1)
            print("{0} :: {1}".format(random_page_URL, entries[random_product_index]['href']))
            r3 = requests.get(entries[random_product_index]['href'])
            if r3.status_code == 200:
                subsoup = BeautifulSoup(r3.text, "lxml")
                infotext = subsoup.find('p')
                if infotext is None:
                    infotext = subsoup.find('li') 
                info = infotext.text
                image = subsoup.find('img',{'class':'avia_image '})['src']
                
                bot.send_message(chat_id, '<b>'+entries[random_product_index]['title']+':</b> '+info, parse_mode= 'html')
                bot.send_photo(chat_id, image)
    else:
        bot.send_message(chat_id, "The site seems to be unavailable at the moment. Please, try again later.")

def send_message_splitting_if_necessary(chat_id, long_text):
	'''
	Sends message expected to be long by smartly splitting it
	'''
	lines = long_text.split('\n')
	current_text = ""
	for line in lines:
		current_text += line + '\n'
		if len(current_text) > 3000:
			bot.send_message(chat_id, current_text)
			current_text = ""

def load_data():
    '''
    Load Main page's info
    '''
    print("load_data()")
    products = {}
    r = requests.get(MAIN_URL)
    if r.status_code == 200:
        npages  = get_num_pages(r.text)
        build_items_dictionary(npages)
        return npages
    else:
        return "The site seems to be unavailable at the moment. \
        Please, try again later."

def get_num_pages(html):
    '''
    Parses incoming info HTML page
    '''
    soup = BeautifulSoup(html, "lxml")
    pagination = soup.find("span",{'class':'pagination-meta'})
    total_pages = int(pagination.text.split(" ")[-1])
    return total_pages

def findMe(param):
    r = requests.get(MAIN_URL)
    if r.status_code == 200:
        npages  = get_num_pages(r.text)
        for num_page in range(npages):
            num_page += 1
            page_URL = MAIN_URL + "/page/" + str(num_page) +"/"
            r = requests.get(page_URL)
            if r.status_code == 200: 
                soup = BeautifulSoup(r.text, "lxml")
                entries = soup.find_all("a",{'class':'av-masonry-entry'})
                for entry in entries:
                    if entry['title'].lower() == param.lower():
                        r2 = requests.get(entry['href'])
                        print(entry['href'])
                        if r2.status_code == 200:
                            subsoup = BeautifulSoup(r2.text, "lxml")
                            
                            aviaDiv = subsoup.find('div',{'class':'avia_textblock'})
                            if aviaDiv.p :
                                infotext = aviaDiv.p.text  
                            else:
                                infotext = aviaDiv.ul.li.text 
                                
                            info = infotext
                            image = subsoup.find('img',{'class':'avia_image '})['src']
                            return info, image, entry['title']
    else:
        return "The site seems to be unavailable at the moment. Please, try again later.", None, None

    return "Item not found.", None, None


def build_items_dictionary(num_pages):
    p = {}
    for num_page in range(num_pages):
        num_page += 1
        page_URL = MAIN_URL + "/page/" + str(num_page) +"/"
        r = requests.get(page_URL)
        if r.status_code == 200: 
            soup = BeautifulSoup(r.text, "lxml")
            entries = soup.find_all("a",{'class':'av-masonry-entry'})
            for entry in entries:
                r2 = requests.get(entry['href'])
                if r2.status_code == 200:
                    subsoup = BeautifulSoup(r2.text, "lxml")
                    title = entry['title'].lower()
                    infotext = subsoup.find('p')
                    if infotext is None:
                        infotext = subsoup.find('li') 
                    info = infotext.text
                    image = subsoup.find('img',{'class':'avia_image '})['src']
                    products[title] = {'info':info, 'image': image}
def help_message():
    '''Return help message'''
    message  =  'Este bot muestra el azucar contenido en diversos productos'
    return message

bot.polling()