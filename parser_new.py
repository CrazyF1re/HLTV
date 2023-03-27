import requests
from bs4 import BeautifulSoup
import time 
from selenium import webdriver
import db


def selenium_get(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument("--headless") 
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    try:
        driver.get(url=url) 
        return driver.page_source
    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()
    

#regular update database with teams and matches

def parse_upcoming_matches():
    #adds new upcoming matches

    resp  = selenium_get('https://www.hltv.org/matches') 
    soup = BeautifulSoup(resp,'lxml')

    matches = soup.find_all('div', class_ ="upcomingMatch")
    info = []
    for match in matches:
        if match.find('div', class_ = 'matchInfoEmpty') is None and match.find('div', class_ = 'team text-ellipsis') is None:

            info.append(match.find('div', class_ = 'matchTeam team1').text.replace('\n',''))
            info.append(match.find('div', class_ = 'matchTeam team2').text.replace('\n',''))
            info.append(match['data-zonedgrouping-entry-unix'][:-3])
            id = match.find('a', class_ = 'match a-reset')['href'].split('/')[2]
            db.sql.execute("""INSERT OR IGNORE INTO matches (first_team,second_team,match_id,TIME,score) VALUES(?,?,?,?,?)""",(info[0],info[1],id,info[2], '-'))
            db.database.commit()

            #adding team in list of actual teams if it needs
            if db.sql.execute("""select team from teams where team = ?""", (info[0],)).fetchone() is None:
                id = match['team1']
                db.sql.execute("""INSERT INTO teams (team,id,url) VALUES(?,?,?)""",(info[0],id,f"https://www.hltv.org/team/{id}/_"))
            elif db.sql.execute("""select team from teams where team = ?""", (info[1],)).fetchone() is None:
                id = match['team2']
                db.sql.execute("""INSERT INTO teams (team,id,url) VALUES(?,?,?)""",(info[1],id,f"https://www.hltv.org/team/{id}/_"))
        info.clear()

#editing upcoming matches->previous matches
def parse_results():
    resp = requests.get('https://www.hltv.org/results')
    soup = BeautifulSoup(resp.text,'html.parser')
    temp = soup.find('div', class_ = 'results-holder allres')
    matches = temp.find_all('div', class_ ='result-con')

    for match in matches:
        id = match.find('a',class_ = 'a-reset')['href'].split('/')[2]
        score = db.sql.execute("""select score from matches where match_id=?""",(id,)).fetchone()
        if  score is not None and score[0] == '-':
            temp = match.find_all('span')
            score = temp[0].text+':'+temp[1].text
            db.sql.execute("""UPDATE matches set score = ? where match_id=?""",(score,id))
            db.database.commit()

#remove teams which were inactive more 3 month            
def delete_unnecessary_teams():
    teams = db.sql.execute("""select team from teams""").fetchall()
    for team in teams:
        resp = db.sql.execute("""select time from matches where first_team=? or second_team=?""", (team[0],team[0])).fetchall()
        if len(resp)==0 or (int(time.time()) - max(resp)[0] >7776000):
            db.sql.execute("""delete from teams where team=?""", (team[0],))
            db.database.commit()

#remove matches which does not need to show
def delete_unncessary_matches():
    teams = db.sql.execute("""select team from teams""").fetchall()
    for team in teams:
        resp = db.sql.execute("""select first_team,second_team,time from matches where
        (first_team = ? or second_team= ?) and  score != '-'""",(team[0],team[0])).fetchall()

        resp.sort(key = lambda x: int(x[2]),reverse=True)
        if len(resp)>5:
            for i in range(5,len(resp)):
                new_team = resp[i][1] if resp[i][0] == team[0] else resp[i][0]

                resp2 = db.sql.execute("""select first_team,second_team,time from matches
                where (first_team = ? or second_team= ?) and  score <> '-'""",(new_team,new_team)).fetchall()

                resp2.sort(key = lambda x: int(x[2]),reverse=True)
                if resp2.index(resp[i])>5:
                    db.sql.execute("""DELETE FROM matches where first_team=? and second_team = ? and time = ?""", (resp[i][0],resp[i][1],resp[i][2]))
                    db.database.commit()    


#function for main
async def parse_functions():
    parse_upcoming_matches()
    delete_unncessary_matches()
    delete_unnecessary_teams()
    parse_results()
    