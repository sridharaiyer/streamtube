import streamlit as st
import SessionState
import subprocess
import os
import re
from os.path import expanduser
import eyed3
import requests
import io
import youtube_dl

ydl_opts = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
}

home = expanduser("~")
MUSIC_DIR = os.path.join(home, 'Music')
if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)

progress_bar = None


@st.cache
def convert_sec_to_hms(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return f'{round(hour)}h:{round(min)}m:{round(sec)}s'


@st.cache(allow_output_mutation=True)
def get_yt_info(url):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def convert_to_mp3(url, output_filepath_mp3):
    base, ext = os.path.splitext(output_filepath_mp3)
    output_filepath_ytdl_ext = base + '.%(ext)s'
    subprocess.run(
        ['youtube-dl', '-f', 'bestaudio', '--restrict-filenames', '--extract-audio', '--audio-format', 'mp3', '-o',
         output_filepath_ytdl_ext, url])
    _set_ide3(output_filepath_mp3)


def _set_ide3(filepath_mp3):
    audiofile = eyed3.load(filepath_mp3)
    audiofile.initTag()
    audiofile.tag.artist = id3['Artist']
    audiofile.tag.genre = id3['Genre']
    audiofile.tag.album_artist = id3['Album Artist']
    audiofile.tag.album = id3['Album']
    audiofile.tag.composer = id3['Composer']
    audiofile.tag.images.set(3, img_url_to_bytes(id3['Image URL']).read(), 'image/jpeg')
    audiofile.tag.save()


@st.cache(allow_output_mutation=True)
def img_url_to_bytes(img_url):
    response = requests.get(img_url)
    return io.BytesIO(response.content)


genre_values = ('Alternative', 'Bhajans', 'BWW', 'Carnatic Fusion',
                'Carnatic Traditional', 'Shloka', 'Hindi Movie', 'Tamil Movie',
                'Kannada Movie', 'Kids English Songs', 'Lullaby', 'Meditation',
                'Pop', 'Tamil Rhymes', 'Rock', 'Tamil Stories', 'Upanyasam')

values_dict = {
    'url': '',
    'get_info_button': False,
    'yt': None,
    'img': None,
    'music_info': None,
    'genre': None,
    'artist': None,
    'album': None,
    'album_artist': None,
    'composer': None,
    'download_button': False
}

id3 = {}


def main():
    st.image('images/ytdl_image.png', use_column_width=True)
    session_state = SessionState.get(**values_dict)
    session_state.url = st.text_input("URL")

    if st.button("Get Info"):
        session_state.get_info_button = True

    if session_state.get_info_button:
        yt_info = get_yt_info(session_state.url)

        col1, col2 = st.beta_columns(2)
        col1.image(img_url_to_bytes(yt_info['thumbnail']), use_column_width=True)
        col2.subheader(f'{yt_info["title"]}\nDuration: {convert_sec_to_hms(yt_info["duration"])}')

        session_state.genre = st.selectbox('Select Genre:', options=genre_values)
        session_state.artist = st.text_input(label='Artist', value=yt_info['artist'])
        session_state.album = st.text_input(label='Album', value=yt_info['album'])
        session_state.album_artist = st.text_input(label='Album Artist', value=yt_info['artist'])
        session_state.composer = st.text_input(label='Composer')
        session_state.download_button = st.button('Download')

        id3['Genre'] = session_state.genre
        id3['Artist'] = session_state.artist
        id3['Album'] = session_state.album
        id3['Album Artist'] = session_state.album_artist
        id3['Composer'] = session_state.composer
        id3['Image URL'] = yt_info['thumbnail']

        if session_state.download_button:
            if not session_state.artist:
                st.error('Artist cannot be blank')
                session_state.download_button = False
            elif not session_state.album:
                st.error('Album cannot be blank')
                session_state.download_button = False
            elif not session_state.album_artist:
                st.error('Album Artist cannot be blank')
                session_state.download_button = False
            elif not session_state.composer:
                st.error('Composer cannot be blank')
                session_state.download_button = False

        if session_state.download_button:
            filename = re.sub(r'[^\x00-\x7f]', r'', yt_info["title"])  # Removing all non-ascii
            filename = re.sub('[^0-9a-zA-Z]+', '_', filename)  # Replacing all non-alpha-numeric with '_'
            output_filepath_mp3 = os.path.join(MUSIC_DIR, filename + '.mp3')
            if not os.path.exists(output_filepath_mp3):
                with st.spinner("MP3 downloading..."):
                    convert_to_mp3(session_state.url, output_filepath_mp3)
                if st.success('MP3 download complete!'):
                    st.warning('Refresh page to download another')
            else:
                if st.warning('MP3 file already exists'):
                    st.warning('Refresh page to download another')


main()
