import requests
import pandas as pd
import datetime
import numpy as np
import seaborn as sns
import base64
import json
import os

from google.cloud import pubsub_v1

def fitbit_call(request):

    # Instantiates a Pub/Sub client
    publisher = pubsub_v1.PublisherClient()
    PROJECT_ID = "fitbit_project"

    access_token = "ey....Y"
    # Set the range of days to define base line for hear rate during night time
    day_range_length = 5
    start_date = "2021-06-25"
    end_date = "2021-06-27"

    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    date_array = (start + datetime.timedelta(days=x) for x in range(0, (end-start).days))

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

    # Set PubSub topic name
    topic_name = "cgm-fitbit" 
    message = df_all[df_all.size -1:df_all.size].to_string()

    topic_path = publisher.topic_path(PROJECT_ID, topic_name)

    message_json = json.dumps({
        'data': {'message': message},
    })
    message_bytes = message_json.encode('utf-8')

    # Publishes a message
    publish_future = publisher.publish(topic_path, data=message_bytes)
    publish_future.result()  # Verify the publish succeeded


