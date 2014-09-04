#! /usr/bin/env python3
import argparse
import calendar
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

def commandDefault(command, args, config):
    print("Unknown command '" + command + "'. Please supply a valid command.")
    # printHelp()
    return

def commandReport(command, args, config):
    selected_backend = 'default' # This may at some point be changeable with a command line switch

    backend_config = config['backend_' + selected_backend]
    backend = BaseBackend.BaseBackend.getBackend(backend_config)

    # Turn the command line arguments into from and to dates. Suffice to say, if
    # these things are mixed in illogical ways, the results are undetermined.
    # (I.e. it makes no sense to set both --yesterday and a --from date)
    fromdate = todate = today = datetime.datetime.today()

    if args.fromstring != None:
        fromdate = datetime.datetime.strptime(args.fromstring, '%Y/%m/%d')

    if args.tostring != None:
        todate = datetime.datetime.strptime(args.tostring, '%Y/%m/%d')

    # If todate is before fromdate, set fromdate to the same date. This is more
    # useful than doing it the other way around, because that way we can get a
    # single date in the past just by setting the todate
    if todate < fromdate:
        fromdate = todate

    # On to the convenience values
    if args.yesterday:
        oneday = datetime.timedelta(1)
        yesterday = today - oneday
        fromdate = todate = yesterday

    # This month
    if args.thismonth:
        todate = today
        fromdate = todate.replace(day=1)

    # Last month
    if args.lastmonth:
        month = today.month - 1
        year = today.year
        if month == 0:
            month = 12
            year = year - 1
        (weekday, numdays) = calendar.monthrange(year, month)
        fromdate = datetime.datetime(year, month, 1)
        todate = datetime.datetime(year, month, numdays)

    time_entries = backend.getTimeEntries(fromdate, todate)

    time_entries.sort(key=lambda entry: entry.booked_on)

    row_format = "{:<20} {:>5} {:<50}"

    # Get the list of bookable hours per weekday. Default to 8 hours for each
    # workday.
    if 'bookable' in backend_config:
        bookable = backend_config['bookable'].split(',')
    else:
        bookable = [8,8,8,8,8,0,0]

    grand_total = datetime.timedelta(0)
    bookable_grand_total = datetime.timedelta(0)

    # TODO: There is a very important flaw/bug in the below logic where the total
    # bookable hours is calculated; it only determines the bookable hours for
    # dates that actually have time entries. This needs to be canged ASAP.
    # Probably, we need to change things around where we loop over *dates*, not
    # time entries. We then find any time entries for that date. That also
    # allows us to DRY the code to handle the last day down below the loop.
    previous_date = None
    day_total = datetime.timedelta(0)
    for entry in time_entries:
        if entry.booked_on != previous_date:

            # If this isn't the first iteration, print the day's total
            if previous_date != None:
                bookable_today = bookableOnDate(previous_date, bookable)
                difference = day_total - bookable_today
                grand_total = grand_total + day_total
                bookable_grand_total = bookable_grand_total + bookable_today

                # Only print if we didn't get a request for just the summary
                if not args.summary:
                    print(summaryLine(day_total, bookable_today, difference))
                    print("")
                day_total = datetime.timedelta(0)

            # Only print this if we have multiple dates (and are not just
            # building a summary)
            if (fromdate != todate and not args.summary):
                print(bold(entry.booked_on.strftime('%a %d %b %Y')))
            previous_date = entry.booked_on

        day_total = day_total + entry.duration

        # Only print if we didn't get a request for just the summary and *did*
        # get a request to be verbose
        if args.verbose and not args.summary:
            print(row_format.format(entry.ticket.identifier, formatTimedelta(entry.duration), entry.description))

    # Handle the last date for totals and summary line.
    # TODO: This is basically an exact copy of what happens inside the loop.
    # Should be DRY'd up.
    bookable_today = bookableOnDate(previous_date, bookable)
    difference = day_total - bookable_today
    grand_total = grand_total + day_total
    bookable_grand_total = bookable_grand_total + bookable_today
    if not args.summary:
        print(summaryLine(day_total, bookable_today, difference))
        print("")

    # If there are several days, we want to display a total summary. This should
    # be the only thing that gets printed if a summary was requested.
    if fromdate != todate or args.summary:
        difference = grand_total - bookable_grand_total
        print(summaryLine(grand_total, bookable_grand_total, difference))
        print("")

    return

def bookableOnDate(date, bookable):
    """Return the number of bookable hours for a datetime

    :param date:     Input date
    :type  date:     datetime.datetime
    :param bookable: List of bookable hours per weekday (monday first)
    :type bookable:  list of int
    """
    return datetime.timedelta(0, 0, 0, 0, 0, int(bookable[date.weekday()]))

def summaryLine(total, bookable, difference):
    lineformat = "Total: {}. Bookable {}. Difference: {}"
    difference_string = ""

    # Color the difference
    seconds_difference = difference.total_seconds()

    if (seconds_difference < 0):
        difference_string = color(1, formatTimedelta(difference))
    elif (seconds_difference > 0):
        difference_string = color(2, formatTimedelta(difference))
    else:
        difference_string = formatTimedelta(difference)

    return bold(lineformat.format(
        formatTimedelta(total),
        formatTimedelta(bookable),
        difference_string))


def formatTimedelta(delta):
    total_seconds = int(delta.total_seconds())

    # This is probably a rather convoluted way of handling negative delta's, but
    # can't come up with something better right now.
    negative = False
    if (total_seconds < 0):
        negative = True
        total_seconds = total_seconds * -1

    hours, remainder = divmod(total_seconds,60*60)
    minutes, seconds = divmod(remainder,60)

    if (negative):
        hours = hours * -1

    return "{:d}:{:02d}".format(hours, minutes)

# Formatting functions from http://www.darkcoding.net/software/pretty-command-line-console-output-on-unix-in-python-and-go-lang/
def bold(msg):
    return u'\033[1m%s\033[0m' % msg

def color(this_color, string):
    return "\033[3" + str(this_color) + "m" + string + "\033[0m"

if len(sys.argv) == 1:
    print("Please supply a valid command.")
#     printHelp()

parser = argparse.ArgumentParser(description='Record time spent in a ticketing backend and run reports')
subparsers = parser.add_subparsers(help='sub-command help')

# Create the parser for the report command
parser_report = subparsers.add_parser('report', description='Run reports against a backend')
parser_report.add_argument('--verbose', action='store_const',
                   const=True, default=False,
                   help='Show details on individual time entries')
parser_report.add_argument('--from', dest="fromstring", help='From date, formatted yyyy/mm/dd')
parser_report.add_argument('--to', dest="tostring", help='To date, formatted yyyy/mm/dd')
parser_report.add_argument('--yesterday', action='store_const',
                   const=True, default=False,
                   help='Show information for the previous day')
parser_report.add_argument('--this-month', dest="thismonth", action='store_const',
                   const=True, default=False,
                   help='Show information for the current day up until today')
parser_report.add_argument('--last-month', dest="lastmonth", action='store_const',
                   const=True, default=False,
                   help='Show information for the previous month')
parser_report.add_argument('--summary', action='store_const',
                   const=True, default=False,
                   help='Show only a single summary line for the requested period')

args = parser.parse_args()

command = sys.argv[1]

commandFunction = {
    "report":   commandReport
}.get(command, commandDefault)

config = configparser.ConfigParser()
config.read('settings.ini')

commandFunction(command, args, config)
