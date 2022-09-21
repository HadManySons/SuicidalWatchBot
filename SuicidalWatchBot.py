import praw
import sqlite3
from pathlib import Path
import random
import logging
import time
import os
import sys
from BotCreds import credsPassword, credsUserName, credsClientSecret, credsClientID, credsUserAgent

# Initialize a logging object and have some examples below from the Python
# Doc page
logging.basicConfig(filename='SuicidalWatchBot.log', level=logging.INFO)
logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") + "Starting script")

# Try to login or sleep/wait until logged in, or exit if user/pass wrong
NotLoggedIn = True
while NotLoggedIn:
    try:
        reddit = praw.Reddit(
            user_agent=credsUserAgent.strip(),
            client_id=credsClientID.strip(),
            client_secret=credsClientSecret.strip(),
            username=credsUserName.strip(),
            password=credsPassword.strip())
        print("Logged in")
        NotLoggedIn = False
    except praw.errors.InvalidUserPass:
        print("Wrong username or password")
        logging.error(time.strftime("%Y/%m/%d %H:%M:%S ") + "Wrong username or password")
        exit(1)
    except Exception as err:
        print(str(err))
        time.sleep(5)

# vars
globalCount = 0
dbFile = Path("SuicidalSubmissionRecord.db")



# check to see if database file exists
if dbFile.is_file():
    # connection to database file
    conn = sqlite3.connect("SuicidalSubmissionRecord.db")
    # database cursor object
    dbsubmissionRecord = conn.cursor()
else:  # if it doesn't, create it
    conn = sqlite3.connect("SuicidalSubmissionRecord.db")
    dbsubmissionRecord = conn.cursor()
    dbsubmissionRecord.execute('''CREATE TABLE submissions(submission text)''')

# subreddit instance of /r/AirForce. 'SuicidalWatchBot' must be changed to 'airforce' for a production version of the
# script.
subreddit = 'airforce+USMC+airnationalguard'
rInstance = reddit.subreddit(subreddit)

logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
             "Starting processing loop for subreddit: " + subreddit)

while True:
    try:
        # stream all submissions from /r/AirForce
        for InstanceSubmissions in rInstance.stream.submissions():
            globalCount += 1

            # If the post is older than about 5 months, ignore it and move on.
            if (time.time() - InstanceSubmissions.created) > 13148715:
                print("Post too old, continuing\n")
                continue

            print("Processing submission #" + str(globalCount) + ": " + InstanceSubmissions.id + "\n")

            # prints a link to the submission.
            permlink = "http://www.reddit.com" + \
                       InstanceSubmissions.permalink
            print(permlink)
            logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
                         "Processing submission: " + permlink)

            # Pulls all submissions previously submissioned on
            dbsubmissionRecord.execute(
                "SELECT * FROM submissions WHERE submission=?", (InstanceSubmissions.id,))

            id_exists = dbsubmissionRecord.fetchone()
            # Make sure we don't reply to the same submission twice or to the bot
            # itself
            if id_exists:
                print("Already processed submission: " +
                      str(InstanceSubmissions.id) + ", skipping")
                continue
            elif InstanceSubmissions.author == "SuicidalWatchBot":
                print("Author was the bot, skipping...")
                continue
            else:   
                try:
                    for i in reddit.redditor(InstanceSubmissions.author.name).submissions.new():
                        if "suicidewatch" in i.permalink.lower():
                            reddit.subreddit(InstanceSubmissions.subreddit.display_name).message("Suicide Watch Hit", f"This person: /u/{InstanceSubmissions.author.name} has recently posted in /r/SuicideWatch: http://www.reddit.com{i.permalink}")
                            logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
                                     f"Match: /u/{InstanceSubmissions.author.name} has recently posted in /r/SuicideWatch: http://www.reddit.com{i.permalink}")
                            if InstanceSubmissions.subreddit.display_name.lower() == "airforce" or "spaceforce":
                                reddit.redditor("412TW_CCC").message("Suicide Watch Hit", f"This person: /u/{InstanceSubmissions.author.name} has recently posted in /r/SuicideWatch: http://www.reddit.com{i.permalink}")
                    dbsubmissionRecord.execute('INSERT INTO submissions VALUES (?);', (InstanceSubmissions.id,))
                    conn.commit()
                except Exception as err:
                    pass

    # what to do if Ctrl-C is pressed while script is running
    except KeyboardInterrupt:
        print("Keyboard Interrupt experienced, cleaning up and exiting")
        conn.commit()
        conn.close()
        print("Exiting due to keyboard interrupt")
        logging.info(time.strftime("%Y/%m/%d %H:%M:%S ")
                     + "Exiting due to keyboard interrupt")
        exit(0)

    except Exception as err:
        print("Exception: " + str(err.with_traceback()))
        logging.error(time.strftime("%Y/%m/%d %H:%M:%S ")
                      + "Unhandled exception: " + str(err.with_traceback()))
