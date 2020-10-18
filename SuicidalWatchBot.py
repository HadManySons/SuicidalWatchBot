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

# Get the PID of this process
pid = str(os.getpid())
pidfile = "SuicidalWatchBot.pid"

# Exit if a version of the script is already running
if os.path.isfile(pidfile):
    print(pidfile + " already running, exiting")
    sys.exit()

# Create the lock file for the script
open(pidfile, 'w').write(pid)

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
rAirForce = reddit.subreddit(subreddit)

logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
             "Starting processing loop for subreddit: " + subreddit)

while True:
    try:
        # stream all submissions from /r/AirForce
        for rAirForceSubmissions in rAirForce.stream.submissions():
            globalCount += 1

            # If the post is older than about 5 months, ignore it and move on.
            if (time.time() - rAirForceSubmissions.created) > 13148715:
                print("Post too old, continuing")
                continue

            print("\nsubmissions processed since start of script: " + str(globalCount))
            print("Processing submission: " + rAirForceSubmissions.id)

            # prints a link to the submission.
            permlink = "http://www.reddit.com" + \
                       rAirForceSubmissions.permalink
            print(permlink)
            logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
                         "Processing submission: " + permlink)

            # Pulls all submissions previously submissioned on
            dbsubmissionRecord.execute(
                "SELECT * FROM submissions WHERE submission=?", (rAirForceSubmissions.id,))

            id_exists = dbsubmissionRecord.fetchone()
            print(id_exists)
            # Make sure we don't reply to the same submission twice or to the bot
            # itself
            if id_exists:
                print("Already processed submission: " +
                      str(rAirForceSubmissions.id) + ", skipping")
                continue
            elif rAirForceSubmissions.author == "SuicidalWatchBot":
                print("Author was the bot, skipping...")
                continue
            else:
                for i in reddit.redditor(rAirForceSubmissions.author.name).submissions.new():
                    if "suicidewatch" in i.permalink.lower():
                        reddit.subreddit(rAirForceSubmissions.subreddit.display_name).message("Suicide Watch Hit", f"This person: /u/{rAirForceSubmissions.author.name} has recently posted in /r/SuicideWatch: http://www.reddit.com/{i.permalink}")
                        print("match")

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

    finally:
        os.unlink(pidfile)
