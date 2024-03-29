import datetime
from  global_variables import sql,database



#Table of teams (team, id, url)
sql.execute("""CREATE TABLE IF NOT EXISTS teams (
team TEXT,
id INTEGER,
url TEXT,
UNIQUE(team),
UNIQUE(id)
)""")
database.commit()

#Table of users ( id , team)
sql.execute("""CREATE TABLE IF NOT EXISTS users (
    id BIGINT,
    team TEXT,
    UNIQUE(id,team)
    )""")
database.commit()


#Table of timezone (id, time)
sql.execute("""CREATE TABLE IF NOT EXISTS timezone (
    id BIGINT,
    time BIGINT DEFAULT 0,
    UNIQUE(id)
    )""")
database.commit()

#Table of past, current and future matches (first_team, second_team, match_id, time, score) 
sql.execute("""CREATE TABLE IF NOT EXISTS matches (
    first_team TEXT,
    second_team TEXT,
    match_id BIGINT,
    TIME BIGINT,
    score TEXT,
    UNIQUE(first_team,second_team,TIME),
    CHECK (first_team <> second_team)
    )""")
database.commit()

#Functions to manipulate with database

#delete choosen teams
def delete_teams(list, id):
    for team in list:
        sql.execute("""DELETE FROM users where id=? AND team =?""", (id,team))
        database.commit()

#Insert choosen teams into database
def update_teams(list,id):
    for i in list:
        sql.execute("""INSERT OR IGNORE INTO users VALUES(?,?)""", (id,i[:-1]))
        database.commit()
    
#Update timezone into database
def update_timezone(my_time, id):
    
    utc = datetime.datetime.utcnow().hour
    if(utc>12 and my_time<12 and (utc-my_time)>=12):
        timezone = 24-utc+my_time
    elif((utc>12 and my_time<12 and (utc-my_time)<12)\
        or (utc<=12 and my_time<=12)\
        or (utc>=12 and my_time>=12)\
        or (utc<=12 and my_time>=12 and (my_time-utc)<=12)):
            timezone = my_time-utc
    elif(utc<12 and my_time>12 and (my_time-utc)>12):
        timezone = my_time-24-utc

    sql.execute("""INSERT OR REPLACE into timezone VALUES(?,?)""", (id,timezone))
    database.commit()   

#Returns list of choosen teams
def select_my_teams(id):
    teams = sql.execute("""SELECT team FROM users WHERE id=?""", (id,)).fetchall()
    bd_list = [team for i in teams for team in i]
    return bd_list