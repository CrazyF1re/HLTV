from global_variables import dp,Conditions,Teams,menu,choose_teams,delete_teams,my_teams,previous_matches,upcoming_matches,bot
from aiogram import types
import db
import emoji


async def delete_message(bot,user_id,message_id):
    try:
        return await bot.delete_message(chat_id=user_id, message_id= message_id)
    except:
        return 0

async def start_command(message: types.Message):
    db.sql.execute("""INSERT OR IGNORE INTO timezone (id,time) values(?,?)""", (message.from_user.id,0))
    db.database.commit()
    await message.answer('Бот позволяет отслеживать активность выбранных команд, прошедшие матчи и те, что еще будут\n\
/timezone - установить часовой пояс (по умолчанию UTC-0)\n\
/help - скорая помощь \n\
/menu - главное меню')

async def help_command(message:types.Message):
     await message.answer('Когда нибудь добавлю')

async def menu_command(message:types.Message):
    await dp.current_state().reset_state()
    menu.inline_keyboard.clear()
    menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)
    await message.answer('Меню' ,reply_markup=menu)

async def timezone_command(message:types.Message):
    menu.inline_keyboard.clear()
    menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
    await message.answer(text = 'Выберите часовой пояс', reply_markup=menu)
    await dp.current_state().set_state(Conditions.SET_TIMEZONE[0])

async def set_timezone2(message:types.Message):
    try:
        timezone = int(message.text)
    except:
        return await message.answer('Введите только часы без минут запятых и тд')
    else:
        if(timezone<0 or timezone >=24):
            return await message.answer('Введите конкретный час')
        
        db.update_timezone(timezone, message.from_user.id)

        menu.inline_keyboard.clear()
        menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)

        await dp.current_state().reset_state()
        await message.answer('Часовой пояс успешно сохранен', reply_markup=menu)

async def go_to_menu(callback_query:types.CallbackQuery):
    menu.inline_keyboard.clear()
    menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)
    await dp.current_state().reset_state()
    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,'Меню' ,reply_markup=menu)

async def back_to_teams(callback_query:types.CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=menu)
    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, 'Твои команды', reply_markup= menu)

async def enter_searching_team(callback_query:types.CallbackQuery):
    menu.inline_keyboard.clear()
    menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))
    await dp.current_state().set_state(Conditions.ENTER_TEAM[0])
    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)
    return await bot.send_message(callback_query.from_user.id, 'Напишите название команды', reply_markup= menu)

async def get_teams(message: types.Message):

    if(len(message.text)<=1):
        return await message.answer('А ничу нормально разговаривай')
    team = Teams (message.text)

    teams = await team.search_team_in_list()
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
            db.update_teams(list_of_chosen_teams ,callback_query.from_user.id)
            list_of_chosen_teams.clear()
        else:
            answer = 'Не было выбрано ни одной команды'
        

        await dp.current_state().reset_state()
        await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
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

async def get_my_teams(callback_query: types.CallbackQuery):
    teams = db.select_my_teams(callback_query.from_user.id)
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

    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)
    return await bot.send_message(callback_query.from_user.id, answer,reply_markup=menu)

async def delete_choosen_team(callback_query : types.CallbackQuery):
    team = callback_query.data.split('_')[1]
    editing_menu = types.InlineKeyboardMarkup()
    editing_menu.add(types.InlineKeyboardButton(team , callback_data= 'chosen_'+team))\
        .add(types.InlineKeyboardButton('Удалить', callback_data='delete'))\
        .add(types.InlineKeyboardButton('Назад', callback_data= 'back_edit'))
    
    await callback_query.message.edit_reply_markup(reply_markup=editing_menu)

async def delete_one_team(callback_query : types.CallbackQuery):
    team = callback_query['message']['reply_markup']['inline_keyboard'][0][0]['text']
    db.delete_teams([team] ,callback_query.from_user.id)

    list_of_teams = [i[0]['text'] for i in menu.inline_keyboard ]

    menu.inline_keyboard.pop(list_of_teams.index(team))

    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,'Команда удалена', reply_markup=menu)

async def delete_choosen_teams(callback_query: types.CallbackQuery):
    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    teams = db.select_my_teams(callback_query.from_user.id)
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
            db.delete_teams(list_of_chosen_teams ,callback_query.from_user.id)
            list_of_chosen_teams.clear()
        else:
            answer = 'Не было выбрано ни одной команды'


        menu.inline_keyboard.clear()
        menu.add(choose_teams,delete_teams).add(my_teams).add(previous_matches,upcoming_matches)

        await dp.current_state().reset_state()
        await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
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

async def get_upcoming_matches(callback_query: types.CallbackQuery):
    id = callback_query.from_user.id
    teams = db.sql.execute("""SELECT team FROM users WHERE id =?""", (id,)).fetchall()
    list_of_matches = list(await Teams.search_upcoming_matches(teams, callback_query.from_user.id))
    string = ''
    list_of_matches.sort(key = lambda x: str(x[2]))
    menu.inline_keyboard.clear()
    menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back'))

    if(len(list_of_matches)==0):
        string = 'На ближайшее время матчей нет'
    for match in list_of_matches:
        string+=match[0]+' VS '+ match[1]+' at '+match[2]+'\n'

    await bot.answer_callback_query(callback_query.id)
    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,string, reply_markup=menu)

async def get_previous_matches(callback_query: types.CallbackQuery ):
    teams= db.sql.execute("""SELECT team FROM users WHERE id =?""", (callback_query.from_user.id,)).fetchall()
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
    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    return await bot.send_message(callback_query.from_user.id, 'Выбери команду',reply_markup=menu)

async def get_five_matches(callback_query: types.CallbackQuery):
    team = callback_query.data.split('_')[1]
    editing_menu = types.InlineKeyboardMarkup()
    editing_menu.add(types.InlineKeyboardButton('Назад', callback_data= 'back_edit'))
    
    await bot.answer_callback_query(callback_query.id)
    await delete_message(bot,callback_query.from_user.id,callback_query.message.message_id)
    return await bot.send_message(callback_query.from_user.id,\
                                  await Teams.last_5_matches(team,callback_query.from_user.id),\
                                  reply_markup=editing_menu)   

async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, "Не понял что вы хотели")

