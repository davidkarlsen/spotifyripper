#!/usr/bin/env python
# -*- coding: utf8 -*-

from subprocess import call, Popen, PIPE
from spotify import Link, Image
from jukebox import Jukebox, container_loaded
import os, sys, argparse
import threading
import time
import re

#Music library imports
import fnmatch
import eyed3
import collections

#playback = False # set if you want to listen to the tracks that are currently ripped (start with "padsp ./jbripper.py ..." if using pulse audio)

pipe = None
ripping = False
end_of_track = threading.Event()

musiclibrary = None
args = None

def printstr(str): # print without newline
    sys.stdout.write(str)
    sys.stdout.flush()

def shell(cmdline): # execute shell commands (unicode support)
    call(cmdline, shell=True)

def rip_init(session, track):
    global pipe, ripping
    num_track = "%02d" % (track.index(),)
    artist = artist = ', '.join(a.name() for a in track.artists())
    album = track.album().name()
    title = track.name()
    
    if args.directory is True:
        directory = os.getcwd() + "/" + artist + "/" + album + "/"
        mp3file = title+".mp3"
    else:
        directory = os.getcwd() + "/"
        mp3file = artist + " - " + title + " - [ " + album + " ].mp3"
    #Removing invalid file characters
    mp3file = re.sub(r'[\\/:"*?<>|]+', ' ', mp3file)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    printstr("ripping " + directory + mp3file + " ...\n")
    p = Popen("lame --silent -V" + args.vbr + " -h -r - \""+ directory + mp3file +"\"", stdin=PIPE, shell=True)
    pipe = p.stdin
    ripping = True

def rip_terminate(session, track):
    global ripping
    if pipe is not None:
        print(' done!')
        #Avoid concurrent operation exceptions
        if args.playback:
            time.sleep(1)
        pipe.close()
    ripping = False

def rip(session, frames, frame_size, num_frames, sample_type, sample_rate, channels):
    if ripping:
        printstr('.')
        pipe.write(frames);

def rip_id3(session, track): # write ID3 data
    num_track = "%02d" % (track.index(),)
    artist = artist = ', '.join(a.name() for a in track.artists())
    album = track.album().name()
    title = track.name()
    year = track.album().year()
    
    if args.directory is True:
        directory = os.getcwd() + "/" + artist + "/" + album + "/"
        mp3file = title+".mp3"
    else:
        directory = os.getcwd() + "/"
        mp3file = artist + " - " + title + " - [ " + album + " ].mp3"
    #Removing invalid file characters
    mp3file = re.sub(r'[\\/:"*?<>|]+', ' ', mp3file)

    # download cover
    image = session.image_create(track.album().cover())
    while not image.is_loaded(): # does not work from MainThread!
        time.sleep(0.1)
    fh_cover = open('cover.jpg','wb')
    fh_cover.write(image.data())
    fh_cover.close()

    # write id3 data
    cmd = "eyeD3" + \
          " --add-image cover.jpg:FRONT_COVER" + \
          " -t \"" + title + "\"" + \
          " -a \"" + artist + "\"" + \
          " -A \"" + album + "\"" + \
          " -n " + str(num_track) + \
          " -Y " + str(year) + \
          " -Q " + \
          " \"" + directory + mp3file + "\""
    shell(cmd)
    print directory + mp3file + " written"
    # delete cover
    shell("rm -f cover.jpg")


def library_scan(path):

    print "Scanning " + path
    count = 0
    tree = lambda: collections.defaultdict(tree)
    musiclibrary = tree()
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.mp3'):
            filepath = os.path.join(root, filename )
            try:
                audiofile = eyed3.load(filepath)
                try:
                    artist=audiofile.tag.artist
                except AttributeError:
                    artist=""
                try:
                    album=audiofile.tag.album
                except AttributeError:
                    album=""
                try:
                    title=audiofile.tag.title
                except AttributeError:
                    title=""
                
                musiclibrary[artist][album][title]=filepath
                count += 1

            except Exception, e:
                print "Error loading " + filepath
                print e
    print str(count) + " mp3 files found"
    return musiclibrary
    
def library_track_exists(track):
    if musiclibrary == None:
        return False

    artist = artist = ', '.join(a.name() for a in track.artists())
    album = track.album().name()
    title = track.name()
    
    filepath = musiclibrary[artist][album][title]
    if filepath == {}:
        return False
    else:
        print "Skipping. Track found at " + filepath
        return True



class RipperThread(threading.Thread):
    def __init__(self, ripper):
        threading.Thread.__init__(self)
        self.ripper = ripper

    def run(self):
        # wait for container
        container_loaded.wait()
        container_loaded.clear()

        # create track iterator
        link = Link.from_string(args.url[0])
        if link.type() == Link.LINK_TRACK:
            track = link.as_track()
            itrack = iter([track])
        elif link.type() == Link.LINK_PLAYLIST:
            playlist = link.as_playlist()
            print('loading playlist ...')
            while not playlist.is_loaded():
                time.sleep(0.1)
            print('done')
            itrack = iter(playlist)

        # ripping loop
        session = self.ripper.session
        count = 0
        for track in itrack:
                count += 1
                print "Track " + str(count)
                if track.availability() != 1:
                    print 'Skipping. Track not available'
                else:
                    self.ripper.load_track(track)

                    if not library_track_exists(track):

                        rip_init(session, track)

                        self.ripper.play()

                        end_of_track.wait()
                        end_of_track.clear() # TODO check if necessary

                        rip_terminate(session, track)
                        rip_id3(session, track)

        self.ripper.disconnect()

class Ripper(Jukebox):
    def __init__(self, *a, **kw):
        Jukebox.__init__(self, *a, **kw)
        self.ui = RipperThread(self) # replace JukeboxUI
        self.session.set_preferred_bitrate(2) # 320 bps

    def music_delivery_safe(self, session, frames, frame_size, num_frames, sample_type, sample_rate, channels):
        rip(session, frames, frame_size, num_frames, sample_type, sample_rate, channels)
        #if playback:
        if args.playback:
            return Jukebox.music_delivery_safe(self, session, frames, frame_size, num_frames, sample_type, sample_rate, channels)
        else:
            return num_frames

    def end_of_track(self, session):
        Jukebox.end_of_track(self, session)
        end_of_track.set()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='jbripper',
        description='Rip Spotify songs',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''Example usage:
        rip a single file: ./jbripper.py -u user -p password -U spotify:track:52xaypL0Kjzk0ngwv3oBPR
        rip entire playlist: ./jbripper.py -u user -p password -U spotify:user:username:playlist:4vkGNcsS8lRXj4q945NIA4
        check if file exists before ripping: ./jbripper.py -u user -p password -U spotify:track:52xaypL0Kjzk0ngwv3oBPR -l ~/Music
        ''')
    parser.add_argument('-u','--user', nargs=1, required=True, help='spotify user')
    parser.add_argument('-p','--password', nargs=1, required=True, help='spotify password')
    parser.add_argument('-U','--url', nargs=1, required=True, help='spotify url')
    parser.add_argument('-l', '--library', nargs='?', help='music library path')
    parser.add_argument('-P', '--playback', action="store_true", help='set if you want to listen to the tracks that are currently ripped (start with "padsp ./jbripper.py ..." if using pulse audio)')
    parser.add_argument('-V', '--vbr', default="0", help='Lame VBR quality setting. Equivalent to Lame -V parameter. Default 0')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-f', '--file', default=True, action="store_true", help='Save output mp3 file with the following format: "Artist - Song - [ Album ].mp3" (default)')
    group.add_argument('-d', '--directory', default=False, action="store_true", help='Save output mp3 to a directory with the following format: "Artist/Album/Song.mp3"')

    args = parser.parse_args()
    #print args
    if args.library != None:
        musiclibrary = library_scan(args.library)
    ripper = Ripper(args.user[0],args.password[0]) # login
    ripper.connect()
    