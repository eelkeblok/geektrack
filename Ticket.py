class Ticket:
    """Describe a ticket, with which TimeEntry objects are associated"""
    def __init__(self, identifier, summary, url = None):
        """Instantiate a Ticket object

        :param identifier:  The identifier for this ticket, which can uniquely
                            identify the ticket within the backend system.
        :type  identifier:  str or unicode
        :param summary:     The ticket summary (or title)
        :type  summary:     str or unicode
        :param url:         URL for showing the ticket in a browser (optional)
        :type  url:         str or unicode
        """
        self.identifier = identifier
        self.summary    = summary
        self.url        = url
