import base64
import datetime
import json
import pprint as pp
import urllib.request

import BaseBackend
import Ticket
import TimeEntry

class UnfuddleBackend(BaseBackend.BaseBackend):
    userid = None
    tickets = {}  # Dictionary of tickets, indexed by ticket ID
    projects = {} # Dictionary of projects, index by project ID

    def __init__(self, config):
        self.config = config
        return

    def getTimeEntries(self, from_date, to_date = None):
        userid = self.getUserId()

        # Get all time entries for the given time range
        from_date_formatted = from_date.strftime('%Y/%m/%d')

        if (to_date == None):
            to_date = from_date
        to_date_formatted = to_date.strftime('%Y/%m/%d')

        url = 'https://' + self.config['domain'] + '.unfuddle.com/api/v1/account/time_invested.json?group_by=project&start_date=' + from_date_formatted + '&end_date=' + to_date_formatted
        headers = self.getAuthorizationHeaders()
        req = urllib.request.Request(url, None, headers)

        response = urllib.request.urlopen(req)
        payload = response.read()

        data = json.loads(payload.decode('UTF-8'))

        time_entries = []

        for project in data['groups']:
            for entry in project['time_entries']:
                project_data = self.getProjectByName(project['title'])
                ticket = self.getTicket(entry['ticket_id'], project_data['id'])
                description = entry['description']
                duration = datetime.timedelta(0, 0, 0, 0, 0, entry['hours'])
                booked_on = datetime.datetime.strptime(entry['date'], "%Y-%m-%d")
                time_entry = TimeEntry.TimeEntry(
                    ticket, description, duration, booked_on)
                time_entries.append(time_entry)

        return time_entries

    def getUserId(self):
        if (self.userid == None):
            # Find the current user
            url = "https://" + self.config['domain'] + ".unfuddle.com/api/v1/people/current.json"
            headers = self.getAuthorizationHeaders()

            req = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(req)
            payload = response.read()

            data = json.loads(payload.decode('UTF-8'))
            self.userid = data['id']

        return self.userid

    def getAuthorizationHeaders(self):
        authorization = self.config['user'] + ":" + self.config['password']
        authorization = base64.b64encode(authorization.encode('UTF-8'))
        authorization = authorization.decode(encoding='UTF-8')
        headers = { 'Authorization' : "Basic " +  authorization}

        return headers

    def getTicket(self, ticket_id, project_id):
        if ticket_id not in self.tickets:
            # Find the current user
            url = "https://" + self.config['domain'] + ".unfuddle.com/api/v1/projects/" + str(project_id) + "/tickets/" + str(ticket_id) + ".json"
            headers = self.getAuthorizationHeaders()

            req = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(req)
            payload = response.read()

            data = json.loads(payload.decode('UTF-8'))

            project = self.getProjectById(project_id)

            ticket_url = "https://" + self.config['domain'] + ".unfuddle.com/a#/projects/" + str(project_id) + "/tickets/by_number/" + str(data['number'])
            ticket = Ticket.Ticket(project['short_name'] + '-' + str(data['number']), data['summary'], ticket_url)
            self.tickets[ticket_id] = ticket

        return self.tickets[ticket_id]

    def getProjectByName(self, project_name):
        self.initProjects()

        for project in self.projects:
            if project['title'] == project_name:
                return project

        raise KeyError('Unknown project name')

    def getProjectById(self, project_id):
        self.initProjects()

        for project in self.projects:
            if project['id'] == project_id:
                return project

        raise KeyError('Unknown project id')

    def initProjects(self):
        if len(self.projects) == 0:
            url = "https://" + self.config['domain'] + ".unfuddle.com/api/v1/projects.json"
            headers = self.getAuthorizationHeaders()

            req = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(req)
            payload = response.read()

            data = json.loads(payload.decode('UTF-8'))
            self.projects = data
