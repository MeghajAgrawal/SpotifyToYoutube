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
    all_song = sp.current_user_saved_tracks(limit=5,offset=10)['items']
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
    pass

@app.route('/youtubePlaylistGeneration')
def youtubePlaylistGeneration():
    return 'generating youtube playlist'
