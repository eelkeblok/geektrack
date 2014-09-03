#! /usr/bin/env python3
import configparser
import datetime
import pprint as pp
import sys
import urllib.parse

import BaseBackend
import TimeEntry

"""Record and report time with a ticketing backend

Define commands to

- Start a timer (make entry in log)
- Stop timer
- Change description
- Starting a timer stops currently running timer, if any (but overridable with option)
- Show log. Default today, but takes parameters
- Show active timers, i.e. uncommitted (doing)
- Finish a timer by recording time to backend (e.g. Unfuddle). Default backend
  configurable, others also (bit like Drupal databases?). Commit? Commits are
  since previous commit. Optionally, don't record anything, or provide date to
  record time for.
- Show overview for backend (logged activites, grand total, compare to
   bookable, detailed or just totals per day, etc.)
- Some sort of configuration for setting bookable hours, for accurate
  calculations. Both structural (0 in weekends, 4 on mondays, 0 on holidays)
- Refer to timers by id or name. When starting timer, optionally provide
  description. Description will be default for commit message.
- What about idle time?

Examples:

$ gt start SPN-123 Research

$ gt doing
SPN-123 0:03 Research *

$ gt start SPN-456 Build solution

$ gt doing
SPN-123 0:04 Research
SPN-456 0:02 Build solution *

$ gt log
17-8-2014 21:51 START SPN-123 Research
17-8-2014 21:55 STOP SPN-123 Research
17-8-2014 21:55 START SPN-456 Build solution

$ gt commit SPN-123
Logged 0:30 on SPN-123. Description: Research

$ gt doing
SPN-456 0:02 Build solution *

$ gt log
17-8-2014 21:51 START SPN-123 Research
17-8-2014 21:55 STOP SPN-123 Research
17-8-2014 21:55 START SPN-456 Build solution
17-8-2014 21:58 COMMIT SPN-123 Research

$ gt report
Total: 0:30. Bookable 8. Difference: -7:30

$ gt report --verbose
SPN-123 0:30 Research
Total: 0:30. Bookable 8. Difference: -7:30

$ gt report --from 1-5
(One summay line per day up to today)

$ gt report --yesterday
(Same as default but for yesterday)

$ gt report --this-month
(Same as --from, for the first of the current month)

gt report --last-month
(Guess)

$ gt report --last-month --summary
(For all multi-day options, only a single summary line for the entire period)
"""

def commandDefault(argv, config):
    print("Unknown command '" + argv[1] + "'. Please supply a valid command.")
    # printHelp()
    return

def commandReport(argv, config):
    selected_backend = 'default' # This may at some point be changeable with a command line switch

    backend_config = config['backend_' + selected_backend]
    backend = BaseBackend.BaseBackend.getBackend(argv, backend_config)
    time_entries = backend.getTimeEntries(datetime.datetime.today())

    time_entries.sort(key=lambda entry: entry.booked_on)

    row_format = "{:<20} {:>2d}:{:02d} {:<50}"
    # Get the list of bookable hours per weekday. Default to 8 hours for each
    # workday.
    if 'bookable' in backend_config:
        bookable = backend_config['bookable'].split(',')
    else:
        bookable = [8,8,8,8,8,0,0]

    previous_date = None
    day_total = datetime.timedelta(0)
    for entry in time_entries:
        if entry.booked_on != previous_date:

            # If this isn't the first iteration, print the day's total
            if previous_date != None:
                print(daySummary(previous_date, day_total, bookable))
                print("")
                day_total = datetime.timedelta(0)

            print(entry.booked_on.strftime('%a %d %b %Y'))
            previous_date = entry.booked_on

        total_seconds = int(entry.duration.total_seconds())
        hours, remainder = divmod(total_seconds,60*60)
        minutes, seconds = divmod(remainder,60)
        day_total = day_total + entry.duration
        print(row_format.format(entry.ticket.identifier, hours, minutes, entry.description))

    return

def daySummary(date, total, bookable):
    return ""

if len(sys.argv) == 1:
    print("Please supply a valid command.")
#     printHelp()

command = sys.argv[1]

commandFunction = {
    "report":   commandReport
}.get(command, commandDefault)

config = configparser.ConfigParser()
config.read('settings.ini')

commandFunction(sys.argv, config)
