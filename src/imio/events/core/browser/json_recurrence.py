# -*- coding: utf-8 -*-
from plone.formwidget.recurrence.browser.json_recurrence import RecurrenceView

import logging

logger = logging.getLogger("imio.events.core")


class LoggingRecurrenceView(RecurrenceView):
    @property
    def json_string(self):
        logger.info(f"Event recurrence request: {self.request.form}")
        if "rrule" in self.request.form:
            rrule = self.request.form["rrule"]
            # INTERVAL=0 is not allowed in RFC 5545
            # See https://github.com/plone/plone.formwidget.recurrence/issues/39
            self.request.form["rrule"] = rrule.replace("INTERVAL=0", "INTERVAL=1")
        return super(LoggingRecurrenceView, self).json_string
