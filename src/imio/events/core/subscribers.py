# -*- coding: utf-8 -*-

from imio.events.core.utils import get_agenda_for_event
from imio.events.core.utils import get_entity_for_obj
from imio.events.core.utils import reload_faceted_config
from imio.events.core.utils import remove_zero_interval_from_recrule
from imio.smartweb.common.interfaces import IAddress
from imio.smartweb.common.utils import geocode_object
from imio.smartweb.common.utils import remove_cropping
from plone import api
from z3c.relationfield import RelationValue
from z3c.relationfield.interfaces import IRelationList
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import modified
from zope.lifecycleevent import ObjectRemovedEvent
from zope.lifecycleevent.interfaces import IAttributes


def set_default_agenda_uid(event):
    event.selected_agendas = event.selected_agendas or []
    agenda = get_agenda_for_event(event)
    if agenda is None:
        return
    uid = agenda.UID()
    if uid not in event.selected_agendas:
        event.selected_agendas = event.selected_agendas + [uid]
    event.reindexObject(idxs=["selected_agendas"])


def added_entity(obj, event):
    request = getRequest()
    reload_faceted_config(obj, request)
    agenda_ac = api.content.create(
        container=obj,
        type="imio.events.Agenda",
        title="Administration communale",
        id="administration-communale",
    )
    api.content.transition(agenda_ac, transition="publish")
    agenda_all = api.content.create(
        container=obj,
        type="imio.events.Agenda",
        title="Agenda général",
        id="agenda-general",
    )
    api.content.transition(agenda_all, transition="publish")
    intids = getUtility(IIntIds)
    setattr(
        agenda_all,
        "populating_agendas",
        [RelationValue(intids.getId(agenda_ac))],
    )
    modified(agenda_all, Attributes(IRelationList, "populating_agendas"))
    api.content.transition(obj, transition="publish")


def added_agenda(obj, event):
    request = getRequest()
    reload_faceted_config(obj, request)
    entity = get_entity_for_obj(obj)
    reload_faceted_config(entity, request)
    modified(obj, Attributes(IRelationList, "populating_agendas"))


def modified_agenda(obj, event):
    mark_current_agenda_in_events_from_other_agendas(obj, event)


def removed_agenda(obj, event):
    try:
        brains = api.content.find(selected_agendas=obj.UID())
    except api.exc.CannotGetPortalError:
        # This happen when we try to remove plone object
        return
    for brain in brains:
        event_obj = brain.getObject()
        event_obj.selected_agendas = [
            uid for uid in event_obj.selected_agendas if uid != obj.UID()
        ]
        event_obj.reindexObject(idxs=["selected_agendas"])
    request = getRequest()
    entity = get_entity_for_obj(obj)
    reload_faceted_config(entity, request)


def added_event(obj, event):
    # INTERVAL=0 is not allowed in RFC 5545
    # See https://github.com/plone/plone.formwidget.recurrence/issues/39
    obj.recurrence = remove_zero_interval_from_recrule(obj.recurrence)

    container_agenda = get_agenda_for_event(obj)
    set_uid_of_referrer_agendas(obj, container_agenda)
    if not obj.is_geolocated:
        # geocode only if the user has not already changed geolocation
        geocode_object(obj)


def modified_event(obj, event):
    # INTERVAL=0 is not allowed in RFC 5545
    # See https://github.com/plone/plone.formwidget.recurrence/issues/39
    obj.recurrence = remove_zero_interval_from_recrule(obj.recurrence)

    set_default_agenda_uid(obj)

    if not hasattr(event, "descriptions") or not event.descriptions:
        return
    for d in event.descriptions:
        if not IAttributes.providedBy(d):
            # we do not have fields change description, but maybe a request
            continue
        if d.interface is IAddress and d.attributes:
            # an address field has been changed
            geocode_object(obj)
        elif "ILeadImageBehavior.image" in d.attributes:
            # we need to remove cropping information of previous image
            remove_cropping(
                obj, "image", ["portrait_affiche", "paysage_affiche", "carre_affiche"]
            )


def moved_event(obj, event):
    if event.oldParent == event.newParent and event.oldName != event.newName:
        # item was simply renamed
        return
    if type(event) is ObjectRemovedEvent:
        # We don't have anything to do if event is being removed
        return
    container_agenda = get_agenda_for_event(obj)
    set_uid_of_referrer_agendas(obj, container_agenda)


def mark_current_agenda_in_events_from_other_agendas(obj, event):
    changed = False
    agendas_to_treat = []
    for d in event.descriptions:
        if not IAttributes.providedBy(d):
            # we do not have fields change description, but maybe a request
            continue
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
            event_obj = brain.getObject()
            if uid_agenda in uids_in_current_agenda:
                event_obj.selected_agendas.append(obj.UID())
                event_obj._p_changed = 1
            else:
                event_obj.selected_agendas = [
                    item for item in event_obj.selected_agendas if item != obj.UID()
                ]
            event_obj.reindexObject(idxs=["selected_agendas"])
    # Keep a copy of populating_agendas
    obj.old_populating_agendas = uids_in_current_agenda


def set_uid_of_referrer_agendas(obj, container_agenda):
    obj.selected_agendas = [container_agenda.UID()]
    rels = api.relation.get(target=container_agenda, relationship="populating_agendas")
    if not rels:
        obj.reindexObject(idxs=["selected_agendas"])
        return
    for rel in rels:
        obj.selected_agendas.append(rel.from_object.UID())
        obj._p_changed = 1
    obj.reindexObject(idxs=["selected_agendas"])
