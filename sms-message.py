import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import date, datetime
import calendar

# Nba imports------------------------------------------------------------------------------------------------------------------------
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder, playerdashboardbylastngames, playergamelog, teamplayerdashboard, teamgamelog
from nba_api.stats.static import players
# ----------------------------------------------------------------------------------------------------------------------------------

# Stocks imports---------------------------------------------------------------------------------------------------------------------
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from matplotlib.pyplot import figure
# ----------------------------------------------------------------------------------------------------------------------------------

# Twilio import---------------------------------------------------------------------------------------------------------------------
from twilio.rest import Client
# ----------------------------------------------------------------------------------------------------------------------------------

def getNbaScore():
    nba_teams = teams.get_teams()
    raptors = [team for team in nba_teams if team['abbreviation'] == 'TOR'][0]
    raptors_id = raptors['id']

    rapsGames = teamgamelog.TeamGameLog(team_id= raptors_id, season_all="2018-19", season_type_all_star='Regular Season')
    mostRecentGame = pd.DataFrame(rapsGames.get_data_frames()[0]).iloc[0]
    gameId = mostRecentGame['Game_ID']
    matchup = mostRecentGame['MATCHUP']
    win = mostRecentGame['WL']
    wins = mostRecentGame['W']
    losses = mostRecentGame['L']
    torScore = mostRecentGame['PTS']

    gamesResult = leaguegamefinder.LeagueGameFinder()
    all_games = gamesResult.get_data_frames()[0]
    opponentGame = all_games[all_games.GAME_ID == gameId]
    opponentGame = opponentGame[opponentGame['TEAM_ABBREVIATION'] != 'TOR'].iloc[0]
    opponentScore = opponentGame['PTS']
    gameDate = getDay(opponentGame['GAME_DATE'])


    statsResult = teamplayerdashboard.TeamPlayerDashboard(team_id = raptors_id, last_n_games = 1)
    playerStats = pd.DataFrame(statsResult.get_data_frames()[1])
    key_player = playerStats.sort_values(by=['PTS'], ascending=False).iloc[0]
    key_player_name = key_player['PLAYER_NAME']
    key_player_pts = key_player['PTS']
    key_player_ast = key_player['AST']
    key_player_reb = key_player['REB']

    return "Latest Game from {}: {}\nThe Raps took a {} making their record {}W / {}L \nScore: {} : {}\nKey Player: {}\nStats:\n\tPoints: {}\n\tAssists: {}\n\tRebounds: {}".format(gameDate,matchup,win, wins, losses,torScore,opponentScore,key_player_name,key_player_pts,key_player_ast, key_player_reb)


def getStocks(key):
    ts = TimeSeries(key, output_format='pandas')
    ti = TechIndicators(key)
    shop_data, shop_meta_data = ts.get_daily(symbol='SHOP')
    last30 = shop_data.iloc[:21]
    open = shop_data['1. open'][0]
    close = shop_data['4. close'][0]
    date = getDay(str(shop_data.index.values[0])[:10])
    closeDayBefore = shop_data['4. close'][1]
    delta = round(close - closeDayBefore, 2)


    # sns.set(style='darkgrid')
    # ax = sns.lineplot(data = last30['4. close'],hue="species",style="smoker")
    # plt.xticks(rotation=45)
    # plt.tight_layout()
    # sns_ploy.savefig('output.png')

    return "SHOP data as of {}:\n\tOpen: {}\n\tClose: {}\n\tPrice Delta(2 days): {}".format(date, open, close, delta)



def getDay(date1):
    dates = date1.split('-')
    d = date(int(dates[0]), int(dates[1]), int(dates[2]))
    return (calendar.day_name[d.weekday()] + " " + d.strftime('%B') + " " + d.strftime('%d'))

def extract_info_from_json(resp):

    city     = resp['name']
    temp     = resp['main']['temp']
    wind_spd = resp['wind']['speed']
    desc     = resp['weather'][0]['description']
    return city, temp, wind_spd, desc

def send_sms(to_phone_number, msg_body, TWILIO_SID, TWILIO_KEY, from_phone_number='+15555555555'):
    """Send an sms with msg_body to to_phone_number
    Using your Twilio credentials, send an sms with msg_body to to_phone_number.
    The TWILIO_SID, TWILIO_KEY, and from_phone_number are all set parameters
    that can be obtained from the Twilio website.
    Parameters
    ----------
    to_phone_number: str
        The phone number you wish to send a message to written in E.164 format
    msg_body: str
        The string that you want to send to to_phone_number
    TWILIO_SID:
        Your Twilio ID
    TWILIO_KEY: str
        The Twilio key associated with that ID
    from_phone_number: str
        A valid Twilio number assigned under the SID. Must be written in E.164 format
    Returns
    -------
    None
    """
    client = Client(TWILIO_SID, TWILIO_KEY)
    client.messages.create(body=msg_body, from_=from_phone_number, to=to_phone_number)

def get_weather_dictionary(api_key, city_id='6176823'):
    payload = {'id': city_id, 'appid': api_key, 'units': 'metric'}

    raw_resp = requests.get('http://api.openweathermap.org/data/2.5/weather', params=payload)
    resp = raw_resp.json()
    return resp

if __name__ == '__main__':
    TWILIO_SID = 'insert-key'
    TWILIO_KEY = 'insert-key'
    OPENWEATHER_KEY = 'insert-key'
    ALPHA_KEY = 'insert-key'

    nbaMessage = getNbaScore()
    stockMessage = getStocks(ALPHA_KEY)

    resp = get_weather_dictionary(OPENWEATHER_KEY)
    city, temp, wind_spd, desc = extract_info_from_json(resp)
    msg_break  = "---------------------------"
    msg_body = "Good morning Emilio\nWeather for {},ON\n\tTemp: {} C\n\tWind Speed: {} m/s\n\tDesc: {}".format(city,temp,wind_spd,desc) + "\n" + msg_break + "\n" + nbaMessage + "\n" + msg_break +"\n" + stockMessage

    to_phone_number = '+insert-number'
    from_phone_number = '+insert-number'
    print(msg_body)

    send_sms(to_phone_number, msg_body, TWILIO_SID, TWILIO_KEY, from_phone_number)

