# -*- coding: utf-8 -*-

from imio.events.core.utils import get_agenda_uid_for_event
from imio.smartweb.common.faceted.utils import configure_faceted
import os


def set_default_agenda_uid(event):
    event.selected_agendas = event.selected_agendas or []
    uid = get_agenda_for_event(event).UID()
    if uid not in event.selected_agendas:
        event.selected_agendas = event.selected_agendas + [uid]
        event.reindexObject()
    return uid


def init_faceted(obj):
    faceted_config_path = "{}/faceted/config/events.xml".format(
        os.path.dirname(__file__)
    )
    configure_faceted(obj, faceted_config_path)


def added_entity(obj, event):
    init_faceted(obj)


def added_agenda(obj, event):
    init_faceted(obj)


def added_event(obj, event):
    set_default_agenda_uid(obj)


def modified_event(obj, event):
    set_default_agenda_uid(obj)
