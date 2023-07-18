from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError


Base = declarative_base()


class TweetInfo(Base):
    """Represents information about a Tweet Info."""

    __tablename__ = "tweet_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_url = Column("Query_URL", String, nullable=False)
    profile_url = Column("Profile_URL", String, nullable=True)
    tweet_url = Column("Tweet_URL", String, nullable=True, unique=True)
    tweet_datetime = Column("Date_Time", DateTime, nullable=True)
    likes_count = Column("Likes_Count", Integer, nullable=True)
    reply_count = Column("Reply_Count", Integer, nullable=True)
    retweet_count = Column("Retweet_Count", Integer, nullable=True)
    tweet_text = Column("Tweet_Text", String, nullable=True)

    def __init__(
            self,
            query_url: str or None,
            profile_url: str or None,
            tweet_url: str or None,
            tweet_datetime: datetime or None,
            likes_count: str or None,
            reply_count: str or None,
            retweet_count: str or None,
            tweet_text: str or None = None
    ):
        self.query_url = query_url
        self.profile_url = profile_url
        self.tweet_url = tweet_url
        self.tweet_datetime = tweet_datetime
        self.likes_count = likes_count
        self.reply_count = reply_count
        self.reply_count = reply_count
        self.retweet_count = retweet_count
        self.tweet_text = tweet_text


def insert_data(session, data):
    """
    Insert data into the database, handling IntegrityError.

    Args:
        session (sqlalchemy.orm.Session): The SQLAlchemy session object.
        data: The data to be inserted.

    Raises:
        sqlalchemy.exc.IntegrityError: If a unique constraint is violated.

    Returns:
        None
    """
    try:
        # Add the data to the session
        session.add(data)
        # Commit the transaction
        session.commit()
        print("Data inserted successfully.")
    except IntegrityError:
        # Rollback the transaction in case of IntegrityError
        session.rollback()
        print("Data already exists. Insertion aborted.")
