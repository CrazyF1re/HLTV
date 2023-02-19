import requests
from bs4 import BeautifulSoup
import time
import datetime
import bd
#ПАРСЕР ВСЕХ АКТУАЛЬНЫХ КОМАНД
def parse_all_actual_teams():
    now_time = datetime.date.today()
    for i in range(14000):
        print(i)
        time.sleep(0.4)
        resp = requests.get(f"https://www.hltv.org/team/{i}/_")
        soup = BeautifulSoup(resp.text,"html.parser")
        if soup.find('div',class_ = 'teamProfile'):#если нашлась команда, а не пустая страница тогда идем дальше
            file = open('actual_teams.txt','r',encoding='utf-8')
            text = file.read()
            if f"https://www.hltv.org/team/{i}/_" not in text:#если команды нет в списке тогда идем дальше
                file.close()
                table = soup.find('table', class_='table-container match-table')
                if  table:#если есть последние матчи тогда идем дальше
                    if soup.find('tr',class_ = 'team-row').find('div',class_='score-cell').text == '-:-':#если есть матчи в ближайшие дни, тогда дату ставим сегодняшнюю
                        last_time_match = now_time
                    else:
                        last_time_match = last_time_match=soup.find('tr',class_ = 'team-row').find('span').text.split('/')
                        last_time_match = datetime.date(int(last_time_match[2]),int(last_time_match[1]),int(last_time_match[0]))  
                    time_delta = (now_time-last_time_match).days
                    if time_delta<180:#если последний матч был сыгран в ближайшие 180 дней, тогда записываем команду
                        file = open('actual_teams.txt','a',encoding='utf-8')
                        file.write(f"https://www.hltv.org/team/{i}/_\n")
                        file.close()

#парсит названия команд
def parse_info_about_teams():    
    file_read = open('actual_teams.txt','r',encoding='utf-8')
    urls = file_read.readlines()
    for url in urls:
        time.sleep(0.33)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text,'html.parser')
        info = [soup.find('h1',class_='profile-team-name text-ellipsis').text ,url.split('/')[4]]
        bd.sql.execute("""INSERT OR IGNORE INTO teams (team,id,url) VALUES(?,?,?)""", (info[0],info[1],url))
        bd.database.commit()


#парсинг последних результатов команд(5 последних матчей) и предстоящих матчей
def parse_previous_mathces():
    res = bd.sql.execute("""select * from teams""").fetchall()
    for i in res:
        time.sleep(0.33)
        print(res.index(i))
        resp = requests.get(i[2])
        soup = BeautifulSoup(resp.text,'html.parser')
        temp = soup.find('tr', class_ = 'team-row')
        if temp is None:
            bd.sql.execute("""DELETE from teams where id=?""",(i[1],))
            bd.database.commit()
            continue
        while temp.find('div',class_ = 'score-cell').text == '-:-':
            temp = temp.find_next('tr',class_ = 'team-row')
        info=[]
        for i in range(5): 
            if temp is None:
                break
            info.append(temp.find('a',class_ = 'team-name team-1').text)
            info.append(temp.find('a', class_ = 'team-name team-2').text)
            info.append(temp.find('span')['data-unix'][:-3])
            text = ''
            score = temp.find('div', class_ = 'score-cell')
            score =  score.find('span')
            text+=score.text+':'
            score = score.find_next('span')
            score = score.find_next('span')
            text+=score.text
            id = temp.find('a', class_ = 'stats-button')['href'].split('/')[2]
            info.append(text)
            if bd.sql.execute("""select * from matches where match_id = ?""", (id,)).fetchone() is None:
                bd.sql.execute("""INSERT OR IGNORE into matches (first_team,second_team,match_id,TIME,score) values(?,?,?,?,?)""",\
                (info[0],info[1],id,info[2],info[3]))
                bd.database.commit()
            info.clear()
            temp = temp.find_next('tr', class_ = 'team-row')



#regular update database with teams and matches
def parse_upcoming_matches():
    #adds new upcoming matches
    resp = requests.get('https://www.hltv.org/matches')
    soup = BeautifulSoup(resp.text,'html.parser')
    matches = soup.find_all('div', class_ ="upcomingMatch")
    
    info = []
    for match in matches:
        if match.find('div', class_ = 'matchInfoEmpty') is None and match.find('div', class_ = 'team text-ellipsis') is None:

            info.append(match.find('div', class_ = 'matchTeam team1').text.replace('\n',''))
            info.append(match.find('div', class_ = 'matchTeam team2').text.replace('\n',''))
            info.append(match['data-zonedgrouping-entry-unix'][:-3])
            id = match.find('a', class_ = 'match a-reset')['href'].split('/')[2]
            bd.sql.execute("""INSERT OR IGNORE into matches (first_team,second_team,match_id,TIME,score) values(?,?,?,?,?)""",(info[0],info[1],id,info[2], '-'))
            bd.database.commit()

            #adding team in list of actual teams if it needs

            if bd.sql.execute("""select team from teams where team = ?""", (info[0],)).fetchone() is None:

                resp2 = requests.get('https://www.hltv.org'+match.find('a', class_ = 'match a-reset')['href'])
                soup = BeautifulSoup(resp2.text,'html.parser')
                id = soup.find('div',class_ = 'team1-gradient').find('a')['href'].split('/')[2]
                bd.sql.execute("""INSERT INTO teams (team,id,url) values(?,?,?)""",(info[0],id,f'https://www.hltv.org/team/{id}/_'))
                bd.database.commit()

            elif bd.sql.execute("""select team from teams where team = ?""", (info[1],)).fetchone() is None:
                resp2 = requests.get('https://www.hltv.org'+match.find('a', class_ = 'match a-reset')['href'])
                soup = BeautifulSoup(resp2.text,'html.parser')
                id = soup.find('div',class_ = 'team2-gradient').find('a')['href'].split('/')[2]
                bd.sql.execute("""INSERT INTO teams (team,id,url) values(?,?,?)""",(info[1],id,f'https://www.hltv.org/team/{id}/_'))
                bd.database.commit()

        info.clear()

def parse_results():
    #editing upcoming->previous matches
    resp = requests.get('https://www.hltv.org/results')
    soup = BeautifulSoup(resp.text,'html.parser')
    temp = soup.find('div', class_ = 'results-holder allres')
    matches = temp.find_all('div', class_ ='result-con')

    for match in matches:
        id = match.find('a',class_ = 'a-reset')['href'].split('/')[2]
        score = bd.sql.execute("""select score from matches where match_id=?""",(id,)).fetchone()
        if  score is not None and score[0] == '-':
            temp = match.find_all('span')
            score = temp[0].text+':'+temp[1].text
            bd.sql.execute("""UPDATE matches set score = ? where match_id=?""",(score,id))
            bd.database.commit()
            
def delete_unncessary_matches():
    teams = bd.sql.execute("""select team from teams""").fetchall()
    for team in teams:
        resp = bd.sql.execute("""select first_team,second_team,time from matches where
        (first_team = ? or second_team= ?) and  score != '-'""",(team[0],team[0])).fetchall()

        resp.sort(key = lambda x: int(x[2]),reverse=True)
        if len(resp)>5:
            for i in range(5,len(resp)):
                new_team = resp[i][1] if resp[i][0] == team[0] else resp[i][0]

                resp2 = bd.sql.execute("""select first_team,second_team,time from matches
                where (first_team = ? or second_team= ?) and  score <> '-'""",(new_team,new_team)).fetchall()

                resp2.sort(key = lambda x: int(x[2]),reverse=True)
                if resp2.index(resp[i])>5:
                    bd.sql.execute("""DELETE FROM matches where first_team=? and second_team = ? and time = ?""", (resp[i][0],resp[i][1],resp[i][2]))
                    bd.database.commit()    


#function for main
def parse_functions():
    #parse_previous_mathces()#only one time
    delete_unncessary_matches()
    parse_upcoming_matches()
    parse_results()
    