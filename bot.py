from aiogram import types,Bot ,Dispatcher
from aiogram.utils.helper import Helper, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
import emoji
import config
import bd
import sqlite3
import datetime


async def start(): #func for main.py
    await dp.start_polling()


bot = Bot(config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
timezone_server = 7 #default timezone


#buttons for main menu
choose_teams = types.InlineKeyboardButton('Выбрать команду ', callback_data='choose_teams')
my_teams = types.InlineKeyboardButton('Мои команды',callback_data='my_teams')
delete_teams = types.InlineKeyboardButton('Удалить команду',callback_data='delete_team')
previous_matches = types.InlineKeyboardButton('Прошедшие матчи', callback_data='previous_matches')
upcoming_matches = types.InlineKeyboardButton('Предстоящие матчи', callback_data='upcoming_matches')

menu = types.InlineKeyboardMarkup().add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)


#класс состояний
class Conditions(Helper):
    DELETE_ONE_TEAM = ListItem()# delete team in list of teams
    DELETE_TEAMS = ListItem()# delete chosing teams
    ENTER_TEAM = ListItem()# entering name of team
    PREVIOUSE_MATCHES = ListItem()# previous matches
    STATE_0 = ListItem()
    STATE_2 = ListItem()

#класс команды
class Teams:
    
    def __init__(self, team:str)-> None :
        self.team = team.lower()

    #searching team in list of teams
    def search_team_in_list(self):
        connection = sqlite3.connect('server.db')
        cursor = connection.cursor()
        mass = cursor.execute("""SELECT * from teams""").fetchall()
        result = []
        for i in mass:
            string = ''.join(i[0]).lower()
            if self.team in string:
                result.append(''.join(i[0]))
        return result

    #search upcoming matches of choosen team
    def search_upcoming_matches(list_of_teams , id):
            timezone_user = bd.sql.execute("""SELECT time FROM timezone WHERE id=?""", (id,)).fetchone()[0]
            all_matches = set()

            for team in list_of_teams:
                matches = bd.sql.execute("""SELECT distinct first_team , second_team, TIME FROM matches WHERE (first_team=? OR second_team=?) and score = '-'""", (team[0],team[0])).fetchall()
                if(len(matches)==0):continue    

                for match in matches:
                        all_matches.add((match[0],match[1], datetime.datetime.utcfromtimestamp(match[2]+3600*(timezone_user)).strftime('%m-%d %H:%M')))    

            return all_matches
    
    #returns last 5 matches of choosen team
    def last_5_matches(team,id):
        matches=  bd.sql.execute("""select first_team,score,second_team, time from matches where (first_team=? or second_team = ?) and score<> '-'""", (team,team)).fetchall()
        matches.sort(key = lambda x: int(x[3]),reverse=True)
        timezone_user = bd.sql.execute("""select time from timezone where id=?""",(id,)).fetchone()[0]
        string=''
        i=0
        for match in matches:
            print(match)
            if i >4:break
            result = match[1].split()
            string+=match[0]+' '+ result[0]+':'+result[1]+' '+ match[2]+ ' at '+ datetime.datetime.utcfromtimestamp(match[3]+3600*(timezone_user)).strftime('%m-%d')+ '\n'
            i+=1
        return string

#начало диалога с ботом
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    bd.sql.execute("""INSERT OR IGNORE INTO timezone (id,time) values(?,?)""", (message.from_user.id,0))
    bd.database.commit()
    await message.answer('Бот позволяет отслеживать активность выбранных команд, прошедшие матчи и те, что еще будут\n\
/timezone - установить часовой пояс (по умолчанию UTC-0)\n\
/help - скорая помощь \n\
/menu - главное меню')

#добавить базовые инструкции
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer('Когда нибудь добавлю')


#Гглавное меню
@dp.message_handler(commands=['menu'] , state= '*')
async def menu_command(message: types.Message):
    menu.inline_keyboard.clear()
    menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)
    await message.answer('Меню' ,reply_markup=menu)


#Chose timezone for correct time of matches
@dp.message_handler(commands=['timezone'])
async def timezone_command(message: types.Message):
    menu.inline_keyboard.clear()
    menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
    await message.answer(text = 'Выберите часовой пояс', reply_markup=menu)
    await dp.current_state().set_state(Conditions.all()[2])


#still chose timezone, process entered data
@dp.message_handler(state = Conditions.STATE_2)
async def timezone2_command(message:types.Message):
    try:
        timezone = int(message.text)
        if(timezone<0 or timezone >=24):
            return await message.answer('Введите конкретный час')
    except:
        await message.answer('Введите только часы без минут запятых и тд')

    bd.update_timezone(timezone, message.from_user.id)

    menu.inline_keyboard.clear()
    menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)

    await dp.current_state().reset_state()
    await message.answer('Часовой пояс успешно сохранен', reply_markup=menu)


#back to main menu
@dp.callback_query_handler(text = 'back',state='*')
async def goin_to_back(callback_query: types.CallbackQuery):
    menu.inline_keyboard.clear()
    menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)

    await dp.current_state().reset_state()
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,'Меню' ,reply_markup=menu)


#back to previous menu
@dp.callback_query_handler(text = 'back_edit', state= '*')
async def back_to_teams(callback_query: types.CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=menu)
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, 'Твои команды', reply_markup= menu)

#выбор команды
@dp.callback_query_handler(text = 'choose_teams')
async def enter_searching_team(callback_query: types.CallbackQuery):
    menu.inline_keyboard.clear()
    menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
    await dp.current_state().set_state(Conditions.ENTER_TEAM[0])
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)
    return await bot.send_message(callback_query.from_user.id, 'Напишите название команды', reply_markup= menu)


#обработка поиска команды
@dp.message_handler(state=Conditions.ENTER_TEAM)
async def get_teams(message: types.Message):

    if(len(message.text)<=1):
        return await message.answer('А ничу нормально разговаривай')
    team = Teams (message.text)

    teams = team.search_team_in_list()
    if (len(teams)== 0):
        #должно будет вылезать не главное меню а что то еще
        await bot.send_message(message.chat.id,'Не найдено ни одной команды',reply_markup=menu)
    else:
        menu.inline_keyboard.clear()
        for i in range(len(teams)):
            menu.add(types.InlineKeyboardButton(teams[i], callback_data='team_'+ str(i)))

        menu.add(types.InlineKeyboardButton('Добавить выбранные команды', callback_data= 'team_-1'))
        menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
        await bot.send_message(message.chat.id,'Найденные команды',reply_markup=menu)


#выбор команд
@dp.callback_query_handler(Text(startswith='team_'), state=Conditions.ENTER_TEAM )
async def select_teams(callback_query: types.CallbackQuery):
    button = int(callback_query.data.split('_')[1])
    list_of_chosen_teams = []
    if(button == -1):
        for team in menu['inline_keyboard']:
            if(team[0]['text'].find('✅')!=-1):
                list_of_chosen_teams.append(team[0]['text'])

        menu.inline_keyboard.clear()
        menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)
        answer = ''

        if (len(list_of_chosen_teams)!=0):
            answer = 'Выбранные команды сохранены'
            bd.update_teams(list_of_chosen_teams ,callback_query.from_user.id)
            list_of_chosen_teams.clear()
        else:
            answer = 'Не было выбрано ни одной команды'
        

        await dp.current_state().reset_state()
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
        return await bot.send_message(callback_query.from_user.id, answer, reply_markup=menu)
        
    check = menu['inline_keyboard'][button][0]['text']
    if(check.find('✅')==-1):
        text = emoji.emojize(check+':check_mark_button:')
    else:
        text = check[:-1]
    menu.inline_keyboard[button] = [{"text": text, "callback_data": menu['inline_keyboard'][button][0]['callback_data']}]

    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(reply_markup=menu)
    return


#мои команды
@dp.callback_query_handler(text = 'my_teams')
async def get_my_teams(callback_query: types.CallbackQuery):
    teams = bd.select_my_teams(callback_query.from_user.id)
    menu.inline_keyboard.clear()

    if(len(teams)==0):
        menu.add(types.InlineKeyboardButton('Добавить команду', callback_data= 'choose_teams'))\
        .add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
        answer = 'Не выбрано ни одной команды'
    else:
        for i in teams:
            menu.add(types.InlineKeyboardButton(i, callback_data= 'team_'+i))
        menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
        answer = 'Твои команды'
        await dp.current_state().set_state(Conditions.DELETE_ONE_TEAM[0])

    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)
    return await bot.send_message(callback_query.from_user.id, answer,reply_markup=menu)


#обновление меню при выборе команды из списка команд
@dp.callback_query_handler(Text(startswith = 'team_'),state=Conditions.DELETE_ONE_TEAM)
async def delete_choosen_team(callback_query : types.CallbackQuery):
    team = callback_query.data.split('_')[1]
    editing_menu = types.InlineKeyboardMarkup()
    editing_menu.add(types.InlineKeyboardButton(team , callback_data= 'chosen_'+team))\
        .add(types.InlineKeyboardButton('Удалить', callback_data='delete'))\
        .add(types.InlineKeyboardButton('Назад', callback_data= 'back_edit'))
    
    await callback_query.message.edit_reply_markup(reply_markup=editing_menu)


#удаление выбранной команды
@dp.callback_query_handler(text = 'delete' , state = Conditions.DELETE_ONE_TEAM)
async def delete_one_team(callback_query : types.CallbackQuery):
    team = callback_query['message']['reply_markup']['inline_keyboard'][0][0]['text']
    bd.delete_teams([team] ,callback_query.from_user.id)

    list_of_teams = [i[0]['text'] for i in menu.inline_keyboard ]

    menu.inline_keyboard.pop(list_of_teams.index(team))

    await bot.delete_message(chat_id=callback_query.from_user.id , message_id= callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,'Команда удалена', reply_markup=menu)


#удалить команды (separate button)
@dp.callback_query_handler(text = 'delete_team')
async def delete_choosen_teams(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    teams = bd.select_my_teams(callback_query.from_user.id)
    if(len(teams)==0):
        menu.inline_keyboard.clear()
        menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
        return await bot.send_message(callback_query.from_user.id,'Не выбрано ни одной команды',reply_markup=menu)
    else:
        menu.inline_keyboard.clear()
        for i in range(len(teams)):
            menu.add(types.InlineKeyboardButton(teams[i], callback_data='team_'+ str(i)))
        menu.add(types.InlineKeyboardButton('Удалить выбранные команды', callback_data= 'team_-1'))
        menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))

        await dp.current_state().reset_state()
        await dp.current_state().set_state(Conditions.DELETE_TEAMS[0])
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, 'Твои команды',reply_markup=menu)


#выбор команд для удаления
@dp.callback_query_handler(Text(startswith = 'team_'), state=Conditions.DELETE_TEAMS)
async def choosing_teams_for_delete(callback_query: types.CallbackQuery):

    button = int(callback_query.data.split('_')[1])
    list_of_chosen_teams =[]
    if(button == -1):
        for team in menu['inline_keyboard']:
            if '✅' in team[0]['text']:
                list_of_chosen_teams.append(team[0]['text'][:-1])

        answer =''
        if (len(list_of_chosen_teams)!=0):
            answer = 'Выбранные команды удалены'
            bd.delete_teams(list_of_chosen_teams ,callback_query.from_user.id)
            list_of_chosen_teams.clear()
        else:
            answer = 'Не было выбрано ни одной команды'


        menu.inline_keyboard.clear()
        menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)

        await dp.current_state().reset_state()
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
        return await bot.send_message(callback_query.from_user.id, answer, reply_markup=menu) 
    
    check = menu['inline_keyboard'][button][0]['text']
    if '✅' not in check:
        text = emoji.emojize(check+':check_mark_button:')
    else:
        text = check[:-1]

    new_bttn = [{"text": text, "callback_data": menu['inline_keyboard'][button][0]['callback_data']}]
    menu.inline_keyboard[button] = new_bttn

    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(reply_markup=menu)


#gets upcoming matches of chosen teams
@dp.callback_query_handler(text = 'upcoming_matches')
async def get_upcoming_matches(callback_query: types.CallbackQuery):
    id = callback_query.from_user.id
    teams = bd.sql.execute("""SELECT team FROM users WHERE id =?""", (id,)).fetchall()
    list_of_matches = Teams.search_upcoming_matches(teams, callback_query.from_user.id)
    string = ''

    menu.inline_keyboard.clear()
    menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))

    if(len(list_of_matches)==0):
        string = 'На ближайшее время матчей нет'
    for match in list_of_matches:
        string+=match[0]+' VS '+ match[1]+' at '+match[2]+'\n'

    await bot.answer_callback_query(callback_query.id)
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,string, reply_markup=menu)


#gets last 5 matches for each choosen team
@dp.callback_query_handler(text = 'previous_matches')
async def get_previous_matches(callback_query: types.CallbackQuery ):
    teams= bd.sql.execute("""SELECT team FROM users WHERE id =?""", (callback_query.from_user.id,)).fetchall()
    menu.inline_keyboard.clear()

    if len(teams) == 0:
        menu.add(types.InlineKeyboardButton('Добавить команду', callback_data='choose_teams'))
        menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
    
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
        return await bot.send_message(callback_query.from_user.id,'Вы не выбрали ни одной команды',reply_markup= menu)
    
    for team in teams:
        menu.add(types.InlineKeyboardButton(team[0], callback_data='team_'+ str(team[0])))
    menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))

    await dp.current_state().set_state(Conditions.PREVIOUSE_MATCHES[0])
    await bot.answer_callback_query(callback_query.id)
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    return await bot.send_message(callback_query.from_user.id, 'Выбери команду',reply_markup=menu)


#chose team from list to get previous matches
@dp.callback_query_handler(Text(startswith = 'team_'), state=Conditions.PREVIOUSE_MATCHES)
async def choosing_teams_for_delete(callback_query: types.CallbackQuery):
    team = callback_query.data.split('_')[1]
    editing_menu = types.InlineKeyboardMarkup()
    editing_menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back_edit'))
    
    await bot.answer_callback_query(callback_query.id)
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id= callback_query.message.message_id)
    return await bot.send_message(callback_query.from_user.id,\
                                  Teams.last_5_matches(team,callback_query.from_user.id),\
                                  reply_markup=editing_menu)   


#дефолтный хэндлер
@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text)





#пример как нужно переделать хэндлеры   
'''async def entry_point(message:types.Message):
    await message.reply('Its work!!!')

dp.register_message_handler(entry_point, commands=['setup'],state = '*')'''
