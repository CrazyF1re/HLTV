
from aiogram.dispatcher.filters import Text
from global_variables import dp,Conditions
import functions

async def start(): #func for main.py
    await dp.start_polling()

#start dialog with bot
dp.register_message_handler(functions.start_command,commands=['start'])


#help command
dp.register_message_handler(functions.help_command,commands=['help'])


#Menu command
dp.register_message_handler(functions.menu_command,commands=['menu'],state='*')


#Timezone command
dp.register_message_handler(functions.timezone_command,commands=['timezone'])


#Handler of chose timezone
dp.register_message_handler(functions.set_timezone2,state = Conditions.SET_TIMEZONE)


#back to main menu
dp.register_callback_query_handler(functions.go_to_menu,text = 'back',state='*')   


#back to previous menu
dp.register_callback_query_handler(functions.back_to_teams,text = 'back_edit',state='*')


#Handler of "Choose teams" button
dp.register_callback_query_handler(functions.enter_searching_team,text = 'choose_teams')


#handler of entered name of team by user
dp.register_message_handler(functions.get_teams,state=Conditions.ENTER_TEAM)


#handler of Menu with teams choose by user
dp.register_callback_query_handler(functions.select_teams,Text(startswith='team_'),state= Conditions.ENTER_TEAM)


#Handler of "My teams" button
dp.register_callback_query_handler(functions.get_my_teams,text = 'my_teams')


#Handler when user chose team from list of teams (just add delete button)
dp.register_callback_query_handler(functions.delete_choosen_team,Text(startswith='team_'),state=Conditions.DELETE_ONE_TEAM)


#Handler of "delete" button (check upper)
dp.register_callback_query_handler(functions.delete_one_team,text = 'delete',state=Conditions.DELETE_ONE_TEAM)


#Handler of "Delete team" button into main menu
dp.register_callback_query_handler(functions.delete_choosen_teams,text='delete_team')


#Handler of menu with teams to delete
dp.register_callback_query_handler(functions.choosing_teams_for_delete,Text(startswith='team_'),state=Conditions.DELETE_TEAMS)


#gets upcoming matches of chosen teams
dp.register_callback_query_handler(functions.get_upcoming_matches,text = 'upcoming_matches')


#gets last 5 matches for each choosen team
dp.register_callback_query_handler(functions.get_previous_matches,text = 'previous_matches')


#chose team from list to get previous matches
dp.register_callback_query_handler(functions.get_five_matches,Text(startswith='team_'),state=Conditions.PREVIOUSE_MATCHES)


#дефолтный хэндлер.
dp.register_message_handler(functions.echo_message)