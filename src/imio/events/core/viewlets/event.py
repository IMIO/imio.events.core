# -*- coding: utf-8 -*-

from plone import api
from plone.app.layout.viewlets import common


class BringEventIntoAgendasViewlet(common.ViewletBase):

    def available(self):
        is_authenticated = api.user.get_current().has_role("Authenticated")
        is_not_the_form = "bring_event_into_agendas_form" not in " ".join(
            self.request.steps
        )
        return is_authenticated and is_not_the_form
