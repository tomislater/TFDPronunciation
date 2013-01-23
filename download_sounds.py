#!/usr/bin/env python

import os
import re
import sys
import requests
import threading
import Queue

MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]
SOUNDS_DIR = os.path.join(MAIN_DIR, 'sounds')

url = 'http://www.thefreedictionary.com/'
URL_TO_SOUND = 'http://img2.tfd.com/pron/mp3/{name}.mp3'
PAT_US = re.compile(r"playV2\('(.*)'\)?;")
PAT_GB = re.compile(r"playV2\('(.*?)'\)")

WORDS_STATUS = {'downloaded': set(),
                'exists': set(),
                'not_found': set()}


class ThreadCheckWord(threading.Thread):
    def __init__(self, queue, queue_to_search):
        threading.Thread.__init__(self)
        self.queue = queue
        self.queue_to_search = queue_to_search

    def run(self):
        while True:
            word = self.queue.get()

            if not self.check_file_exists(word):
                self.queue_to_search.put(word)
            else:
                WORDS_STATUS['exists'].add(word)

            self.queue.task_done()

    def check_file_exists(self, word):
        try:
            return (word + '.mp3') in os.listdir(SOUNDS_DIR)
        except OSError:
            os.makedirs(SOUNDS_DIR)
            return (word + '.mp3') in os.listdir(SOUNDS_DIR)


class ThreadSearchWord(threading.Thread):
    def __init__(self, queue_to_search, queue_to_download):
        threading.Thread.__init__(self)
        self.queue_to_search = queue_to_search
        self.queue_to_download = queue_to_download

    def run(self):
        while True:
            word = self.queue_to_search.get()
            url_word = self.get_full_url(word)
            r = requests.get(url_word)
            sound_url = self.get_sound_url(r.content)

            if sound_url:
                self.queue_to_download.put((sound_url, word))
            else:
                WORDS_STATUS['not_found'].add(word)

            self.queue_to_search.task_done()

    def get_full_url(self, word):
        return url + word

    def get_sound_url(self, text):
        url = PAT_US.findall(text)
        if url:
            return URL_TO_SOUND.format(name=url[0])

        url = PAT_GB.findall(text)
        if url:
            return URL_TO_SOUND.format(name=url[0])
        return False


class ThreadDownloading(threading.Thread):
    def __init__(self, queue_to_download):
        threading.Thread.__init__(self)
        self.queue_to_download = queue_to_download

    def run(self):
        while True:
            sound_url, word = self.queue_to_download.get()
            self.download_sound_url(sound_url, word)
            self.queue_to_download.task_done()

    def download_sound_url(self, url, name):
        full_name = name + '.mp3'

        while True:
            try:
                s = requests.get(url)
            except requests.exceptions.ConnectionError:
                continue
            else:
                break

        with open('sounds/{0}'.format(full_name), 'wb') as f:
            f.write(s.content)

        WORDS_STATUS['downloaded'].add(name)


if __name__ == '__main__':
    words = sys.argv[1:]

    queue = Queue.Queue()
    queue_to_search = Queue.Queue()
    queue_to_download = Queue.Queue()

    for word in words:
        tcw = ThreadCheckWord(queue, queue_to_search)
        tcw.setDaemon(True)
        tcw.start()
        queue.put(word)

        tsw = ThreadSearchWord(queue_to_search, queue_to_download)
        td = ThreadDownloading(queue_to_download)
        tsw.setDaemon(True)
        td.setDaemon(True)
        tsw.start()
        td.start()

    queue.join()
    queue_to_search.join()
    queue_to_download.join()

    print('Files exists: {0}'.format(', '.join(WORDS_STATUS['exists'])))
    print('Files not_found: {0}'.format(', '.join(WORDS_STATUS['not_found'])))
    print('Files downloaded: {0}'.format(', '.join(WORDS_STATUS['downloaded'])))
