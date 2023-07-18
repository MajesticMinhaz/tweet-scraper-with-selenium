import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from databases import TweetInfo, Base, insert_data


# Replace 'your_database_url' with the actual connection URL for your database
engine = create_engine("sqlite:///mydb.sql", echo=True)
# Create the tables if they don't exist
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()


# Assuming your Excel file is named 'tweets_data.xlsx' and data is in 'tweets_sheet' sheet
with open('output.csv', newline='') as csv_file:
    reader = csv.DictReader(csv_file)

    # Define the format of the input string
    date_format = "%Y-%m-%d %H:%M:%S"

    for row in reader:
        try:
            datetime_object = datetime.strptime(row.get('Tweet_Datetime'), date_format)
        except ValueError:
            datetime_object = None

        tweet_info = TweetInfo(
            query_url=row['Query_URL'],
            profile_url=row['Profile_URL'],
            tweet_url=row['Tweet_URL'],
            tweet_datetime=datetime_object,
            likes_count=int(row.get('Likes_Count')),
            reply_count=int(row.get('Reply_Count')),
            retweet_count=int(row.get('Retweet_Count')),
            tweet_text=row['Tweet_Text'],
        )
        insert_data(session=session, data=tweet_info)

session.close()
