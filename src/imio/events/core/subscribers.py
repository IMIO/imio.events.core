# -*- coding: utf-8 -*-

from imio.events.core.utils import get_agenda_for_event
from imio.smartweb.common.faceted.utils import configure_faceted
from imio.smartweb.common.interfaces import IAddress
from imio.smartweb.common.utils import geocode_object
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
    try:
        brains = api.content.find(selected_agendas=obj.UID())
    except api.exc.CannotGetPortalError:
        # This happen when we try to remove plone object
        return
    for brain in brains:
        event = brain.getObject()
        event.selected_agendas = [
            uid for uid in event.selected_agendas if uid != obj.UID()
        ]


def added_event(obj, event):
    container_agenda = get_agenda_for_event(obj)
    set_uid_of_referrer_agendas(obj, event, container_agenda)
    if not obj.is_geolocated:
        # geocode only if the user has not already changed geolocation
        geocode_object(obj)


def modified_event(obj, event):
    set_default_agenda_uid(obj)

    if not hasattr(event, "descriptions") or not event.descriptions:
        return
    for d in event.descriptions:
        if d.interface is IAddress and d.attributes:
            # an address field has been changed
            geocode_object(obj)
            return


def mark_current_agenda_in_events_from_other_agendas(obj, event):
    changed = False
    agendas_to_treat = []
    for d in event.descriptions:
        if "populating_agendas" in d.attributes:
            changed = True
            uids_in_current_agenda = [
                rf.to_object.UID() for rf in obj.populating_agendas
            ]
            old_uids = getattr(obj, "old_populating_agendas", [])
            agendas_to_treat = set(old_uids) ^ set(uids_in_current_agenda)
            break
    if not changed:
        return
    for uid_agenda in agendas_to_treat:
        agenda = api.content.get(UID=uid_agenda)
        event_brains = api.content.find(context=agenda, portal_type="imio.events.Event")
        for brain in event_brains:
            event = brain.getObject()
            if uid_agenda in uids_in_current_agenda:
                event.selected_agendas.append(obj.UID())
            else:
                event.selected_agendas = [
                    item for item in event.selected_agendas if item != obj.UID()
                ]
            event.reindexObject(idxs=["selected_agendas"])
    # Keep a copy of populating_agendas
    obj.old_populating_agendas = uids_in_current_agenda


def set_uid_of_referrer_agendas(obj, event, container_agenda):
    obj.selected_agendas = [container_agenda.UID()]
    rels = api.relation.get(target=container_agenda, relationship="populating_agendas")
    for rel in rels:
        obj.selected_agendas.append(rel.from_object.UID())
