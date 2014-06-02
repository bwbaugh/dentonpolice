# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Scrapes mug shot and inmate information from the City Jail Custody
Report page for Denton, TX and posts some of the information to Twitter
via TwitPic.

The City Jail Custody Report page that we are scraping is available here:
http://dpdjailview.cityofdenton.com/

Configuration is first required in order to post to TwitPic or Twitter.

If run as __main__, will loop and continuously check the report page.
To run only once, execute this module's main() function.
"""
import logging
import time

from dentonpolice.logic import main


# How often to check the City Jail Custody Report webpage
SECONDS_BETWEEN_CHECKS = 60 * 5

# Logging level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)


# Continuously checks the custody report page every SECONDS_BETWEEN_CHECKS.
logging.info("Starting main loop.")
while True:
    try:
        main()
        logging.debug("Main loop: going to sleep for %s seconds",
                      SECONDS_BETWEEN_CHECKS)
        time.sleep(SECONDS_BETWEEN_CHECKS)
    except KeyboardInterrupt:
        print("Bye!")
        logging.shutdown()
        break
