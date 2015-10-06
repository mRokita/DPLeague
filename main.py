from pypb2lib import *
import config
import dbfunc as db
from random import shuffle
from time import sleep

class Data:
    def __init__(self):
        pass


def on_elim(arg, server):
    if data.match_started < 3:
        return # zakończ jeśli mecz nie został rozpoczęty
    global data
    db.increase_player_score(data.match_id, server.GetID(arg['player1']), "kills")
    db.increase_player_score(data.match_id, server.GetID(arg['player2']), "deaths")
    update_scores()

def update_scores():
    # aktualizacja wyników w bazie danych
    global data
    scores = main_server.Scores()
    data.team1_score = scores[data.team1_color]
    data.team2_score = scores[data.team2_color]
    db.set_scores(data.match_id, data.team1_score, data.team2_score)

def on_cap(arg, server):
    if data.match_started < 3:
        return
    global data
    db.increase_player_score(data.match_id, server.GetID(arg['player']), "caps")
    update_scores()


def on_eliminated_teams_flag(arg, server):
    update_scores()


def on_join(arg, server):
    global data
    player_id = server.GetID(arg['player'])
    if (not player_id) or (player_id not in data.team1_roster) and (player_id not in data.team2_roster):
        server.rcon("sv forcejoin %s observer" % server.GetPlayersIngameID(arg['player']))
    if (player_id in data.team1_roster) and arg['team'] == data.team2_color:
        server.rcon("sv forcejoin %s %s" % (server.GetPlayersIngameID(arg['player']), data.team1_color))
    if (player_id in data.team2_roster) and arg['team'] == data.team1_color:
        server.rcon("sv forcejoin %s %s" % (server.GetPlayersIngameID(arg['player']), data.team2_color))


def on_mapchange(arg, server):
    global data
    if data.match_started == 1:
        data.colors = server.Scores().keys()
        shuffle(data.colors)
        data.team1_color = data.colors[0]
        data.team2_color = data.colors[1]
        data.match_started = 2
    if data.match_started == 3: # zakończenie meczu i dodanie danych do bazy
        if data.team1_score > data.team2_score:
            main_server.rcon("sv newmap pbcup")
            db.set_current(data.match_id, 3)
            db.give_map(data.team1_id, data.map_info['mapname'])
            default_vars()
            sleep(8)
            main_server.Say("{C}B%s gets the map." % data.team1_info['name'])
        else:
            main_server.rcon("sv newmap pbcup")
            db.set_current(data.match_id, 3)
            db.map_defended(data.map_info['mapname'])
            default_vars()
            sleep(8)
            main_server.Say("{C}B%s defended the map. +20 points." % data.team1_info['name'])

def on_roundstarted(arg, server):
    global data
    teams = main_server.Teams()
    if data.match_started == 3: # Inicjalizacja analizy błędów w balansie teamów
        players = main_server.rcon_players()
        for player in players:
            if (player['id'] in teams[data.team1_color]) or (player['id'] in teams[data.team2_color]):
                db.add_scores(data.match_id, player['dplogin'])
    if ((data.team1_color not in teams) # Szukanie błędów w balansie teamów
        or (data.team2_color not in teams)
        or (len(teams[data.team1_color]) != config.league_type)
        or (len(teams[data.team2_color]) != config.league_type)):
            if data.match_started == 2:
                main_server.Say("{C}BERROR: Teams aren't {n} vs {n}. Restarting...".format(n=config.league_type))
                main_server.rcon("map " + data.map_info['mapname'])
            elif data.match_started == 3:
                if data.wrong_rounds < config.league_max_wrong_rounds:
                    main_server.Say("{C}BERROR: Teams aren't {n} vs {n}.".format(n=config.league_type))
                    main_server.Say("{C}BMatch is going to end after {l} rounds."
                                    .format(l=(config.league_max_wrong_rounds-data.wrong_rounds)))
                    data.wrong_rounds += 1
                else:
                    if len(teams[data.team1_color]) > len(teams[data.team2_color]):
                        main_server.Say("{C}B%s gets the map by a forfeit" % data.team1_info['name'])
                        main_server.rcon("sv newmap pbcup")
                        db.set_current(data.match_id, 3)
                        db.give_map(data.team1_id, data.map_info['mapname'])
                    elif len(teams[data.team1_color]) < len(teams[data.team2_color]):
                        main_server.Say("{C}B%s defends the map by a forfeit" % data.team1_info['name'])
                        main_server.rcon("sv newmap pbcup")
                        db.set_current(data.match_id, 3)
                        db.map_defended(data.map_info['mapname'])
                    elif len(teams[data.team1_color]) == len(teams[data.team2_color]):
                        main_server.Say("{C}Match canceled." % data.team1_info['name'])
                        db.set_current(data.match_id, 4)
                    default_vars()
    else:
        if not data.match_started == 3: #Rozpoczecie meczu
            data.match_started = 3
            main_server.Say("{C}BMatch started!")
            db.set_current(data.match_id, 2)
            players = main_server.rcon_players()
            for player in players:
                if (player['id'] in teams[data.team1_color]) or (player['id'] in teams[data.team2_color]):
                    db.add_scores(data.match_id, player['dplogin'])
        data.wrong_rounds = 0


def on_entered(arg, server):
    global data
    data.match = db.get_match(config.server_id)
    if data.match and data.match_started == 0: # Initializacja teamow, uruchomienie mapy
        data.wrong_rounds = 0
        data.team1_id = data.match['team1']
        data.team2_id = data.match['team2']
        data.team1_score = 0
        data.team2_score = 0
        data.team1_info = db.get_team(data.team1_id)
        data.team2_info = db.get_team(data.team2_id)
        data.team1_roster = data.team1_info['roster_dplogin']
        data.team2_roster = data.team2_info['roster_dplogin']
        data.team1_color = ""
        data.team2_color = ""
        data.match_id = data.match['Id']
        data.map_id = data.match['map_id']
        data.map_info = db.get_map(data.map_id)
        if not data.match_started:
            main_server.Say("{C}BMatch: %s is defending %s from %s" %
                            (data.team1_info['name'], data.map_info['mapname'], data.team2_info['name']))
            main_server.rcon("sv newmap %s" % data.map_info['mapname'])
            data.match_started = 1
        db.set_current(data.match['Id'], 1)

    if data.match_started == 2:
        main_server.Say("{C}BTeams: %s - %s, %s - %s" %
                        (data.team1_info['tag'], data.team1_color, data.team2_info['tag'], data.team2_color))


def default_vars():
    # Domyślne zmienne dla serwera
    global data
    data.match = {} # Dane o aktualnym meczu
    data.wrong_rounds = 0 # Złe rundy - rundy z niezbalansowanymi zespołami itp. 
    data.match_started = 0 # Czy mecz rozpoczęty - 0 nie - 1 wybrano kolory 2- ? 3-rozpoczęto mecz, statystyki aktywne
    data.team1_id = None	# ID z bazy danych dla teamow
    data.team2_id = None
    data.team1_color = None # Kolor teamu - niebieski, czerwony, żółty lub fioletowy
    data.team2_color = None
    data.team1_score = 0 # Punkty teamu
    data.team2_score = 0
    data.team1_roster = [] # Skład teamu [zbudowany z ID graczy w bazie]
    data.team2_roster = []
    data.map_info=[] # info o mapie
    data.map_id=None # ID mapy w bazie


if __name__ == "__main__":
    # Stworzenie obiektu typu Server (pypb2lib.Server) z parametrami z configa
    main_server = Server(hostname=config.server_hostname,
                         rcon_password=config.server_rconpassword,
                         port=config.server_port,
                         logfile=config.server_logfile)
    # Bindowanie do zdarzeń
    data=Data()
    default_vars()
    main_server.Bind(EVT_ENTERED, on_entered)
    main_server.Bind(EVT_JOIN, on_join)
    main_server.Bind(EVT_MAPCHANGE, on_mapchange)
    main_server.Bind(EVT_ROUNDSTARTED, on_roundstarted)
    main_server.Bind(EVT_ELIM, on_elim)
    main_server.Bind(EVT_CAP, on_cap)
    main_server.Bind(EVT_ELIMINATED_TEAMS_FLAG, on_eliminated_teams_flag)
    running = True
    while running:
        try:
            raw_input()
        except:
            main_server.destroy()
            running = False
