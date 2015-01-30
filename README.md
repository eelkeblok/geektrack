# README #

An extremely ambitious command line time track tool that currently only reports time invested for Unfuddle.

You need python 3 to run this. Configure by copying the file settings.example.ini to settings.ini and fill in your Unfuddle credentials.

The only command that currently works is "report"

# Commands #

## Report

Reports time entries. Defaults to today.

Example:


```
#!shell

$ gt report --yesterday
```

### Optional arguments
```
  -h, --help         show this help message and exit
  --verbose          Show details on individual time entries
  --from FROMSTRING  From date, formatted yyyy/mm/dd
  --to TOSTRING      To date, formatted yyyy/mm/dd
  --yesterday        Show information for the previous day
  --this-month       Show information for the current day up until today
  --last-month       Show information for the previous month
  --summary          Show only a single summary line for the requested period
```