# PyScrapy
Scraper for allo search tips
Work from shell.
Has two functions:
def request_new_set(threadPool) - start new set of requests.
def request_continue_set(threadPool) - continue previous set of request.

You can enter second arg, as a number of threads for thread pool.

Uses 'peewee', 'twisted', 'requests' packages.
Has been tested with python3.5.

Example usage:
python PyScrapy.py request_new_set 50
