import os
import re
import sys
import requests

main_dir = os.path.split(os.path.abspath(__file__))[0]
sounds_dir = os.path.join(main_dir, 'sounds')

url = 'http://www.thefreedictionary.com/'
url_to_sound = 'http://img2.tfd.com/pron/mp3/{name}.mp3'
pat_us = re.compile(r"playV2\('(.*)'\)?;")
pat_gb = re.compile(r"playV2\('(.*?)'\)")


def get_full_url(word):
    return url + word


def check_file_exsist(word):
    global sounds_dir
    try:
        return (word + '.mp3') in os.listdir(sounds_dir)
    except OSError:
        os.makedirs(os.path.join(main_dir, 'sounds'))
        sounds_dir = os.path.join(main_dir, 'sounds')
        return (word + '.mp3') in os.listdir(sounds_dir)


def get_sound_url(text):
    try:
        print 'Downloading US version'
        return url_to_sound.format(name=pat_us.findall(text)[0])
    except IndexError:
        print 'US version not found'
        print 'Downloading GB version'
        return url_to_sound.format(name=pat_gb.findall(text)[0])
    # TODO other exceptions


def download_sound_url(url, name):
    come_up = 1
    full_name = name + '.mp3'

    while True:
        print '{0} approach'.format(come_up)
        try:
            s = requests.get(url)
        except requests.exceptions.ConnectionError:
            come_up += 1
        else:
            break

    with open('sounds/{0}'.format(full_name), 'wb') as f:
        f.write(s.content)
    return full_name


if __name__ == '__main__':
    for word in sys.argv[1:]:
        if check_file_exsist(word):
            print 'File {0} exists. Omit downloading. \n'.format(word)
            continue

        url_word = get_full_url(word)
        r = requests.get(url_word)
        sound_url = get_sound_url(r.content)
        print 'Sound url: {0}'.format(sound_url)

        print 'Downloading sound'
        name = download_sound_url(sound_url, word)
        print 'Sound {0} completely downloaded\n'.format(name)

    print 'Files: {0}'.format(', '.join(sys.argv[1:]))
