import asyncio
import headers
import parser_new

#start bot    

async def bot_task():
    await headers.start()

#update database
async def update_data():
    while True:
        await parser_new.parse_functions()
        await asyncio.sleep(600) 
        

#main6
async def main():
    await asyncio.gather(update_data(),bot_task())


if __name__ =='__main__':
    asyncio.get_event_loop().run_until_complete(main())
