from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from datetime import date
import requests
import pandas as pd
import numpy as np
import pymongo
import json


app = Flask(__name__)


# To renderHomepage
@app.route('/', methods=['POST', 'GET'])
def home_page():
    return render_template('home.html')


# This will be called from UI
@app.route('/results', methods=['POST'])
def weather_report():
    if request.method == 'POST':

        city_name = request.form['Name of City'].replace(' ','').lower()
        print(city_name)
        State_Id = request.form['State ID']
        print(State_Id)


        dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
        dbname = 'us_cities'
        db = dbConn[dbname]
        collection_name = 'us_cities_lat_lng'
        collection = db[collection_name]
        my_db_query = {'city': city_name, 'state_id': State_Id}
        result = list(collection.find(my_db_query))
        print(result)
        if not result:
            return 'your search criteria is wrong - either the city spelling or wrong state ID or city not in database- Go to Home to Search again'
        else:
            latitude = str(result[0]['lat'])
            longitude = str(result[0]['lng'])
            print(latitude,longitude)
            url = 'https://forecast.weather.gov/MapClick.php?lat='+ latitude + '&lon=' +longitude
            landing_data = requests.get(url)
            Day = []
            Weather = []
            Temp = []
            #weather_report = []
            if landing_data.status_code == requests.codes.ok:
                landing_soup = BeautifulSoup(landing_data.content, 'html.parser')
                week = landing_soup.findAll("div", {"class": "tombstone-container"})

                for days in week:
                    temp = days.find('p', {'class': 'temp'})
# this condition is checked to avoid a tombstone box for national advisory
                    if temp:
                        day = days.find('p', {'class': 'period-name'})
                        Day.append(day.text)
                        weather = days.find('p', {'class': 'short-desc'})
                        Weather.append(weather.text)
                        Temp.append(temp.text)
                    else:
                        continue
                     # my_dict = {'Day': day.text,'Weather': weather.text,'Temperature': temp.text}
                     # weather_report.append(my_dict)
# The weather report list changes length based on the when we access the national weather site, based on which the below code function
                from datetime import date
                today = date.today()
                if len(Day) == 8:
                    Dates = pd.Series(pd.date_range(today, periods=4)).repeat([2, 2, 2, 2])
                elif len(Day) == 9:
                    Dates = pd.Series(pd.date_range(today, periods=5)).repeat([2, 2, 2, 2, 1])


                weather_df = pd.DataFrame({'Day': Day, 'Weather': Weather, 'Temperature': Temp})
                weather_df = weather_df.reset_index(drop=True)
                today = date.today()
                weather_df.index = Dates
                weather_df.reset_index()
                weather_df['Date'] = weather_df.index
                weather_list = weather_df.T.to_dict().values()
                print(weather_list)
                return render_template('results.html', results=weather_list)

            else:
                return 'your search criteria is wrong - either the city spelling or wrong state ID or city not in database- Go to Home to Search again'
if __name__ == '__main__':
    app.run(debug=True)
