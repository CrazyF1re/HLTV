import handlers
import asyncio
import parser_new
import time

#start bot    
async def bot_task():
    await handlers.start()

#update database
async def update_data():
    while True:
        parser_new.parse_functions()
        print('parsing succeed '+ str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        await asyncio.sleep(600) 

#main
async def main():
    await asyncio.gather(update_data(),bot_task())


if __name__ =='__main__':
    
    asyncio.get_event_loop().run_until_complete(main())
