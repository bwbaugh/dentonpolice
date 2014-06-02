dentonpolice
============

Scrapes mug shot and inmate information from the City Jail Custody
Report page for Denton, TX and posts some of the information to Twitter
via TwitPic.

The City Jail Custody Report page that we are scraping is available
here: <http://dpdjailview.cityofdenton.com/>

Usage
-----

### Installation

1. Create a venv using Python 3 e.g.,

        virtualenv --no-site-packages --python `which python3` venv

2. Install requirements e.g., `pip install -r requirements.txt`.

### Configuration

Configuration is first required in order to post to TwitPic or Twitter.
Without configuration the program will still scrape mug shots and log
the images and inmate information to disk.

### Invocation

If the package is executed e.g., `python -m dentonpolice`, the script
will loop and continuously check the report page. To run only once,
execute the logic module's main() function.

### Tor and Proxy

By default the script retrieves the jail custody report page using a
proxy. If you don't already have a proxy setup on your machine, I would
suggest downloading and installing the Vidalia Bundle from the Tor
Project homepage. Note that if you install the Tor Browser Bundle
instead of the Vidalia Bundle bundle then you will need to install the
Polipo proxy separately. Download here: <https://www.torproject.org/>
