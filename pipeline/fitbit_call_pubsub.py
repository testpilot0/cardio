import requests
import pandas as pd
import datetime
import numpy as np
import seaborn as sns
import base64
import json
import os

from google.cloud import pubsub_v1

def fitbit_call_pubsub(event, context):

    # Instantiates a Pub/Sub client
    publisher = pubsub_v1.PublisherClient()
    PROJECT_ID = "covid-19-271..."

    # Implicit Grant Flow
    #Enter your OAuth token in place
    #supposed to expire in 2021-03-27 - 12:40 PM - [GMT + 5:30 time zone]
    #Here the steps to find OAuth->https://dev.fitbit.com/apps/details/23B9FL
    #Use Web Developer tools in Firefox to GET token
    #Open Firefox WeB Tools and in Network
    #Tutorial here: https://dev.fitbit.com/apps/oauthinteractivetutorial?clientEncodedId=23B9FL&clientSecret=f7b6feedab6d6a385b4eee763e447df8&redirectUri=https://exain.com/fitbit/token.php&applicationType=PERSONAL

    # Go here #https://exain.com/fitbit/data.php and provide your app 23B9FL then see Heart Rate
    #Then copy long Authorize link from tutorial https://dev.fitbit.com/apps/details/23B9FL 
    #and open in Web Developer Tools and you should see token
    #https://www.fitbit.com/oauth2/authorize?response_type=token&client_id=23B9FL&redirect_uri=https%3A%2F%2Fexain.com%2Ffitbit%2Ftoken.php&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800
    #https://exain.com/fitbit/data.php

    access_token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyM0I5RkwiLCJzdWIiOiI5R0hHTlMiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyc29jIHJhY3QgcnNldCBybG9jIHJ3ZWkgcmhyIHJudXQgcnBybyByc2xlIiwiZXhwIjoxNjMzNDY0MzU3LCJpYXQiOjE2MzI4NTk2ODl9.KZQP1F5xr4TZoQhYAtETnqWKqF-Yg0FE3An806vmwkM"


    day_range_length = 5
    start_date = "2021-06-25"
    end_date = "2021-06-27"

    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d")
    print("Current Time =", current_time)
    #yesterday = datetime.today() - timedelta(days = 1 )
    date_N_days_ago = datetime.datetime.now() - datetime.timedelta(days=5)
    n_days_ago_time = date_N_days_ago.strftime("%Y-%m-%d")
    print("5 days ago Time =", n_days_ago_time)

    #Update your start and end dates here in yyyy-mm-dd format 
    #start_date = "2021-09-24"
    start_date = n_days_ago_time
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    current = datetime.datetime.strptime(current_time, "%Y-%m-%d")
    end = current

    date_array = (start + datetime.timedelta(days=x) for x in range(0, (end-start).days+1))

    day_list = []
    for date_object in date_array:
        day_list.append(date_object.strftime("%Y-%m-%d"))
        
    print("day range : ",day_list)
    df_all = pd.DataFrame()
    header = {'Authorization': 'Bearer {}'.format(access_token)}

    for single_day in day_list:
        response = requests.get("https://api.fitbit.com/1/user/-/activities/heart/date/"+ single_day +"/1d/1min/time/00:00/23:59.json", headers=header).json()
        try:
            df = pd.DataFrame(response['activities-heart-intraday']['dataset'])
            date = pd.Timestamp(single_day).strftime('%Y-%m-%d')
            df = df.set_index(pd.to_datetime(date + ' ' + df['time'].astype(str)))
            #print(df)
            df_all = df_all.append(df, sort=True)
        except KeyError as e:
            print("No data for the given date", date)
          
    del df_all['time']
    df_all[df_all.size -1:df_all.size]
    print(df_all[df_all.size -1:df_all.size])

    summary_df = (df_all['value'].resample('5s').mean())
    summary_df[summary_df.size -1:summary_df.size]
    print(summary_df[summary_df.size -1:summary_df.size])

    topic_name = "cgm-fitbit" 
    message = df_all[df_all.size -1:df_all.size].to_string().strip().replace("\n", " ").replace("    "," ").replace("       ","")
    print("Print message ", message)

    topic_path = publisher.topic_path(PROJECT_ID, topic_name)
    print("Print topic_path ", topic_path)

    #message_json = json.dumps({'data': {'message': message},})
    message_json = json.dumps({'message': message},)
    print("Print message_json ", message_json)


    message_bytes = message_json.encode('utf-8')
    print("Print message_bytes ", message_bytes)

    # Publishes a message
    publish_future = publisher.publish(topic_path, data=message_bytes)
    publish_future.result()  # Verify the publish succeeded

