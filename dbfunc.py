import config
import MySQLdb as Mdb


def get_connection():
    con = Mdb.connect(config.db_address, config.db_login, config.db_password, config.db_database)
    cur = con.cursor(Mdb.cursors.DictCursor)
    return con, cur


def destroy_db():
    con, cur = get_connection()
    cur.execute("DROP TABLE IF EXISTS maps")
    cur.execute("DROP TABLE IF EXISTS matches")
    cur.execute("DROP TABLE IF EXISTS player_scores")
    con.commit()


def create_db():
    con, cur = get_connection()
    cur.execute("CREATE TABLE IF NOT EXISTS maps(Id INT PRIMARY KEY AUTO_INCREMENT,\
                                                    mapname TEXT,\
                                                    score int(3),\
                                                    team_id int(3))")

    cur.execute("CREATE TABLE IF NOT EXISTS matches(Id INT PRIMARY KEY AUTO_INCREMENT,\
                                                    server_id int(1),\
                                                    team1 int(3),\
                                                    team2 int(3),\
                                                    team1_score int(3),\
                                                    team2_score int(3),\
                                                    team1_color TEXT,\
                                                    team2_color TEXT,\
                                                    map_id int(3),\
                                                    current tinyint(1))")

    cur.execute("CREATE TABLE IF NOT EXISTS player_scores(player_id int(3),\
                                                          match_id int(3),\
                                                          kills int(3),\
                                                          deaths int(3),\
                                                          caps int(3),\
                                                          ingame tinyint(1))")

    cur.execute("CREATE TABLE IF NOT EXISTS teams(Id INT PRIMARY KEY AUTO_INCREMENT,\
                                                  tag TEXT,\
                                                  name TEXT,\
                                                  roster_dplogin TEXT)")

    con.commit()


def add_match(server_id, team1, team2, team1_color, team2_color, map_id):
    con, cur = get_connection()
    cur.execute("INSERT INTO matches(server_id,\
                                     team1,\
                                     team2,\
                                     team1_score,\
                                     team2_score,\
                                     team1_color,\
                                     team2_color,\
                                     map_id,\
                                     current)\
                                     VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                     (server_id, team1, team2, 0, 0, team1_color, team2_color, map_id, 0))
    con.commit()
    return cur.lastrowid


def add_scores(match_id, player_id):
    con, cur = get_connection()
    cur.execute("SELECT * FROM player_scores WHERE player_id = %s AND match_id = %s", (player_id, match_id))
    if len(cur.fetchall()) == 0:
        cur.execute("INSERT INTO player_scores(player_id, match_id, kills, deaths, caps) VALUES(%s, %s, %s, %s, %s)",
                                                                                    (player_id, match_id, 0, 0, 0))
        con.commit()


def add_map(mapname, team_id):
    con, cur = get_connection()
    cur.execute("INSERT INTO maps(mapname, score, team_id) VALUES(%s, %s, %s)", (mapname, 20, team_id))
    con.commit()

def give_map(team_id, mapname):
    con, cur = get_connection()
    print (team_id, mapname)
    cur.execute("UPDATE maps SET team_id = %s WHERE mapname = %s", (team_id, mapname))
    con.commit()

def map_defended(mapname):
    con, cur = get_connection()
    cur.execute("SELECT * FROM maps WHERE mapname = %s", mapname)
    score = cur.fetchall()['score']
    cur.execute("UPDATE maps SET score = %s WHERE mapname = %s", (score+20, mapname))
    con.commit()

def increase_player_score(match_id, player_id, score_label):
    con, cur = get_connection()
    cur.execute("SELECT * FROM player_scores WHERE player_id = %s AND match_id = %s", (player_id, match_id))
    cur.execute("UPDATE player_scores SET {score_label} = %s WHERE player_id = %s AND match_id = %s"
                .format(score_label=score_label),
                ((cur.fetchall()[0][score_label])+1, player_id, match_id))
    con.commit()


def set_current(match_id, current):
    con, cur = get_connection()
    cur.execute("UPDATE matches SET current = %s WHERE Id = %s", (match_id, current))
    con.commit()


def set_scores(match_id, team1_score, team2_score):
    con, cur = get_connection()
    cur.execute("UPDATE matches SET team1_score = %s, team2_score = %s WHERE Id = %s",
                                                                                (team1_score, team2_score, match_id))
    con.commit()


def set_ingame(match_id, player_id, ingame):
    con, cur = get_connection()
    cur.execute("UPDATE player_scores SET ingame = %s WHERE player_id = %s AND match_id = %s",
                                                                                        (ingame, player_id, match_id))
    con.commit()

def get_team(team_id):
    con, cur = get_connection()
    cur.execute("SELECT * FROM teams WHERE Id = %s", team_id)
    ret=cur.fetchall()[0]
    ret['roster_dplogin']=ret['roster_dplogin'].split(',')
    return ret

def get_match(server_id):
    con, cur = get_connection()
    cur.execute("SELECT * FROM matches WHERE server_id = %s AND current = 0", server_id)
    response = cur.fetchall()
    if len(response) > 0:
        return response[0]
    else:
        return None

def get_map(map_id):
    con, cur = get_connection()
    cur.execute("SELECT * FROM maps WHERE Id = %s", map_id)
    return cur.fetchall()[0]


print "init"
destroy_db()
create_db()
add_map("airtime", 1)
add_map("shazam33", 2)
matchid = add_match(0, 1, 5, "", "", 1)
# increment_player_score(0, matchid, "kills")
# set_scores(matchid, 0, 69)