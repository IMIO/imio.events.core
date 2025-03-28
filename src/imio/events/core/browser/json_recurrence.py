# -*- coding: utf-8 -*-

from imio.smartweb.common.utils import is_log_active
from imio.events.core.utils import remove_zero_interval_from_recrule
from plone.formwidget.recurrence.browser.json_recurrence import RecurrenceView

import logging

logger = logging.getLogger("imio.events.core")


class LoggingRecurrenceView(RecurrenceView):
    @property
    def json_string(self):
        if is_log_active():
            logger.info(f"Event recurrence request: {self.request.form}")
        if "rrule" in self.request.form:
            rrule = self.request.form["rrule"]
            # INTERVAL=0 is not allowed in RFC 5545
            # See https://github.com/plone/plone.formwidget.recurrence/issues/39
            self.request.form["rrule"] = remove_zero_interval_from_recrule(rrule)
        return super(LoggingRecurrenceView, self).json_string
