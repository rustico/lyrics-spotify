import dbus
from urllib.parse import quote_plus
import time
import curses
import threading
import requests
from bs4 import BeautifulSoup


def get_spotify_song_data():
    session_bus = dbus.SessionBus()

    spotify_bus = session_bus.get_object(
        "org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    spotify_properties = dbus.Interface(
        spotify_bus, "org.freedesktop.DBus.Properties")
    metadata = spotify_properties.Get(
        "org.mpris.MediaPlayer2.Player", "Metadata")

    title = metadata['xesam:title'].encode(
        'utf-8').decode('utf-8').replace("&", "&amp;")
    artist = metadata['xesam:artist'][0].encode(
        'utf-8').decode('utf-8').replace("&", "&amp;")
    return {'title': title, 'artist': artist}


def get_lyrics(song_name):
    song_name += ' metrolyrics'
    name = quote_plus(song_name)
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11'
           '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}

    url = 'http://www.google.com/search?q=' + name

    result = requests.get(url, headers=hdr).text
    link_start = result.find('http://www.metrolyrics.com')

    if(link_start == -1):
        return("Lyrics not found on Metrolyrics")

    link_end = result.find('html', link_start + 1)
    link = result[link_start:link_end + 4]

    lyrics_html = requests.get(link, headers={
                               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel'
                               'Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, '
                               'like Gecko) Chrome/55.0.2883.95 Safari/537.36'
                               }
                               ).text

    soup = BeautifulSoup(lyrics_html, "lxml")
    raw_lyrics = (soup.findAll('p', attrs={'class': 'verse'}))
    try:
        final_lyrics = unicode.join(u'\n', map(unicode, raw_lyrics))
    except NameError:
        final_lyrics = str.join(u'\n', map(str, raw_lyrics))

    final_lyrics = (final_lyrics.replace('<p class="verse">', '\n'))
    final_lyrics = (final_lyrics.replace('<br/>', ' '))
    final_lyrics = final_lyrics.replace('</p>', ' ')

    return (final_lyrics)


pos = 0


def spotify_thread(stdscr, pad):
    global pos

    old_song = ''
    while True:
        height, width = stdscr.getmaxyx()
        song = get_spotify_song_data()
        title = '{} - {}'.format(song['title'], song['artist'])
        if old_song != title:
            pos = 0
            old_song = title
            lyrics = get_lyrics(title)
            pad.clear()
            pad.addstr(title,  curses.A_BOLD)
            pad.addstr(lyrics)
            pad.refresh(0, 0, 0, 0, height - 1, width)

        time.sleep(1)


def get_spotify_lyrics(stdscr):
    global pos
    curses.init_color(0, 0, 0, 0)

    height, width = stdscr.getmaxyx()
    pad_height = 100
    pad = curses.newpad(pad_height, width)
    pad.scrollok(True)

    thread = threading.Thread(target=spotify_thread, args=(stdscr, pad))
    thread.daemon = True
    thread.start()

    running = True
    while running:
        ch = pad.getch()
        height, width = stdscr.getmaxyx()

        if ch < 256 and chr(ch) == 'k' and pos > 0:
            pos -= 10
            pad.refresh(pos, 0, 0, 0, height - 1, width)
        elif ch < 256 and chr(ch) == 'j' and pos < pad_height - height:
            pos += 10
            pad.refresh(pos, 0, 0, 0, height - 1, width)
        elif ch < 256 and chr(ch) == 'q':
            running = False


def main():
    curses.wrapper(get_spotify_lyrics)


if __name__ == "__main__":
    main()
