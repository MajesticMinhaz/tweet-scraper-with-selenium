from time import sleep
from json import loads
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from datetime import datetime, timedelta
from dotenv import dotenv_values
from undetected_chromedriver import Chrome
from selenium.webdriver.common.by import By
from databases import Base, TweetInfo, insert_data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dateutil.parser import parse


config = dotenv_values(dotenv_path='./.env')

# Create the engine and bind it to the database
engine = create_engine("sqlite:///mydb.sql", echo=True)

# Create the tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()


def convert_number(number_string):
    # Remove commas from the input number_string
    number_string = number_string.replace(',', '')

    if number_string:
        # Convert the cleaned number_string to an integer and return
        return int(number_string)
    else:
        # Return 0 if the input is an empty string
        return 0


def scrap_info(chrome_driver: Chrome):
    global url

    elements = chrome_driver.find_elements(by=By.CSS_SELECTOR, value='article[role="article"]')

    base_url = 'https://www.twitter.com{}'

    for element in elements:
        try:
            element_html = element.get_attribute('innerHTML')
            soup = BeautifulSoup(element_html, 'html.parser')

            username_section = soup.find(name='div', attrs={'data-testid': 'User-Name'})
            tweet_datetime = username_section.find(name='time')
            tweet_datetime = parse(tweet_datetime.get('datetime')) if tweet_datetime is not None else None
            links = username_section.find_all(name='a', attrs={'role': 'link'})

            profile_url = None
            tweet_url = None

            for link in links:
                if (profile_url is None or tweet_url is None) and link is not None:
                    link_href = link.get('href')

                    if '/status/' not in link_href:
                        profile_url = base_url.format(link_href)
                    else:
                        tweet_url = base_url.format(link_href)

                else:
                    continue

            tweet_text = soup.find(name='div', attrs={'data-testid': 'tweetText'})
            tweet_text = tweet_text.text.strip() if tweet_text is not None else None

            reply_count = soup.find(name='div', attrs={'role': 'button', 'data-testid': 'reply'}).text.strip()
            retweet_count = soup.find(name='div', attrs={'role': 'button', 'data-testid': 'retweet'}).text.strip()
            likes_count = soup.find(name='div', attrs={'role': 'button', 'data-testid': 'like'}).text.strip()

            reply_count = convert_number(reply_count)
            retweet_count = convert_number(retweet_count)
            likes_count = convert_number(likes_count)

            tweet_info = TweetInfo(
                query_url=url,
                profile_url=profile_url,
                tweet_url=tweet_url,
                tweet_datetime=tweet_datetime,
                likes_count=likes_count,
                reply_count=reply_count,
                retweet_count=retweet_count,
                tweet_text=tweet_text
            )

            insert_data(session=session, data=tweet_info)
        except Exception as e:
            print(e)


def scroll_bottom(chrome_driver: Chrome):
    # Get the initial page height
    old_page_height = chrome_driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom of the page
        chrome_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for a short delay to let new content load
        sleep(3)  # Adjust the time as needed.
        scrap_info(chrome_driver=chrome_driver)

        # Get the new page height after scrolling
        new_page_height = chrome_driver.execute_script("return document.body.scrollHeight")

        # If the old and new page heights are equal, it means we've reached the end
        if old_page_height == new_page_height:
            print("Reached the end of the page.")
            break

        # Update the old page height for the next iteration
        old_page_height = new_page_height


driver = Chrome(options=None)
driver.set_window_size(width=600, height=750)
driver.get('https://twitter.com/')

with open(file='cookies_ambrose.json', mode="r") as read_cookie_file:
    cookie = loads(read_cookie_file.read())

    for cookie_data in cookie:
        customized_cookie = dict()
        customized_cookie['domain'] = cookie_data.get("domain")
        customized_cookie['name'] = cookie_data.get("name")
        customized_cookie['value'] = cookie_data.get("value")

        driver.add_cookie(cookie_dict=customized_cookie)

    driver.refresh()


def get_dates_within_range(since: str, until: str) -> list:
    """
    Returns a list of dates within the specified range.

    Args:
        since (str): The start date in the format 'YYYY-MM-DD'.
        until (str): The end date in the format 'YYYY-MM-DD'.

    Returns:
        list: A list of dates in the format 'YYYY-MM-DD'.

    Raises:
        ValueError: If the input date format is invalid.

    Example:
        >>> get_dates_within_range('2020-03-01', '2020-03-05')
        ['2020-03-01', '2020-03-02', '2020-03-03', '2020-03-04', '2020-03-05']
    """
    try:
        # Convert the input strings to datetime objects
        since_date = datetime.strptime(since, '%Y-%m-%d')
        until_date = datetime.strptime(until, '%Y-%m-%d')

        # Create an empty list to store the dates within the range
        dates_within_range = []

        # Loop through the dates and add them to the list
        current_date = since_date
        while current_date <= until_date:
            # Append the formatted date to the list
            dates_within_range.append(current_date.strftime('%Y-%m-%d'))
            # Move to the next day
            current_date += timedelta(days=1)

        return dates_within_range

    except ValueError as e:
        # Handle any invalid date format errors
        raise ValueError(f"Error: {e}. Date format should be 'YYYY-MM-DD'.")


def get_next_date(date_str):
    # Convert the input date string to a datetime object
    input_date = datetime.strptime(date_str, '%Y-%m-%d')

    # Add one day to the input date
    next_date = input_date + timedelta(days=1)

    # Format the next date as a string in 'YYYY-MM-DD' format
    next_date_str = next_date.strftime('%Y-%m-%d')

    return next_date_str


def generate_twitter_search_url(query_keyword, lang, until, since):
    base_url = "https://twitter.com/search"
    query_params = {
        "q": f"{query_keyword} lang:{lang} until:{until} since:{since}",
        "src": "typed_query"
    }

    # Encode the query parameters and append to the base URL
    search_url = f"{base_url}?{urlencode(query_params)}"

    return search_url


selected_words = ["BAME", "ethnic_minority", "female", "healthcare_worker", "frontline", "NHS", "UK", "England",
                  "covid-19", "first_wave", "first_lockdown", "march_2020", "july_2020", "key_workers", "doctor",
                  "nurse", "pandemic", "PPE", "protection", "physical", "psychological", "mental", "health", "Black",
                  "Asian", "South_Asian", "Muslim", "Indian", "Pakistani", "African", "Caribbean"]

current_keyword = ["ethnic_minority"]

date_list = get_dates_within_range(since='2020-06-01', until='2020-07-30')

for keyword in current_keyword:
    for date in date_list:
        second_date = get_next_date(date_str=date)
        url = generate_twitter_search_url(keyword, 'en', second_date, date)
        driver.get(url)
        scrap_info(chrome_driver=driver)
        scroll_bottom(chrome_driver=driver)
