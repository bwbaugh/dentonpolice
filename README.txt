Scrapes mug shot and inmate information from the City Jail Custody
Report page for Denton, TX and posts some of the information to Twitter
via TwitPic.

The City Jail Custody Report page that we are scraping is available here:
http://dpdjailview.cityofdenton.com/

Configuration is first required in order to post to TwitPic or Twitter.

If run as __main__, will loop and continuously check the report page.
To run only once, execute this module's main() function.

Required Libraries
twython3k: https://github.com/ryanmcgrath/twython
    Which in turn requires:
    httplib2: https://github.com/pakt/httplib2/tree/master/python3
    oauth2: https://github.com/hades/python-oauth2/tree/python3
