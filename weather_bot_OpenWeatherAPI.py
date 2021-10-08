import telebot
from telebot import types
import time
import requests
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import http.client
from types import SimpleNamespace
import pathlib

token = '2025938640:AAFlxsDc-uYdktMUpMHiRwewiKzhKvfnn3Y'
chat_id = 248529223
DAYS_TO_FORECAST = 8

# Create bot class
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['Hello'])
@bot.message_handler(commands=['hello'])
def say_hello(message):
    bot.reply_to(message, "Hi there. I'm alive. Bot version 1.1")


@bot.message_handler(commands=['weather'])
def check_weather(message):
    continue_process = True
    if message.text == "/weather":
        bot.reply_to(message, "Enter the city name after the command.\nFor example: /weather Haifa")
    else:
        city = message.text.replace("/weather", "").strip()
        bot.reply_to(message, f"Checking weather for {city}...")
        data = ""
        request_str = "/forecast/daily?q={}&cnt={}&units=metric".format(city.replace(" ", "%20"), DAYS_TO_FORECAST)

        try:
            conn = http.client.HTTPSConnection("community-open-weather-map.p.rapidapi.com")
            headers = {
                'x-rapidapi-key': "b46ffd02a8msh377f9367d2d09e9p173166jsnb5c63a9f08c9",
                'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com"
                }
            conn.request("GET", request_str, headers=headers)

            res = conn.getresponse()
            data = res.read()
        except Exception as e:
            continue_process = False
            print(f"Failed to read data from weather API for: {city}")
            if hasattr(e, 'message'):
                bot.reply_to(message, f"Failed to read data from weather API for: {city}. Error: {e.message}")
                print("Error message", e.message)
            else:
                bot.reply_to(message, f"Failed to read data from weather API for: {city}.")
                print("Error", e)

        if continue_process:
            if len(data) > 0:
                response_str = data.decode("utf-8")
                if response_str.startswith("""{"cod":"""):
                    continue_process = False
                    print(f"Failed to retrieve weather information for {city}.\nResponse:\n{response_str}")
                    bot.reply_to(message, f"Failed to retrieve weather information for {city}\nResponse: {response_str}")
            else:
                continue_process = False
                print(f"Failed to retrieve weather information for {city}.\nNo response.")
                bot.reply_to(message, f"Failed to retrieve weather information for {city}. No response.")

        if continue_process:
            try:
                jsData = json.loads(response_str, object_hook=lambda d: SimpleNamespace(**d))

                lstDates = [datetime.fromtimestamp(x.dt).strftime("%a %d-%m") for x in jsData.list]
                lstMinTemp = [x.temp.min for x in jsData.list]
                lstMaxTemp = [x.temp.max for x in jsData.list]

                from_date = lstDates[0]
                to_date = lstDates[-1]

                dfData = {'Date': lstDates,
                          'MinTemp': lstMinTemp,
                          'MaxTemp': lstMaxTemp}

                df = pd.DataFrame(dfData)
            except Exception as e:
                continue_process = False
                bot.reply_to(message, f"Failed to handle weather information for {city}.")
                print(f"Exiting. Failed to handle weather information for {city}.")
                if hasattr(e, 'message'):
                    print("Error message", e.message)
                else:
                    print("Error", e)

        if continue_process:
            try:
                text = ""
                for index, row in df.iterrows():
                    text += "{:<15} {} - {}\n".format(row['Date'], round(row['MinTemp']), round(row['MaxTemp']))
                bot.send_message(chat_id, text)

                # file for plot image
                dir_name = pathlib.Path().parent.absolute()
                imgFile = 'weather.png'
                imgFilePath = str(dir_name) + "\\" + imgFile

                # plotting image
                title = "Temperature in " + city + ", " + from_date + " to " + to_date
                plt.plot(df['Date'], df['MaxTemp'], label='Max', color="red")
                plt.plot(df['Date'], df['MinTemp'], label='Min', color="blue")
                plt.title(title)
                plt.legend()
                plt.xticks(rotation=45)
                plt.subplots_adjust(bottom=0.2)
                plt.savefig(imgFilePath)
                plt.close()

                bot.send_chat_action(message.chat.id, 'upload_photo')
                img = open(imgFilePath, 'rb')
                bot.send_photo(chat_id, img)
                img.close()

            except Exception as e:
                bot.reply_to(message, f"Failed to display results for {city}.")
                print(f"Failed to display results for {city}.")
                if hasattr(e, 'message'):
                    print("Error message", e.message)
                else:
                    print("Error", e)


bot.polling()
