import telebot
import requests

from sin_azucar_token import TOKEN
from bs4 import BeautifulSoup


print(TOKEN)
bot = telebot.TeleBot(TOKEN)

INCOMING_URL = "http://www.sinazucar.org/page/2"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	'''This handlert shows a welcome message.'''
	bot.reply_to(message, "Howdy, how are you doing now?")

'''
@bot.message_handler(func=lambda message: True)
def echo_all(message):
	#This handler echoes all incoming text messages back to the sender.
	bot.reply_to(message, message.text)
'''
@bot.message_handler(commands=['producto'])
def get_producto(message):
	'''
	Retrieve product info.
	'''
	print('pasa')
	chat_id = message.chat.id
	# get incoming's page, parse it and cache it
	incoming_info = download_locations_incoming()
	print(incoming_info)
	bot.send_message(chat_id, incoming_info)	
	#send_message_splitting_if_necessary(chat_id, incoming_info)

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

def download_locations_incoming():
    '''
    Download incoming info page and parses it to a (large) string
    '''
    print("download_locations_incoming")
    r = requests.get(INCOMING_URL)
    if r.status_code == 200:
        return parse_incoming_page(r.text)
    else:
        return "Hummm, parece que esa informacion no esta disponible en estos momentos. \
        Por favor, intentalo de nuevo mas tarde"

def parse_incoming_page(html):
    '''
    Parses incoming info HTML page
    '''
    soup = BeautifulSoup(html, "lxml")
    pp = soup.find("span",{'class':'pagination-meta'})
    total_pages = int(pp.text.split(" ")[-1])

    parsed_string = 'PRODUCTOS:\n'
    zz = soup.find_all("a",{'class':'av-masonry-entry'})
    for z in zz:
    	parsed_string += '{0}\n'.format(z['title'])
    return parsed_string
    #print("{0} :: {1} :: {2}".format(pp, pp.text, type(pp)))
    '''
    table = soup.find('table')
    rows = table.find_all('tr')[2:-1]
    for row in rows:
        columns = row.find_all('td')
        date = columns[0].text.strip()
        if date == today_str:
            continue # Ignores the line if incoming date is today
        location = columns[1].text.title().strip()
        info = parse_info_column(columns[2])
        parsed_string += "- {0}: {1} ({2})\n".format(date, info['info'], location)
    
	return parsed_string
	'''
bot.polling()