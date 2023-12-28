from flask import Flask, request, url_for, session, redirect
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pickle
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = "Sdcjhe3463vuebc"
app.config['SESSION_COOKIE_NAME'] = 'SpotMyData'
TOKEN_INFO = "token_info"

load_dotenv('.env')

credentials = None
all_song = []

YOUTUBE_API_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
playlist_id = ""

@app.route('/')
def login():
    sp_oauth = create_spotify_OAuth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_OAuth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getTracks',_external = True))

@app.route('/getTracks')
def getTracks():
    global all_song
    try:
        token_info = get_token()
    except:
        print('user not logged in')
        return redirect(url_for("login", _external=False))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    all_song = []
    #while True:
    #    items = sp.current_user_saved_tracks(limit=50,offset=iter * 50)['items']
    #    iter +=1
    #    all_song += items
    #    if(len(items) < 50):
    #        break
    all_song = sp.current_user_saved_tracks(limit=5,offset=18)['items']
    return redirect(url_for('youtubeRedirect',_external = False))

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        sp_oauth = create_spotify_OAuth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_OAuth():
    return SpotifyOAuth(
        client_id =os.getenv('CLIENT_ID'),
        client_secret = os.getenv('CLIENT_SECRET'),
        redirect_uri = url_for('redirectPage', _external = True),
        scope="user-library-read")

@app.route('/youtubeRedirect')
def youtubeRedirect():
    global credentials
    if os.path.exists('token.pickle'):
        print('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing Access Token...')
            credentials.refresh(Request())
        else:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=[
                'https://www.googleapis.com/auth/youtube'
            ]
            )
            flow.run_local_server()
            credentials = flow.credentials

        # Save the credentials for the next run
            with open('token.pickle', 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)
        
    return redirect(url_for('youtubePlaylistGeneration',_external = False))


def youtubePlaylistCheck():
    global playlist_id
    youtube = build(YOUTUBE_API_NAME,YOUTUBE_API_VERSION,credentials=credentials)
    request = youtube.playlists().list(part="snippet",mine= True)
    response = request.execute()
    for item in response['items']:
        if item["snippet"]["title"] == "Music":
            playlist_id = item['id']
            print(playlist_id)
            return True
    return False

@app.route('/youtubePlaylistGeneration')
def youtubePlaylistGeneration():
    if not youtubePlaylistCheck():
        youtube = build(YOUTUBE_API_NAME,YOUTUBE_API_VERSION,credentials=credentials)
        request = youtube.playlists().insert(
            part = "snippet,status",
            body = {
                "snippet":{
                    "title": "Music"
                },
                "status": {
                    "privacyStatus": "private"
                }
            }
        )
        response = request.execute()
    return redirect(url_for('youtubeAddSongs',_external = True))

def checkPlaylistforSong():
    youtube = build(YOUTUBE_API_NAME,YOUTUBE_API_VERSION,credentials=credentials)
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=50,
        playlistId=playlist_id
    )
    response = request.execute()
    playlist_items = []
    for items in response["items"]:
        playlist_items.append(items["snippet"]["title"])
    return playlist_items

def searchYoutubeforSong(song_name):
    print("Searching Song")
    youtube = build(YOUTUBE_API_NAME,YOUTUBE_API_VERSION,credentials=credentials)
    request = youtube.search().list(
        part="snippet",
        maxResults=25,
        q=song_name
    )
    response = request.execute()
    for items in response["items"]:
        if items["id"]["kind"] == "youtube#video":
            return items["id"]
    #return response["items"][0]["id"]

@app.route("/youtubeAddSongs")
def youtubeAddSongs():
    playlist_items = checkPlaylistforSong()
    #print(playlist_items)
    for item in all_song:
        if any(item["track"]["name"] in s for s in playlist_items):
            continue
        else:
            search_string = item["track"]["name"] +" "+ item["track"]["artists"][0]["name"]
            print(search_string)
            id = searchYoutubeforSong(search_string)
            try:
                youtube = build(YOUTUBE_API_NAME,YOUTUBE_API_VERSION,credentials=credentials)
                request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                    "resourceId": {
                        "kind": id["kind"],
                        "videoId": id["videoId"]
                        }
                    }
                }
                )
                response = request.execute()
            except:
                print("Error for "+search_string)
                continue
    return "Done"
