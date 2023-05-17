import requests
from bs4 import BeautifulSoup
import time 
from selenium import webdriver
from global_variables import sql,database
import datetime
import os.path

# get for parse actual matches because of cloudflare
def selenium_get(url):
    driver = webdriver.Chrome()
    try:
        driver.get(url=url) 
        return driver.page_source
    except:
        return 0
    finally:
        driver.close()
        driver.quit()


#single function call to fill database if it is empty
def parse_all_actual_teams():
    now_time = datetime.date.today()
    for i in range(14000):
        time.sleep(0.4)
        
        resp = requests.get(f"https://www.hltv.org/team/{i}/_")
        soup = BeautifulSoup(resp.text,"html.parser")

        #если нашлась команда, а не пустая страница и если есть последние матчи тогда идем дальше
        if soup.find('div',class_ = 'teamProfile') and soup.find('table', class_='table-container match-table'):
                
            if soup.find('tr',class_ = 'team-row').find('div',class_='score-cell').text == '-:-':#если есть матчи в ближайшие дни, тогда дату ставим сегодняшнюю
                last_time_match = now_time
            else:
                last_time_match = last_time_match=soup.find('tr',class_ = 'team-row').find('span').text.split('/')
                last_time_match = datetime.date(int(last_time_match[2]),int(last_time_match[1]),int(last_time_match[0]))  

            # find defference between nowadays and last match time
            time_delta = (now_time-last_time_match).days
                
            if time_delta<180:#если последний матч был сыгран в ближайшие 180 дней, тогда записываем команду

                soup = BeautifulSoup(resp.text,'html.parser')
                info = [soup.find('h1',class_='profile-team-name text-ellipsis').text ,i]
                sql.execute("""INSERT OR IGNORE INTO teams (team,id,url) VALUES(?,?,?)""", (info[0],info[1],f"https://www.hltv.org/team/{i}/_"))
                database.commit()
                temp = soup.find('tr', class_ = 'team-row')
                while temp.find('div',class_ = 'score-cell').text == '-:-':
                    temp = temp.find_next('tr',class_ = 'team-row')
                info=[]

                for i in range(5): 
                    if temp is None:
                        break
                    #gets info about match and write into "info"
                    info.append(temp.find('a',class_ = 'team-name team-1').text)
                    info.append(temp.find('a', class_ = 'team-name team-2').text)
                    info.append(temp.find('span')['data-unix'][:-3])
                    text = ''
                    score = temp.find('div', class_ = 'score-cell')
                    score =  score.find('span')
                    text+=score.text+' '
                    score = score.find_next('span')
                    score = score.find_next('span')
                    text+=score.text
                    id = temp.find('a', class_ = 'stats-button')['href'].split('/')[2]
                    info.append(text)

                    if sql.execute("""select * from matches where match_id = ?""", (id,)).fetchone() is None:
                        sql.execute("""INSERT OR IGNORE into matches (first_team,second_team,match_id,TIME,score) values(?,?,?,?,?)""",\
                        (info[0],info[1],id,info[2],info[3]))
                        database.commit()
                    info.clear()
                    temp = temp.find_next('tr', class_ = 'team-row')

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
            sql.execute("""INSERT OR IGNORE INTO matches (first_team,second_team,match_id,TIME,score) VALUES(?,?,?,?,?)""",(info[0],info[1],id,info[2], '-'))
            database.commit()

            #adding team in list of actual teams if it needs
            if sql.execute("""select team from teams where team = ?""", (info[0],)).fetchone() is None:
                id = match['team1']
                sql.execute("""INSERT INTO teams (team,id,url) VALUES(?,?,?)""",(info[0],id,f"https://www.hltv.org/team/{id}/_"))
            elif sql.execute("""select team from teams where team = ?""", (info[1],)).fetchone() is None:
                id = match['team2']
                sql.execute("""INSERT INTO teams (team,id,url) VALUES(?,?,?)""",(info[1],id,f"https://www.hltv.org/team/{id}/_"))
        info.clear()

#editing upcoming matches->previous matches
def parse_results():

    resp = requests.get('https://www.hltv.org/results')
    soup = BeautifulSoup(resp.text,'html.parser')
    temp = soup.find('div', class_ = 'results-holder allres')
    matches = temp.find_all('div', class_ ='result-con')

    for match in matches:
        id = match.find('a',class_ = 'a-reset')['href'].split('/')[2]
        score = sql.execute("""select score from matches where match_id=?""",(id,)).fetchone()

        if  score is not None and score[0] == '-':
            temp = match.find_all('span')
            score = temp[0].text+':'+temp[1].text
            sql.execute("""UPDATE matches set score = ? where match_id=?""",(score,id))
            database.commit()

#remove teams which were inactive more 3 month            
def delete_unnecessary_teams():

    teams = sql.execute("""select team from teams""").fetchall()
    
    for team in teams:
        resp = sql.execute("""select time from matches where first_team=? or second_team=?""", (team[0],team[0])).fetchall()

        if len(resp)==0 or (int(time.time()) - max(resp)[0] >7776000):
            sql.execute("""delete from teams where team=?""", (team[0],))
            database.commit()

#remove matches which does not need to show
def delete_unncessary_matches():

    teams = sql.execute("""select team from teams""").fetchall()

    for team in teams:
        resp = sql.execute("""select first_team,second_team,time from matches where
        (first_team = ? or second_team= ?) and  score != '-'""",(team[0],team[0])).fetchall()

        resp.sort(key = lambda x: int(x[2]),reverse=True)

        if len(resp)>5:

            for i in range(5,len(resp)):
                new_team = resp[i][1] if resp[i][0] == team[0] else resp[i][0]

                resp2 = sql.execute("""select first_team,second_team,time from matches
                where (first_team = ? or second_team= ?) and  score <> '-'""",(new_team,new_team)).fetchall()

                resp2.sort(key = lambda x: int(x[2]),reverse=True)
                if resp2.index(resp[i])>5:
                    sql.execute("""DELETE FROM matches where first_team=? and second_team = ? and time = ?""", (resp[i][0],resp[i][1],resp[i][2]))
                    database.commit()    


#function for main
async def parse_functions():
    if (not os.path.exists('server.db')  or time.time() -os.stat('server.db').st_mtime >1296000):
        parse_all_actual_teams()
    parse_upcoming_matches()
    delete_unncessary_matches()
    delete_unnecessary_teams()
    parse_results()
    