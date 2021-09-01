# -*- coding: utf-8 -*-

from imio.events.core.utils import get_agenda_uid_for_event
from imio.smartweb.common.faceted.utils import configure_faceted
import os


def added_agenda(obj, event):
    faceted_config_path = "{}/faceted/config/events.xml".format(
        os.path.dirname(__file__)
    )
    configure_faceted(obj, faceted_config_path)


def added_entity(obj, event):
    added_agenda(obj, event)


def modified_event(obj, event):
    uid = get_agenda_uid_for_event(obj)
    if uid in obj.selected_agendas:
        return
    obj.selected_agendas = obj.selected_agendas + [uid]
    obj.reindexObject()


def added_event(obj, event):
    modified_event(obj, event)
