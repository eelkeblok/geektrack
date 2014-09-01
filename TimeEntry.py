import Ticket

class TimeEntry:
    def __init__(self, ticket, description, duration, booked_on):
        """Instantiate a TimeEntry object

        :param ticket:      The ticket with which this time entry is associated
        :type  ticket:      geektrack.Ticket
        :param description: Description of the time entry
        :type  description: str or unicode
        :param duration:    The amount of time booked
        :type  duration:    datetime.timedelta
        :param booked_on:   The date on which the time was booked
        :type  booked_on:   datetime.datetime
        """
        self.ticket      = ticket
        self.description = description
        self.duration    = duration
        self.booked_on   = booked_on

    def __str__(self):
        return self.ticket.identifier + " " + self.description + " " + str(self.duration) + " " + str(self.booked_on)
