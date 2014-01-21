spotifyripper
=============

small ripper script for spotify (rips playlists to mp3 and includes ID3 tags and album covers) 

note that stream ripping violates the ToC's of libspotify!

    usage: jbripper [-h] -u USER -p PASSWORD -U URL [-l [LIBRARY]] [-P] [-V VBR]
                    [-f | -d]

    Rip Spotify songs

    optional arguments:
      -h, --help            show this help message and exit
      -u USER, --user USER  spotify user
      -p PASSWORD, --password PASSWORD
                            spotify password
      -U URL, --url URL     spotify url
      -l [LIBRARY], --library [LIBRARY]
                            music library path
      -P, --playback        set if you want to listen to the tracks that are currently ripped (start with "padsp ./jbripper.py ..." if using pulse audio)
      -V VBR, --vbr VBR     Lame VBR quality setting. Equivalent to Lame -V parameter. Default 0
      -f, --file            Save output mp3 file with the following format: "Artist - Song - [ Album ].mp3" (default)
      -d, --directory       Save output mp3 to a directory with the following format: "Artist/Album/Song.mp3"

    Example usage:
            rip a single file: ./jbripper.py -u user -p password -U spotify:track:52xaypL0Kjzk0ngwv3oBPR
            rip entire playlist: ./jbripper.py -u user -p password -U spotify:user:username:playlist:4vkGNcsS8lRXj4q945NIA4
            check if file exists before ripping: ./jbripper.py -u user -p password -U spotify:track:52xaypL0Kjzk0ngwv3oBPR -l ~/Music

features
    - real-time VBR ripping from spotify PCM stream
    - writes id3 tags (including album cover)

prerequisites:
    - libspotify (download at https://developer.spotify.com/technologies/libspotify/)
    - pyspotify (sudo pip install -U pyspotify)
    - spotify appkey (download at developer.spotify.com, requires premium!)
    - jukebox.py (pyspotify example)
    - lame
    - eyeD3 (pip install eyeD3)

TODO
- detect if other spotify instance is interrupting
. add album supprt : spotify:album:1UnRYaeCev9JVKEHWBEgHe