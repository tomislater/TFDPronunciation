#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import Queue
import requests
import threading

from progressbar import ProgressBar

from termcolor import cprint

MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]
SOUNDS_DIR = os.path.join(MAIN_DIR, 'sounds')

url = 'http://www.thefreedictionary.com/'
URL_TO_SOUND = 'http://img2.tfd.com/pron/mp3/{name}.mp3'
PAT = re.compile(r"playV2\('(.*?)'\)")

WORDS_STATUS = {'downloaded': set(),
                'exists': set(),
                'not_found': set()}


class ThreadCheckWord(threading.Thread):
    def __init__(self, queue_start, queue_to_search, pbar):
        threading.Thread.__init__(self)
        self.queue_start = queue_start
        self.queue_to_search = queue_to_search
        self.pbar = pbar

    def run(self):
        while True:
            word = self.queue_start.get()

            if not self.check_file_exists(word):
                self.queue_to_search.put(word)
            else:
                WORDS_STATUS['exists'].add(word)

            self.pbar.update(self.pbar.currval + 1)
            self.queue_start.task_done()

    def check_file_exists(self, word):
        try:
            return (word + '.mp3') in os.listdir(SOUNDS_DIR)
        except OSError:
            os.makedirs(SOUNDS_DIR)
            return (word + '.mp3') in os.listdir(SOUNDS_DIR)


class ThreadSearchWord(threading.Thread):
    def __init__(self, queue_to_search, queue_to_download, pbar):
        threading.Thread.__init__(self)
        self.queue_to_search = queue_to_search
        self.queue_to_download = queue_to_download
        self.pbar = pbar

    def run(self):
        while True:
            word = self.queue_to_search.get()
            url_word = self.get_full_url(word)

            try:
                r = requests.get(url_word)
            except requests.ConnectionError as e:
                WORDS_STATUS['not_found'].add(word)
                print e
            else:
                sound_url = self.get_sound_url(r.content)

                if sound_url:
                    self.queue_to_download.put((sound_url, word))
                else:
                    WORDS_STATUS['not_found'].add(word)
            finally:
                self.pbar.update(self.pbar.currval + 1)
                self.queue_to_search.task_done()

    def get_full_url(self, word):
        return url + word

    def get_sound_url(self, text):
        url = PAT.findall(text)

        if url:
            return URL_TO_SOUND.format(name=url.pop())

        return False


class ThreadDownloading(threading.Thread):
    def __init__(self, queue_to_download, pbar):
        threading.Thread.__init__(self)
        self.queue_to_download = queue_to_download
        self.pbar = pbar

    def run(self):
        while True:
            sound_url, word = self.queue_to_download.get()
            self.download_sound_url(sound_url, word)
            self.pbar.update(self.pbar.currval + 1)
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

    queue_start = Queue.Queue()
    queue_to_search = Queue.Queue()
    queue_to_download = Queue.Queue()

    pbar = ProgressBar(maxval=len(words) * 3).start()

    for word in words:
        queue_start.put(word)

        tcw = ThreadCheckWord(queue_start, queue_to_search, pbar)
        tcw.daemon = True
        tcw.start()

        tsw = ThreadSearchWord(queue_to_search, queue_to_download, pbar)
        tsw.daemon = True
        tsw.start()

        td = ThreadDownloading(queue_to_download, pbar)
        td.daemon = True
        td.start()

    queue_start.join()
    queue_to_search.join()
    queue_to_download.join()

    pbar.finish()

    exists = ', '.join(WORDS_STATUS['exists'])
    not_found = ', '.join(WORDS_STATUS['not_found'])
    downloaded = ', '.join(WORDS_STATUS['downloaded'])

    if exists:
        cprint('Files exists: {0}'.format(exists), 'green')

    if not_found:
        cprint('Files not_found: {0}'.format(not_found), 'red')

    if downloaded:
        cprint('Files downloaded: {0}'.format(downloaded), 'blue')
