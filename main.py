import sys
import json
import os
from urlparse import parse_qsl
from urllib import urlencode
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import inputstreamhelper
from requests_oauthlib import OAuth1Session

# NLZiet API and OAuth docs
# https://github.com/Wouter0100/nlziet-api/blob/master/README.md

# Specify DRM settings
PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36'

# Define keys
KEY_CHANNEL = '{{CHANNEL}}'
KEY_VOD = '{{VOD}}'
KEY_TOKEN = '{{TOKEN}}'

# Define requestable urls
CHANNEL_LIST_URL = 'https://api.nlziet.nl/v6/epg/channels'
USER_PLAYLISTS_URL = 'http://api.nlziet.nl/v6/userplaylists'
USER_FAVOURITES_SERIES_URL = 'https://api.nlziet.nl/v6/favorites/series'
CHANNEL_STREAM_URL = 'https://api.nlziet.nl/v6/stream/handshake/Widevine/dash/Live/'+KEY_CHANNEL+'?playerName=NLZIET%20Meister%20Player%20Web'
VOD_STREAM_URL = 'https://api.nlziet.nl/v6/stream/handshake/Widevine/dash/VOD/'+KEY_VOD+'?playerName=NLZIET%20Meister%20Player%20Web'
LOGIN_URL = "https://www.nlziet.nl/Account/AppLogin"
AUTHORIZE_URL = "https://www.nlziet.nl/OAuth/Authorize?oauth_token="+KEY_TOKEN
REQUEST_TOKEN_URL = 'https://www.nlziet.nl/OAuth/GetRequestToken'
ACCESS_TOKEN_URL = "http://www.nlziet.nl/OAuth/GetAccessToken"
CHANNEL_LOGO_URL = 'https://nlzietprodstorage.blob.core.windows.net/static/channel-logos/'+KEY_CHANNEL+'.png'
VOD_LOGO_URL = 'https://nlzietprodstorage.blob.core.windows.net/'


# Define some OAuth settings
OAUTH_CONSUMER_KEY = 'key'
OAUTH_CONSUMER_SECRET = 'secret'
OAUTH_CALLBACK = 'null'

# Define alerts
ALERT_SETUP = "Voor gebruik dien je eerst (via de configuratie) je accountgegevens in te stellen."
ALERT_LOGIN_ERROR = "Fout opgetreden tijdens inloggen, controleer accountgegevens."

# Create a OAuth session and set-up some settings
session = OAuth1Session(OAUTH_CONSUMER_KEY, client_secret=OAUTH_CONSUMER_SECRET, callback_uri=OAUTH_CALLBACK)

# Define logged in status
logged_in = False

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

# Get addon information
addon = xbmcaddon.Addon()

# Get user credentials
email = addon.getSetting('email')
password = addon.getSetting('password')

def have_credentials():
    """
    Check if there are credentials available.
    :return: Availibility of credentials
    :rtype: bool
    """
    return email and password

def get_credentials():
    """
    Get credentials.
    :return: Array of credentials
    :rtype: dict
    """
    return {
        "username": email,
        "password": password
    }

def is_logged_in():
    return logged_in

def set_logged_in():
    global logged_in
    logged_in = True

def login(credentials):
    """
    Log-in using credentials.
    :param credentials: Username and password
    :type credentials: dict
    """
    request = session.fetch_request_token(REQUEST_TOKEN_URL)
    session.post(LOGIN_URL, data=credentials)
    authorization_url = session.get(AUTHORIZE_URL.replace(KEY_TOKEN, request['oauth_token'])).url
    session.parse_authorization_response(authorization_url)

    try:
        session.fetch_access_token(ACCESS_TOKEN_URL)
        set_logged_in()
    except:
        show_dialog(ALERT_LOGIN_ERROR)
    
def write_serie_epsiodes_to_filecache(episodes):
    script_dir = os.path.dirname(__file__)
    cacheFile =os.path.join(script_dir,'resources/data/favourite_episodes.json')
    with open(cacheFile, 'w') as f:
        json.dump(episodes, f)

def get_serie_epsiodes_from_filecache():
    script_dir = os.path.dirname(__file__)
    cacheFile = os.path.join(script_dir,'resources/data/favourite_episodes.json')
    with open(cacheFile) as data_file:
        data_loaded = json.load(data_file)
    return data_loaded


def get_channel_stream(channel):
    """
    Get stream by channel name
    :param channel: URL friendly channel name
    :type channel: str
    :return: Stream information
    :rtype: types.GeneratorType
    """
    return session.get(CHANNEL_STREAM_URL.replace(KEY_CHANNEL, channel)).json()

def get_vod_stream(vod):
    """
    Get stream by vod item name
    :param channel: URL friendly channel name
    :type channel: str
    :return: Stream information
    :rtype: types.GeneratorType
    """
    return session.get(VOD_STREAM_URL.replace(KEY_VOD, vod)).json()
   
def get_channels():
    """
    Get list of channels.
    :return: List of channels
    :rtype: types.GeneratorType
    """
    return session.get(CHANNEL_LIST_URL).json()

def get_user_playlists():
    """
    Get list of user playlists.
    :return: List of playlists
    :rtype: types.GeneratorType
    """
    return session.get(USER_PLAYLISTS_URL).json()

def get_user_playlist(playlist_id):
    """
    Get list of user playlists.
    :return: List of playlists
    :rtype: types.GeneratorType
    """
    return session.get(USER_PLAYLISTS_URL + '/' + str(playlist_id)).json()

def get_user_favourites_series():
    """
    Get list of channels.
    :return: List of channels
    :rtype: types.GeneratorType
    """
    return session.get(USER_FAVOURITES_SERIES_URL).json()

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def main_menu():
    xbmcplugin.setContent(_handle, 'NLZiet')

    url = get_url(action='menu', menu_item='live')
    li = xbmcgui.ListItem('Live', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=_handle, url=url,
                                listitem=li, isFolder=True)

    url = get_url(action='menu', menu_item='favourites')
    li = xbmcgui.ListItem('Mijn Favorieten', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=_handle, url=url,
                                listitem=li, isFolder=True)
     
    xbmcplugin.endOfDirectory(_handle)

def favourites_menu():
    xbmcplugin.setContent(_handle, 'Favorieten')

    url = get_url(action='menu', menu_item='favourites_watchlater')
    li = xbmcgui.ListItem('Uitzendingen', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=_handle, url=url,
                                listitem=li, isFolder=True)
    
    url = get_url(action='menu', menu_item='favourites_series')
    li = xbmcgui.ListItem('Series', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=_handle, url=url,
                                listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(_handle)

def list_channels():
    """
    Create list of channels in the Kodi interface.
    """
    # Set plugin content.
    xbmcplugin.setContent(_handle, 'videos')

    # Get channels
    channels = get_channels()
   
    # Iterate through channels.
    for channel in channels:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=channel['Title'])

        # Set graphics
        list_item.setArt({'icon': CHANNEL_LOGO_URL.replace(KEY_CHANNEL, channel['UrlFriendlyName'])})

        # Set additional info for the list item.
        list_item.setInfo('video', {'title': channel['Title'], 'mediatype': 'video'})

        # Set 'IsPlayable' property to 'true'.
        list_item.setProperty('IsPlayable', 'true')

        # Create a URL for a plugin recursive call.
        url = get_url(action='play', channel=channel['UrlFriendlyName'])

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_favourites_watchlater():
    """
    Create list of playlist items in the Kodi interface.
    """
    # Set plugin content.
    xbmcplugin.setContent(_handle, 'watchlater')

    # Get userplaylists, select watchlater list
    #  user playlists: [{"Type": "WatchLater", "Id": 1, "Title": "Favorites"}, {"Type": "Watched", "Id": 2, "Title": "Bekeken"}]
    playlists = get_user_playlists()
    #xbmc.log(json.dumps(playlists))
    
    # Todo: Fix the const array position
    watchlaterList = get_user_playlist(playlists[0]['Id'])
    #xbmc.log(json.dumps(watchlaterList))
    
    # Iterate through watchlater items.
    for playlistitem in watchlaterList['Items']:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=playlistitem['ProgrammaTitel']+ ' ' +playlistitem['AfleveringTitel'])

        # Set graphics
        # fix: API reports incorrect image path /thumbnail/[image.jpg] this should be /thumbnails/[image.jpg]
        fixedLogoUrl = playlistitem['ProgrammaAfbeelding'].replace('thumbnail','thumbnails')
        list_item.setArt({'icon': VOD_LOGO_URL + fixedLogoUrl})

        # Set additional info for the list item.
        list_item.setInfo('video', {'title': playlistitem['ProgrammaTitel'], 'mediatype': 'video'})

        # Set 'IsPlayable' property to 'true'.
        list_item.setProperty('IsPlayable', 'true')

        # Create a URL for a plugin recursive call.
        url = get_url(action='playvod', vod=playlistitem['ContentId'])

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_favourites_series():
    """
    Create list of playlist items in the Kodi interface.
    """
    xbmcplugin.setContent(_handle, 'Favourite Series')
    favouriteSeries = get_user_favourites_series()
    episodes = list()

    # Iterate through watchlater items.
    for serie in favouriteSeries:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=serie['Titel'])

        # Set graphics
        # fix: API reports incorrect image path /thumbnail/[image.jpg] this should be /thumbnails/[image.jpg]
        fixedLogoUrl = serie['ProgrammaAfbeelding'].replace('thumbnail','thumbnails')
        list_item.setArt({'icon': VOD_LOGO_URL + fixedLogoUrl})

        # Set additional info for the list item.
        list_item.setInfo('video', {'title': serie['Titel'], 'mediatype': 'video'})

        # Set 'IsPlayable' property to 'true'.
        list_item.setProperty('IsPlayable', 'false')

        xbmc.log(json.dumps(serie))
        
        #create custom episodes dictionary
        for nlZietEpisode in serie['Items']:
            episode = {
                'contentId': nlZietEpisode['ContentId'],
                'title': nlZietEpisode['ProgrammaTitel'].encode("utf-8"),
                'tvshowtitle': nlZietEpisode['AfleveringTitel'].encode("utf-8"),
                'season': nlZietEpisode['SeizoenVolgnummer'],
                'premiered': nlZietEpisode['Uitzenddatum'].encode("utf-8"),
                'duration': nlZietEpisode['Duur'],
                # fix: API reports incorrect image path /thumbnail/[image.jpg] this should be /thumbnails/[image.jpg]
                'icon' :  nlZietEpisode['ProgrammaAfbeelding'].replace('thumbnail','thumbnails')
                }
            episodes.append(episode)

        write_serie_epsiodes_to_filecache(episodes)
             
        # Create a URL for a plugin recursive call.
        url = get_url(action='menu', menu_item='favourites_series_list_episodes',serietitle=episode['title'])

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(handle=_handle, url=url, listitem=list_item, isFolder=True)

    # Finish creating a virtual folder.

    xbmcplugin.endOfDirectory(_handle)
    xbmc.log("end of fav series - HANDLE IS:" + str(_handle))

def list_serie(serieTitle):
    """
    Create list of episodes in the Kodi interface.
    """
    # Set plugin content.
    xbmcplugin.setContent(_handle, 'tvshows')
    
    episodes = get_serie_epsiodes_from_filecache()
    
    # Iterate through episodes.
    for episode in episodes:
        if episode['title'] != serieTitle:
            continue
        xbmc.log("Serie found: " + serieTitle)
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=episode['title'])

        # Set graphics
        list_item.setArt({'icon': VOD_LOGO_URL + episode['icon']})

        # Set additional info for the list item.
        list_item.setInfo('video', {
            'mediatype': 'tvshow',
            'title': episode['title'], 
            'tvshowtitle': episode['tvshowtitle'],
            'season': episode['season'],
            'premiered': episode['premiered'],
            'duration': episode['duration']
           })

        # Set 'IsPlayable' property to 'true'.
        list_item.setProperty('IsPlayable', 'false')

        # Create a URL for a plugin recursive call.
        url = get_url(action='playvod', vod=episode['contentId'])

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play(channel):
    """
    Play channel by the provided name.
    :param channel: URL friendly channel name
    :type channel: str
    """
    stream = get_channel_stream(channel)

    is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
    if is_helper.check_inputstream():
        playitem = xbmcgui.ListItem(path=stream['uri'])
        playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        playitem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
        playitem.setProperty('inputstream.adaptive.license_type', DRM)
        playitem.setProperty('inputstream.adaptive.license_key', stream['drmConfig']['widevine']['drmServerUrl'] + '|Content-Type=&User-Agent='+USER_AGENT+'|R{SSM}|')
        xbmcplugin.setResolvedUrl(_handle, True, listitem=playitem)

def play_vod(vod):
    """
    Play vod item by the provided name.
    :param channel: URL friendly vod item name
    :type channel: str
    """
    stream = get_vod_stream(vod)
   
    is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
    if is_helper.check_inputstream():
        playitem = xbmcgui.ListItem(path=stream['uri'])
        playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        playitem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
        playitem.setProperty('inputstream.adaptive.license_type', DRM)
        playitem.setProperty('inputstream.adaptive.license_key', stream['drmConfig']['widevine']['drmServerUrl'] + '|Content-Type=&User-Agent='+USER_AGENT+'|R{SSM}|')
        xbmcplugin.setResolvedUrl(_handle, True, listitem=playitem)

def show_dialog(text):
    """
    Show a dialog with a provided string.
    :param text: Notification text
    :type text: str
    """
    xbmcgui.Dialog().ok(addon.getAddonInfo('name'), text)

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    params = dict(parse_qsl(paramstring))
    xbmc.log("###PARAMSTRING###" +paramstring)
    if params:
        if params['action'] == 'play':
            play(params['channel'])
        if params['action'] == 'playvod':
            play_vod(params['vod'])
        if params['action'] == 'menu':
            if params['menu_item'] == 'live':
                list_channels()
            elif params['menu_item'] == 'favourites':
                favourites_menu()
            elif params['menu_item'] == 'favourites_watchlater':
                    list_favourites_watchlater()
            elif params['menu_item'] == 'favourites_series':
                    list_favourites_series()
            elif params['menu_item'] == 'favourites_series_list_episodes':
                    list_serie(params['serietitle'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        main_menu()

if __name__ == '__main__':
    # Check if user has configured its credentials
    if not have_credentials():
        show_dialog(ALERT_SETUP)
    else:
        # Check if user is logged in
        if not logged_in:

            # Login using provided username and password
            login(get_credentials())

        # Call the router function and pass the plugin call parameters to it.
        # We use string slicing to trim the leading '?' from the plugin call paramstring
        router(sys.argv[2][1:])
