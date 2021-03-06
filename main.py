#!/usr/bin/env python3

# https://github.com/ytdl-org/youtube-dl/blob/master/README.md#embedding-youtube-dl
# https://github.com/alexmercerind/youtube-search-python

import argparse
import configparser
import json
import logging as log
import os
import re
import youtube_dl
from youtubesearchpython import searchYoutube

log.basicConfig(level=log.DEBUG)


class Song(object):
    """
    Represents a Song. Has convenience methods for reading the ini file of a
    song and checking other properties
    """
    def __init__(self, path):
        super(Song, self).__init__()
        self.path = path
        self.inifile = os.path.join(self.path, 'song.ini')

        # setup config
        config = configparser.ConfigParser()
        config.read(self.inifile)
        
        # read values out of the config
        self.name   = config['song']['name']
        self.artist = config['song']['artist']


    def hasVideo(self):
        return os.path.isfile(self.videoPath)

    @property
    def videoPath(self):
        """ returns the path to the video file """
        return os.path.join(self.path, 'video.mp4')

    @property
    def searchTerm(self):
        """ returns a reasonable search query for this song """
        # strip out the (wavegroup) suffix in some songs to make the search more accurate
        artist = re.sub(r' ?\(wavegroup\)', "", self.artist, flags=re.I)
        return f'{self.name} {artist} music video'

    def topLink(self):
        """
        Returns the top video for a youtube search of this song
        """
        if not hasattr(self, '_topLink'):
            search = searchYoutube(self.searchTerm, offset = 1, mode = "dict", max_results = 1)
            self._topLink = search.result()['search_result'][0]['link']
        return self._topLink

    def downloadVideo(self):
        """
        Downloads a video for this song
        """
        if not self.hasVideo():
            log.debug(f'Downloading video for {self.name}, {self.artist}')
            self.saveVideoURL()
            try:
                downloadYoutubeVideo(self.topLink(), self.videoPath)
            except Exception as e:
                log.error(f'Couldn\'t download video for {self.name}, {self.artist}')
                print(e)
                self.deleteVideoURLFile()

        else:
            log.debug(f'video found for {self.name}, {self.artist}')

    def saveVideoURL(self):
        # TODO see if this can be saved in song.ini
        with open(os.path.join(self.path, 'video_origin.txt'), 'w') as f:
            f.write(self.topLink())
    def deleteVideoURLFile(self):
        """ Delete the url video file creaded by saveVideoURL """
        urlfile = os.path.join(self.path, 'video_origin.txt')
        if os.path.isfile(urlfile):
            os.remove(urlfile)
         

        

def getSongs(root):
    """
    Given a root dir, create a Song for each songdir
    Sometimes the dirs are nested, depending on how they were zipped/unzipped
    """
    def isSongdir(d):
        return 'song.ini' in d[2]

    return [ Song(d[0]) for d in os.walk(root) if isSongdir(d) ]



def downloadYoutubeVideo(url, path):
    """Downloads and saves the video at url to a file at path

    :url: url of youtube video
    :path: path to save downloaded file to
    """
    ydl_opts = {
            'format': 'mp4',
            'outtmpl': path
        }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir')
    args = parser.parse_args()

    print("Scanning songs...")
    for song in getSongs(args.dir):
        song.downloadVideo()

