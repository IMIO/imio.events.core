# -*- coding: utf-8 -*-
from plone.formwidget.recurrence.browser.json_recurrence import RecurrenceView

import logging

logger = logging.getLogger("imio.events.core")


class LoggingRecurrenceView(RecurrenceView):
    @property
    def json_string(self):
        logger.info(f"Event recurrence request: {self.request.form}")
        return super(LoggingRecurrenceView, self).json_string
