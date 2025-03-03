# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from eea.facetednavigation.settings.interfaces import IHidePloneLeftColumn
from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEntity
from imio.smartweb.common.faceted.utils import configure_faceted
from plone import api
from plone.event.recurrence import recurrence_sequence_ical
from plone.restapi.serializer.converters import json_compatible
from Products.CMFPlone.utils import parent
from pytz import utc
from zope.component import getMultiAdapter
from zope.interface import noLongerProvides

import copy
import dateutil
import os


def get_entity_for_obj(obj):
    while not IEntity.providedBy(obj) and obj is not None:
        obj = parent(obj)
    entity = obj
    return entity


def get_agenda_for_event(event):
    obj = event
    while not IAgenda.providedBy(obj) and obj is not None:
        obj = parent(obj)
    agenda = obj
    return agenda


def get_agendas_uids_for_faceted(obj):
    if IAgenda.providedBy(obj):
        return [obj.UID()]
    elif IEntity.providedBy(obj):
        brains = api.content.find(context=obj, portal_type="imio.events.Agenda")
        return [b.UID for b in brains]
    else:
        raise NotImplementedError


def reload_faceted_config(obj, request):
    faceted_config_path = "{}/faceted/config/events.xml".format(
        os.path.dirname(__file__)
    )
    configure_faceted(obj, faceted_config_path)
    agendas_uids = "\n".join(get_agendas_uids_for_faceted(obj))
    request.form = {
        "cid": "agenda",
        "faceted.agenda.default": agendas_uids,
    }
    handler = getMultiAdapter((obj, request), name="faceted_update_criterion")
    handler.edit(**request.form)
    if IHidePloneLeftColumn.providedBy(obj):
        noLongerProvides(obj, IHidePloneLeftColumn)


def get_start_date(event):
    return datetime.fromisoformat(event["start"])


# just expand occurences. No filtering here

def expand_occurences(events, range="min"):
    expanded_events = []

    for event in events:
        start_date = dateutil.parser.parse(event["first_start"]).astimezone(utc)
        end_date = dateutil.parser.parse(event["first_end"]).astimezone(utc)

        # Mise à jour des dates en format JSON
        event["start"] = json_compatible(start_date)
        event["end"] = json_compatible(end_date)

        if not event["recurrence"]:
            expanded_events.append(event)
            continue

        # Définition des bornes temporelles
        from_, until = datetime.now(utc), start_date + timedelta(days=365 * 5)
        if range == "min":
            from_ = None
        elif range == "min:max":
            from_ = datetime.now() # min(start_date, datetime.now(utc))
        elif range == "max":
            from_, until = start_date - timedelta(days=365), datetime.now(utc)
               
        start_dates = recurrence_sequence_ical(
            start=start_date,
            recrule=event["recurrence"],
            from_=from_,
            until=until,
        )
        if event["whole_day"] or event["open_end"]:
            duration = timedelta(hours=23, minutes=59, seconds=59)
        else:
            duration = end_date - start_date

        # Création des nouvelles occurrences avec conservation de l'heure originale
        for occurence_start in start_dates:
            occurence_start = occurence_start.replace(hour=start_date.hour, minute=start_date.minute, second=start_date.second)  # 🔥 On s'assure que l'heure est correcte
            start_time = datetime.combine(datetime.today(), start_date.time())
            end_time = datetime.combine(datetime.today(), end_date.time())
            duration = end_time - start_time
            new_event = {
                **event,
                "start": json_compatible(occurence_start),
                "end": json_compatible(occurence_start + duration),
            }
            expanded_events.append(new_event)

    return expanded_events


def remove_zero_interval_from_recrule(recrule):
    if not recrule:
        return recrule
    recrule = recrule.replace(";INTERVAL=0", "")
    return recrule
