#!/usr/bin/env python

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

come_up_dict = {1: 'st',
                2: 'nd',
                3: 'rd'}


def get_full_url(word):
    return url + word


def check_file_exists(word):
    try:
        return (word + '.mp3') in os.listdir(sounds_dir)
    except OSError:
        os.makedirs(sounds_dir)
        return (word + '.mp3') in os.listdir(sounds_dir)


def get_sound_url(text):
    print('Downloading US version')
    url = pat_us.findall(text)
    if url:
        return url_to_sound.format(name=url[0])

    print('US version not found')
    print('Downloading GB version')
    url = pat_gb.findall(text)
    if url:
        return url_to_sound.format(name=url[0])
    return False


def download_sound_url(url, name):
    come_up = 1
    full_name = name + '.mp3'

    while True:
        print('{0}{1} approach'.format(come_up, come_up_dict.get(come_up, 'th')))

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
        if check_file_exists(word):
            print('File {0} exists. Omit downloading. \n'.format(word))
            continue

        print('Downloading {word}.mp3 file'.format(word=word))
        url_word = get_full_url(word)
        r = requests.get(url_word)
        sound_url = get_sound_url(r.content)
        if sound_url:
            name = download_sound_url(sound_url, word)
            print('Sound {0} completely downloaded\n'.format(name))
        else:
            print('Pronunciation of word {0} has been not found\n'.format(word))

    print('Files: {0}'.format(', '.join(sys.argv[1:])))
