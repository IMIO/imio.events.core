# -*- coding: utf-8 -*-

from imio.events.core.utils import get_agenda_for_event
from imio.smartweb.common.faceted.utils import configure_faceted
from plone import api
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


def modified_agenda(obj, event):
    mark_current_agenda_in_events_from_other_agendas(obj, event)


def removed_agenda(obj, event):
    brains = api.content.find(selected_agendas=obj.UID())
    for brain in brains:
        event = brain.getObject()
        event.selected_agendas = [
            uid for uid in event.selected_agendas if uid != obj.UID()
        ]


def added_event(obj, event):
    container_agenda = get_agenda_for_event(obj)
    set_uid_of_referrer_agendas(obj, event, container_agenda)


def modified_event(obj, event):
    set_default_agenda_uid(obj)


def diff_list(li1, li2):
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
    return li_dif


def mark_current_agenda_in_events_from_other_agendas(obj, event):
    agendas_to_treat = []
    for d in event.descriptions:
        if "populating_agendas" in d.attributes:
            uids_in_current_agenda = [
                rf.to_object.UID() for rf in obj.populating_agendas
            ]
            agendas_to_treat = diff_list(
                getattr(obj, "old_populating_agendas", []),
                uids_in_current_agenda,
            )
    for uid_agenda in agendas_to_treat:
        agenda = api.content.get(UID=uid_agenda)
        for tuple in agenda.contentItems():
            event = tuple[1]
            if uid_agenda in uids_in_current_agenda:
                event.selected_agendas.append(obj.UID())
            else:
                event.selected_agendas = [
                    item for item in event.selected_agendas if item != obj.UID()
                ]
            event.reindexObject()
    # Keep a copy of populating_agendas
    obj.old_populating_agendas = [rf.to_object.UID() for rf in obj.populating_agendas]
    return


def set_uid_of_referrer_agendas(obj, event, container_agenda):
    obj.selected_agendas = [container_agenda.UID()]
    brains = api.relation.get(
        target=container_agenda, relationship="populating_agendas"
    )
    for brain in brains:
        obj.selected_agendas.append(brain.__parent__.UID())
