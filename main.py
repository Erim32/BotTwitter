# Standard libraries
import logging
import random
import sys
import time
from datetime import datetime, timedelta

# third party libraries
import tweepy

# Local libraries
from BotTwitter.helpers import Helpers
from BotTwitter.action import Action
from BotTwitter.manage_follow import Manage_follow
import BotTwitter.database_client

# Configuration
VERSION = 3.0
CONFIGURATION_FILE = 'configuration.yml'
DB_FILE = 'data.db'

helpers = Helpers()
# Load all configuration variables
config = helpers.load_configuration(CONFIGURATION_FILE)
# Configuration of the logging library
helpers.logging_configuration(config['logging_level'])

# if doesn't exist create database
dbman = BotTwitter.database_client.database(DB_FILE)
# if doesn't exist create users table
dbuser = dbman.Users()

while True:
    mainaccount = None
    list_name = []
    user_information_list = []
    for account in config['accounts']:
        for account_name, list_auth in account.items():
            try:
                # Extract API & ACCESS credentials
                api_key, api_secret, access_token, access_secret = list_auth
                api, user = helpers.get_user(api_key, api_secret, access_token, access_secret)

                # Creation of the user in the database if it does not already exist
                if not dbuser.user_exists(user.id_str):
                    dbuser.add_user(user.id_str, user.screen_name)

                # Get account to retrieve the list of giveaways
                if not mainaccount:
                    mainaccount = api

                list_name.append('@' + user.screen_name)
                user_information_list.append({'api': api, 'user': user})
                logging.info('Configuration completed for the account : %s', user.screen_name)

            except Exception as e:
                logging.error('Error with account : %s', account_name)
                logging.error(e)
                continue

    # If no account is available
    if not mainaccount:
        logging.error('No account available!')
        sys.exit()

    # Add Accounts to Tag
    if config['accounts_to_tag']:
        list_name += config['accounts_to_tag']
        # We don't want a duplicate
        list_name = list(set(list_name))


    # Each user do the actions, twitter will suggest different suggestion could be different
    for user_information in user_information_list:
        action = Action(config, list_name, user_information["user"], user_information["api"])
        manage_follow = Manage_follow(user_information["user"], user_information["api"])

        # We retrieve the list of actions to do
        list_action = action.search_tweets(mainaccount)
        # If there is no action
        if not list_action:
            logging.error('There is no action to do!')
            sys.exit()

        action.manage_action(list_action, manage_follow)
    time.sleep(100)
