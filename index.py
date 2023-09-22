import json, os, requests, discord, time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from discord.ui import View, Button
from discord.ext import tasks
from dotenv import load_dotenv

# Extract eltiempo data for the location
url = "https://www.tiempo.com/marbella.htm"

html = requests.get(url).content
soup = BeautifulSoup(html, "html.parser")

# Extract the 7-day forecast data
forecast_days = soup.find_all("span", class_="cuando")
forecast_weather = soup.find_all("span", class_="prediccion")
forecast_temp = soup.find_all("span", class_="temperatura")

# Build the information of every day with the following structure
# [Day , Temperature, Forecast]
forecast_data = []

# First, fetch the days and format them DD-MM
for i in range(0,7):
    try:
        # Let's format the date in DD-MM way
        # First we take care of the day, adding
        # "0" when necessary
        fetch = forecast_days[i].find("span").text
        day = fetch.split()[0]
        
        if len(day) == 1:
            day = "0" + day
            
        # Now we take care of the months,
        # translating the text to number
        month = fetch.split()[1]
        
        if month == "Ene":
            month = "01"
        if month == "Feb":
            month = "02"
        if month == "Mar":
            month = "03"
        if month == "Abr":
            month = "04"
        if month == "May":
            month = "05"
        if month == "Jun":
            month = "06"
        if month == "Jul":
            month = "07"
        if month == "Ago":
            month = "08"
        if month == "Sep":
            month = "09"
        if month == "Oct":
            month = "10"
        if month == "Nov":
            month = "11"
        if month == "Dic":
            month = "12"
        
        # Now we compose the string
        forecast_data.append([day + "-" + month])
        
    except AttributeError:
        pass

# We take the temperature data
for i in range (0,8):
    try:
        max = forecast_temp[i].find("span", class_="maxima changeUnitT").text
        min = forecast_temp[i].find("span", class_="minima changeUnitT").text
        
        temp = max + "/" + min + "C"

        forecast_data[i-1].append(temp)
    except AttributeError:
        pass
    
# And, lastly, the weeather conditions:
for i in range(0,7):
    try:
        day = forecast_weather[i].find("img", alt=True)["alt"]
        
        if "Nieba" in day:
            day = "🌫️"
        if "despejados" in day:
            day = "☀️"
        if "cubiertos" in day:
            if "lluvias" in day:
                day = "🌧️"
            else:
                day = "🌦️"
        if "nubosos" in day:
            if "lluvias" in day:
                day = "🌦️"
            else:
                day = "🌤️"
        
        forecast_data[i].append(day + " ")
    
    except AttributeError:
        pass
    
print(forecast_data)

### --- DISCORD BOT --- ###

# Declare tokens and identification points
load_dotenv()
token = os.getenv("TOKEN_BOT")
guild = int(os.getenv("CHANNEL_ID"))

# Initialize the Discord bot
# Declare intents
intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.messages = True
intents.message_content = True

# Run the bot
client = discord.Client(intents=intents)

@tasks.loop(minutes=1.0)
async def daily_message():
    now = datetime.datetime.now()
    if now.hour == 8 and now.minute == 0:
        channel = client.get_channel(guild)
        await channel.send("Good morning! This is your daily reminder.")

@daily_message.before_loop
async def before_daily_message():
    await client.wait_until_ready()

@client.event
async def on_ready():
    print("I'm in")
    daily_message.star()

@client.event
async def on_message(message):
    if message.content == "c" and message.channel.id == guild:
        channel = message.channel
        await channel.purge()
    
    if message.content == "w" and message.channel.id == guild:
        channel = message.channel  
        await channel.send("Sure! Here is this week's forecast:")
        
        dayNumber = 0
        for i in forecast_data:
            date = datetime.now() + timedelta(dayNumber)
            await channel.send(i[2] + i[1] + " " + date.strftime("%a") + " " + i[0] + "")
            dayNumber += 1
            time.sleep(0.5)
        await channel.send("I hope you'll have a great day! 🌞")
        
        button1 = Button(label=" ", url="https://weather.com/es-US/tiempo/mapas/interactive/l/36.52,-4.89", emoji="🌦️")
        button2 = Button(label=" ", url="https://www.aemet.es/es/eltiempo/prediccion/espana?a=pb", emoji="🗺️")
        button3 = Button(label=" ", url="https://www.tiempo.com/marbella.htm", emoji="🔍")
        view = View()
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)
        await channel.send(view=view)

client.run(token)