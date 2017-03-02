# -*- coding: utf-8 -*-

import telebot as tb
import requests

from sin_azucar_token import TOKEN
from bs4 import BeautifulSoup
import random
import time

import gettext

# Set up message catalog access

t = gettext.translation(
    'sin_azucar_bot', 'locale',
    fallback=True,
)
_ = t.gettext

bot = tb.TeleBot(TOKEN)

commands = {  # command description used in the "help" command
              'start': _('Get used to the bot'),
              'help': _('Gives you information about the available commands'),
              'product '+_('[name]'): _('Retrieves a given product or a random one'),
              'list '+_('[letter]'): _('Show all available products starting with a given letter'),
              'hist': _('List last 5 products shown')
}

MAIN_URL = "http://www.sinazucar.org"   

products = {}
hist = []

# start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    '''This handlert shows a welcome message.'''
    welcome_message = _("Howdy!")
    bot.reply_to(message, welcome_message)
    start_time = time.time()
    load_data()
    print("load time: {0}".format(time.time()-start_time))
    print("#products: {0}".format(len(products)))

# help
@bot.message_handler(commands=['help'])
def command_help(message):
    '''
    Display the commands and what are they intended for.
    '''
    chat_id = message.chat.id
    help_text = _("The following commands are available: \n")
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(chat_id, help_text) # send the generated help page

# product
@bot.message_handler(commands=['product'])
def get_product(message):
    '''
    Retrieve product info & photo.
    If no argument is passed, returns a random product
    '''

    chat_id = message.chat.id
    
    # extract arguments from message
    arguments = tb.util.extract_arguments(message.text).lower()
    
    if len(arguments) != 0:
        info, image, title = findMe(arguments)
        if info is not None and image is not None:
            bot.send_message(chat_id, '<b>'+title+':</b> '+info, parse_mode= 'html')
            bot.send_photo(chat_id, image)
            update_hist(title)
        else:
            bot.send_message(chat_id,info)
    else: # no arguments
        get_random_product(message)
        #bot.send_message(chat_id, "No product available. Try /product_list command.")


@bot.message_handler(commands=['list'])
def get_list(message):
    '''
    Lists all products starting with a given letter
    '''
    
    chat_id = message.chat.id
    # extract arguments from message
    arguments = tb.util.extract_arguments(message.text).lower()
    if len(arguments) != 0:
        short_list = []
        for k in products.keys():
            if k[0].lower() == arguments:
                short_list.append(k)
        if len(short_list) == 0:
            bot.send_message(chat_id,_("No products found starting with {0}").format(arguments))
        else:
            bot.send_message(chat_id,'\n'.join(sorted(short_list)))
    else: # no arguments
        bot.send_message(chat_id,'\n'.join(sorted(list(products.keys()))))

@bot.message_handler(commands=['hist'])
def show_hist(message):
    '''
    Last n elementsRetrieve product info.
    '''
    chat_id = message.chat.id
    if len(hist) > 0:
        bot.send_message(chat_id, '\n'.join(hist))
    else:
        bot.send_message(chat_id,_("Hist is empty"))

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
                update_hist(entries[random_product_index]['title'])
    else:
        bot.send_message(chat_id, _("The site seems to be unavailable at the moment. Please, try again later."))

def update_hist(prod_name):
    global hist
    if len(hist) > 4:
        hist = hist[1:]
    hist.append("* {0}".format(prod_name))

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
    Loads all products
    '''
    print("load_data()")
    r = requests.get(MAIN_URL)
    if r.status_code == 200:
        npages  = get_num_pages(r.text)
        build_items_dictionary(npages)
        print("END load_data()")
        return npages
    else:
        return _("The site seems to be unavailable at the moment. Please, try again later.")

def get_num_pages(html):
    '''
    Gets number of pages to be scanned
    '''
    soup = BeautifulSoup(html, "lxml")
    pagination = soup.find("span",{'class':'pagination-meta'})
    total_pages = int(pagination.text.split(" ")[-1])
    return total_pages

def findMe(param):
    '''
    Finds a product
    '''
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
        return _("The site seems to be unavailable at the moment. Please, try again later."), None, None

    return _("Item not found."), None, None


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


'''
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    #This handler echoes all incoming text messages back to the sender.
    bot.reply_to(message, message.text)
'''
bot.polling()