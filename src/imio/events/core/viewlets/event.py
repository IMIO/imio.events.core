# -*- coding: utf-8 -*-

from imio.events.core.contents import IEntity
from plone import api
from plone.app.layout.viewlets import common


class BringEventIntoAgendasViewlet(common.ViewletBase):

    def available(self):
        form_name = "bring_event_into_agendas_form"
        is_not_the_form = form_name not in " ".join(self.request.steps)
        return (
            is_not_the_form
            and user_is_contributor_in_entity_which_authorize_to_bring_events()
        )


def user_is_contributor_in_entity_which_authorize_to_bring_events():
    user = api.user.get_current() or None
    if user is None:
        return False
    has_permission = False
    brains = api.content.find(object_provides=IEntity.__identifier__)
    for brain in brains:
        entity = brain.getObject()
        if (
            api.user.get_permissions(user=user, obj=entity).get("Modify portal content")
            is True
        ):
            if entity.authorize_to_bring_event_anywhere:
                has_permission = True
                break
    return has_permission
