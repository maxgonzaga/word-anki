#To be implemented
#List wiht not found words
#Get definitions from another dictionary when the word is not found
#Try getting examples without openning headless browser
#Thread for images downloading
#add synonims

import csv, time, shutil, sys, os, time, logging
import urllib.request
from urllib.request import Request, urlopen
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from google_images_download import google_images_download

logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ANKI_MEDIA_PATH = 'C:\\Users\\maxgonzaga\\AppData\\Roaming\\Anki2\\maxgonzaga\\collection.media'

# The function takes a word as argument and returns a triple with its definition in several versions
def get_definition(word, soup):
    try:
        short_definition = soup.find(class_='short')
        long_definition = soup.find(class_='long').get_text()
        hidden_word = []
        visible_word = []
        for item in short_definition.contents:
            if type(item) == type(short_definition):
                hidden_word.append('[...]')
                visible_word.append(item.string)
            else:
                visible_word.append(item.string)
                hidden_word.append(item.string)
        hidden_word_string = ''.join(hidden_word)
        visible_word_string = ''.join(visible_word)
    except:
        logging.info('Definitions weren\'t found.')
        hidden_word_string = 'NOT FOUND!'
        visible_word_string = 'NOT FOUND!'
        long_definition = 'NOT FOUND!'
    return hidden_word_string, visible_word_string, long_definition

def get_example(word, number, browser):
    browser.get('https://www.vocabulary.com/dictionary/' + word)
    time.sleep(3)
    soup = BeautifulSoup(browser.page_source, features='lxml')
    list_examples = []
    try:
        tags = soup.find_all(class_='sentence', limit=number)
        for example in tags:
            list_examples.append(example.get_text())
    except:
        logging.info('Examples weren\'t found.')
        for i in range(number):
            list_examples.append('NOT FOUND!')
    return list_examples

# This function downloads first Google image result for word and stores it in Anki collection
def get_image(word):
    response = google_images_download.googleimagesdownload()
    arguments = {"keywords":word,"limit":1,"print_urls":True, "output_directory":ANKI_MEDIA_PATH, "no_directory":True, "format":"jpg"}
    temporary_path = response.download(arguments)[word][0]
    print('Temporary path: ' + temporary_path)
    destination_path = os.path.join(ANKI_MEDIA_PATH, word + '.jpg')
    print('Destination path: ' + destination_path)
    shutil.move(temporary_path, destination_path)

# The function takes a word as argument and returns its pronunciation in audio and its transcription
def get_audio_and_transcription(word, page_source):
    soup = BeautifulSoup(page_source, features='lxml')
    try:
        audio_source = soup.find(attrs={'title':' pronunciation American'}).attrs['data-src-mp3']
        urllib.request.urlretrieve(audio_source, os.path.join(ANKI_MEDIA_PATH, word + '.mp3'))
        transcription = str(soup.find(class_='phon').contents[3])
        return transcription
    except:
        logging.info('Audio wasn\'t downloaded.')
        return 'NOT FOUND!'

def download_page(url):
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    page_source = response.read().decode('utf-8')
    return page_source

# This is the main program
def main():
    t0 = time.time()
    try:
        file_path = os.path.abspath(sys.argv[1])
    except:
        print('Missing arguments.')
        sys.exit()
    print('Openning browser...')
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options)
    file_object = open(file_path)
    file_content = file_object.read()
    list_words = file_content.split('\n')
    file_object = open('vocabulary.csv', 'w', newline='', encoding='utf-8')
    csv_writer_object = csv.writer(file_object)
    for word in list_words:
        print('Current word: ' + word)
        logging.info('Current word: ' + word)
        try:
            page_source_vocabulary = download_page('https://www.vocabulary.com/dictionary/' + word)
            page_source_oxford = download_page('https://www.oxfordlearnersdictionaries.com/definition/american_english/' + word)
        except:
            print(word + " wasn't found.")
            continue
        soup = BeautifulSoup(page_source_vocabulary, features='lxml')
        print('Getting definitions...')
        definitions = get_definition(word, soup)
        print('Getting examples of use...')
        examples = get_example(word, 4, browser)
        print('Downloading pronounce...')
        transcription = get_audio_and_transcription(word, page_source_oxford)
        print('Downloading image...')
        try:
            get_image(word)
        except:
            logging.info('Problem downloading image.')
        csv_writer_object.writerow([word,
                                    definitions[0],
                                    definitions[1],
                                    definitions[2],
                                    examples[0],
                                    examples[1],
                                    examples[2],
                                    examples[3],
                                    transcription,
                                    '[sound:' + word + '.mp3' + ']',
                                    '<img src=' + word + '.jpg>'])
        print('\n')
    file_object.close()
    browser.quit()
    t1 = time.time()
    print('Time: ' + str(round(t1 - t0, 0)) + ' seconds')

main()