import config
from aiogram import types,Bot ,Dispatcher
from aiogram.utils.helper import Helper, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import db
import datetime

bot = Bot(config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
timezone_server = 7 #default timezone


choose_teams = types.InlineKeyboardButton('Выбрать команду ', callback_data='choose_teams')
my_teams = types.InlineKeyboardButton('Мои команды',callback_data='my_teams')
delete_teams = types.InlineKeyboardButton('Удалить команду',callback_data='delete_team')
previous_matches = types.InlineKeyboardButton('Прошедшие матчи', callback_data='previous_matches')
upcoming_matches = types.InlineKeyboardButton('Предстоящие матчи', callback_data='upcoming_matches')

menu = types.InlineKeyboardMarkup().add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)


class Conditions(Helper):
    DELETE_ONE_TEAM = ListItem()# delete team in list of teams
    DELETE_TEAMS = ListItem()# delete chosing teams
    ENTER_TEAM = ListItem()# entering name of team
    PREVIOUSE_MATCHES = ListItem()# previous matches
    STATE_0 = ListItem()
    SET_TIMEZONE = ListItem()


class Teams:
    
    def __init__(self, team:str)-> None :
        self.team = team.lower()

    #searching team in list of teams
    async def search_team_in_list(self):
        teams = db.sql.execute("""SELECT * from teams""").fetchall()
        result = []
        for team in teams:
            string = ''.join(team[0]).lower()
            if self.team in string:
                result.append(''.join(team[0]))
        return result

    #search upcoming matches of choosen team
    async def search_upcoming_matches(list_of_teams , id):
            timezone_user = db.sql.execute("""SELECT time FROM timezone WHERE id=?""", (id,)).fetchone()[0]
            all_matches = set()

            for team in list_of_teams:
                matches = db.sql.execute("""SELECT distinct first_team , second_team, TIME FROM matches WHERE (first_team=? OR second_team=?) and score = '-'""", (team[0],team[0])).fetchall()
                if(len(matches)==0):continue    

                for match in matches:
                        all_matches.add((match[0],match[1], \
                        datetime.datetime.utcfromtimestamp(match[2]+3600*(timezone_user)).strftime('%m-%d %H:%M')))    

            return all_matches
    
    #returns last 5 matches of choosen team
    async def last_5_matches(team,id):
        matches=  db.sql.execute(
            """select first_team,score,second_team, time 
            from matches 
            where (first_team=? or second_team = ?) and score<> '-'""", (team,team)).fetchall()
        matches.sort(key = lambda x: int(x[3]),reverse=True)
        timezone_user = db.sql.execute("""select time from timezone where id=?""",(id,)).fetchone()[0]
        string=''
        for i,match in enumerate(matches):
            if i >4:break
            string+=match[0]+' '+ match[1] +' '+ match[2]+ ' at '+ datetime.datetime.utcfromtimestamp(match[3]+3600*(timezone_user)).strftime('%m-%d')+ '\n'
        return string
