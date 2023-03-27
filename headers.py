
from aiogram.dispatcher.filters import Text
from global_variables import dp,Conditions
import functions

async def start(): #func for main.py
    await dp.start_polling()

#начало диалога с ботом
dp.register_message_handler(functions.start_command,commands=['start'])


#добавить базовые инструкции
dp.register_message_handler(functions.help_command,commands=['help'])


#Гглавное меню
dp.register_message_handler(functions.menu_command,commands=['menu'],state='*')


#Chose timezone for correct time of matches
dp.register_message_handler(functions.timezone_command,commands=['timezone'])


#still chose timezone, process entered data
dp.register_message_handler(functions.set_timezone2,state = Conditions.SET_TIMEZONE)


#back to main menu
dp.register_callback_query_handler(functions.go_to_menu,text = 'back',state='*')   


#back to previous menu
dp.register_callback_query_handler(functions.back_to_teams,text = 'back_edit',state='*')


#выбор команды
dp.register_callback_query_handler(functions.enter_searching_team,text = 'choose_teams')


#обработка поиска команды
dp.register_message_handler(functions.get_teams,state=Conditions.ENTER_TEAM)


#выбор команд
dp.register_callback_query_handler(functions.select_teams,Text(startswith='team_'),state= Conditions.ENTER_TEAM)


#мои команды
dp.register_callback_query_handler(functions.get_my_teams,text = 'my_teams')


#обновление меню при выборе команды из списка команд
dp.register_callback_query_handler(functions.delete_choosen_team,Text(startswith='team_'),state=Conditions.DELETE_ONE_TEAM)


#удаление выбранной команды
dp.register_callback_query_handler(functions.delete_one_team,text = 'delete',state=Conditions.DELETE_ONE_TEAM)


#удалить команды (separate button)
dp.register_callback_query_handler(functions.delete_choosen_teams,text='delete_team')


#выбор команд для удаления
dp.register_callback_query_handler(functions.choosing_teams_for_delete,Text(startswith='team_'),state=Conditions.DELETE_TEAMS)


#gets upcoming matches of chosen teams
dp.register_callback_query_handler(functions.get_upcoming_matches,text = 'upcoming_matches')


#gets last 5 matches for each choosen team
dp.register_callback_query_handler(functions.get_previous_matches,text = 'previous_matches')


#chose team from list to get previous matches
dp.register_callback_query_handler(functions.get_five_matches,Text(startswith='team_'),state=Conditions.PREVIOUSE_MATCHES)


#дефолтный хэндлер.
dp.register_message_handler(functions.echo_message)






