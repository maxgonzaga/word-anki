import csv, time, shutil, sys, os, time, logging
import urllib.request
from urllib.request import Request, urlopen
import requests
from bs4 import BeautifulSoup
from google_images_download import google_images_download

ANKI_MEDIA_PATH = 'C:\\Users\\maxgonzaga\\AppData\\Roaming\\Anki2\\maxgonzaga\\collection.media'

def get_examples(examples_container):
    list_of_examples = []
    examples = examples_container.find_all(class_='x')
    for example in examples:
        list_of_examples.append(example.get_text())
    for item in list_of_examples:
        logging.info(' ' * 10 + item)
    return list_of_examples

def get_meanings(meanings_container):
    meanings = meanings_container.find_all(class_='sn-g')
    list_of_meanings = []
    list_of_examples = []
    for meaning in meanings:
        try:
            definition = meaning.find(class_='def').get_text()
            logging.info(definition)
            try:
                examples_container = meaning.find(class_='x-gs')
                list_of_examples = get_examples(examples_container)
                list_of_meanings.append((definition, list_of_examples))
            except:
                list_of_meanings.append((definition, []))
        except:
            continue
    return list_of_meanings
    
def generate_notes(csv_object, page_source):
    soup = BeautifulSoup(page_source, features='lxml')
    word = soup.find('h2', class_='h').get_text()
    transcription = get_audio_and_transcription(word, page_source)
    audio = '[sound:' + word + '.mp3]'
    image = ''
    try:
        get_image(word)
        image = '<img>' + word + '</img>'
    except:
        image = ''
        logging.info('Problem downloading image.')
    part_of_speech = soup.find('span', class_='pos').get_text()
    logging.info('Part of speech: ' + part_of_speech)
    definitions_container = soup.find(class_='sn-gs')
    groups_of_definitions = definitions_container.find_all(class_='shcut-g')
    if len(groups_of_definitions) != 0:
        for group in groups_of_definitions:
            group_name = group.find(class_='shcut').get_text()
            logging.info('Group: ' + group_name)
            list_of_meanings = get_meanings(group)
            write_to_file(csv_object, list_of_meanings, group_name, word, part_of_speech, transcription, audio, image)
    else:
        group_name = ''
        list_of_meanings = get_meanings(definitions_container)
        write_to_file(csv_object, list_of_meanings, group_name, word, part_of_speech, transcription, audio, image) 

def write_to_file(csv_object, list_of_meanings, group_name, word, part_of_speech, transcription, audio, image):
    html_all_meanings = '<p class=\'group-name\'>' + group_name + '</p>'
    for meaning, list_of_examples in list_of_meanings:
        html_examples = []
        for example in list_of_examples:
            html_examples.append('<li>' + example + '</li>')
        html_list_of_examples = '<ul class=\'examples\'>' + ''.join(html_examples) + '</ul>'
        html_meaning = '<p class=\'def\'>' + meaning + '</p>' + html_list_of_examples
        html_all_meanings = html_all_meanings + '<div class=\'meaning\'>' + html_meaning + '<div>'
    csv_object.writerow([html_all_meanings, part_of_speech, word, transcription, audio, image])

def get_image(word):
    response = google_images_download.googleimagesdownload()
    arguments = {"keywords":word,"limit":1,"print_urls":True, "output_directory":ANKI_MEDIA_PATH, "no_directory":True, "format":"jpg", "metadata":False}
    temporary_path = response.download(arguments)[word][0]
    print('Temporary path: ' + temporary_path)
    destination_path = os.path.join(ANKI_MEDIA_PATH, word + '.jpg')
    print('Destination path: ' + destination_path)
    shutil.move(temporary_path, destination_path)

def get_audio_and_transcription(word, page_source):
    soup = BeautifulSoup(page_source, features='lxml')
    audio_source = soup.find(attrs={'title':' pronunciation American'}).attrs['data-src-mp3']
    urllib.request.urlretrieve(audio_source, os.path.join(ANKI_MEDIA_PATH, word + '.mp3'))
    transcription = str(soup.find(class_='phon').contents[3])
    return transcription

def download_page(url):
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    page_source = response.read().decode('utf-8')
    return page_source

def main():
    level = logging.INFO
    format = '%(message)s'
    handlers = [logging.FileHandler('vocabulary.log'), logging.StreamHandler()]
    logging.basicConfig(level=level, format=format, handlers=handlers)
    t0 = time.time()
    try:
        file_path = os.path.abspath(sys.argv[1])
    except:
        logging.info('Missing argument...')
        logging.info('Script is going to close.')
        sys.exit()
    file_object = open(file_path)
    file_content = file_object.read()
    file_object.close()
    list_words = file_content.split('\n')
    not_found_words = []
    output = open('oxford.csv', 'w', newline='', encoding='utf-8')
    csv_object = csv.writer(output)
    for word in list_words:
        logging.info('CURRENT WORD: ' + word)
        try:
            page_source = download_page('https://www.oxfordlearnersdictionaries.com/definition/american_english/' + word)
            generate_notes(csv_object, page_source)
        except:
            not_found_words.append(word)
            logging.info(word + " wasn't found.")
            continue
        logging.info('\n\n')
    logging.info('Not found words:\n' + '\n'.join(not_found_words))
    output.close()
    t1 = time.time()
    logging.info('Time: ' + str(round(t1 - t0, 0)) + ' seconds')

if __name__ == "__main__":
    main()