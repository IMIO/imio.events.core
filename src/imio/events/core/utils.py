# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from eea.facetednavigation.settings.interfaces import IHidePloneLeftColumn
from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEntity
from imio.smartweb.common.config import DIRECTORY_URL
from imio.smartweb.common.faceted.utils import configure_faceted
from imio.smartweb.common.utils import get_json
from imio.smartweb.common.utils import is_log_active
from plone import api
from plone.event.recurrence import recurrence_sequence_ical
from plone.restapi.serializer.converters import json_compatible
from Products.CMFPlone.utils import parent
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import noLongerProvides

import dateutil
import logging
import os
import pytz

brussels = pytz.timezone("Europe/Brussels")

logger = logging.getLogger("imio.events.core")


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


def _resolve_sponsors(uids):
    """Batch-fetch sponsor data for a list of directory contact UIDs."""
    if not uids:
        return {}
    params = "&".join(f"UID={uid}" for uid in uids)
    url = f"{DIRECTORY_URL}/@search?{params}&fullobjects=true"
    data = get_json(url, None, 12) or {}
    result = {}
    for contact in data.get("items", []):
        uid = contact.get("UID")
        if not uid:
            continue
        logo = None
        logo_data = contact.get("logo")
        if logo_data:
            scales = logo_data.get("scales") or {}
            logo = (scales.get("large") or {}).get("download") or logo_data.get(
                "download"
            )
        result[uid] = {
            "uid": uid,
            "name": contact.get("title") or "",
            "logo": logo,
            "url": contact.get("@id"),
        }
    return result


def get_directory_contact_lines(uid):
    """Fetch phones / mails / urls of a directory contact (by UID).

    Returns a dict of lists mirroring the imio.directory.Contact JSON, keeping
    only the columns we display. Empty structure when uid is falsy or the
    directory is unreachable/empty.
    """
    empty = {"phones": [], "mails": [], "urls": []}
    if not uid:
        return empty
    url = "{}/@search?UID={}&fullobjects=true".format(DIRECTORY_URL, uid)
    data = get_json(url, None, 12)
    items = (data or {}).get("items") or []
    if not items:
        return empty
    contact = items[0]
    phones = [
        {
            "label": p.get("label") or "",
            "type": p.get("type") or "",
            "number": p.get("number") or "",
        }
        for p in (contact.get("phones") or [])
    ]
    mails = [
        {
            "label": m.get("label") or "",
            "type": m.get("type") or "",
            "mail_address": m.get("mail_address") or "",
        }
        for m in (contact.get("mails") or [])
    ]
    urls = [
        {
            "type": u.get("type") or "",
            "url": u.get("url") or "",
        }
        for u in (contact.get("urls") or [])
    ]
    return {"phones": phones, "mails": mails, "urls": urls}


def _selected_values(rows, value_key):
    """Values of the rows that were ticked, used to preserve ticks on refresh."""
    return {
        row.get(value_key)
        for row in (rows or [])
        if row.get("selected") and row.get(value_key)
    }


def merge_directory_lines(existing_rows, fresh_rows, value_key):
    """Return the freshly fetched rows as datagrid dicts, re-ticking the lines
    that were ticked before (matched by their value, e.g. the phone number)."""
    keep = _selected_values(existing_rows, value_key)
    merged = []
    for row in fresh_rows:
        new_row = dict(row)
        new_row["selected"] = row.get(value_key) in keep
        merged.append(new_row)
    return merged


def refresh_contact_informations(contact):
    """(Re)populate a Contact's phones/mails/urls from its linked directory
    contact, preserving previously-ticked lines."""
    uid = getattr(contact, "related_contact", None)
    lines = get_directory_contact_lines(uid)
    contact.phones = merge_directory_lines(
        getattr(contact, "phones", None), lines["phones"], "number"
    )
    contact.mails = merge_directory_lines(
        getattr(contact, "mails", None), lines["mails"], "mail_address"
    )
    contact.urls = merge_directory_lines(
        getattr(contact, "urls", None), lines["urls"], "url"
    )


# If we want to further optimize the retrieval of a single event without using fullobjects=1
# , then this function will be useful.
def hydrate_ids_for(field_name, event, vocabulary):
    current_lang = event.get("language", "fr")
    raw_ids = event.get(field_name, [])
    result = []
    if not raw_ids:
        return raw_ids
    for term_id in raw_ids:
        term = vocabulary.getTermByToken(term_id)
        result.append(
            {
                "title": translate(term.title, target_language=current_lang),
                "token": term.token,
            }
        )
    return result


# If we want to further optimize the retrieval of a single event without using fullobjects=1
# , then this function will be useful.
# def get_gallery_images(event):
#     pass


def _uid_from_sponsor_item(item):
    """Return the UID string from a sponsor item.

    With fullobjects=False the catalog returns plain UID strings.
    With fullobjects=True the full serializer returns {"token": uid, ...} dicts
    (same as event_type, country, etc. in that context).
    """
    if isinstance(item, dict):
        return item.get("token") or item.get("UID")
    return item


# just expand occurences. No filtering here
def expand_occurences(events, range="min"):
    expanded_events = []
    all_sponsor_uids = list(
        {
            _uid_from_sponsor_item(item)
            for event in events
            if event
            for item in (event.get("event_sponsors") or [])
            if _uid_from_sponsor_item(item)
        }
    )
    sponsors_by_uid = _resolve_sponsors(all_sponsor_uids)
    # iam_vocabulary = IAmVocabulary()
    # topics_vocabulary = TopicsVocabulary()
    for event in events:
        if event is None:
            continue
        first_start = event.get("first_start") or event.get("start")
        first_end = event.get("first_end") or event.get("end")
        start_date = dateutil.parser.parse(first_start).astimezone(brussels)
        end_date = dateutil.parser.parse(first_end).astimezone(brussels)
        event["geolocation"] = {
            "latitude": event.get("latitude", ""),
            "longitude": event.get("longitude", ""),
        }
        # without fullobjects
        # event["iam"] = hydrate_ids_for("iam", event, iam_vocabulary)
        # event["topics"] = hydrate_ids_for("topics", event, topics_vocabulary)

        if event.get("image_scales", None):
            id_event = event["@id"]
            url_image = event["image_scales"]["image"][0]["download"]
            event["image_scales"]["image"][0][
                "download"
            ] = url_image  # f"{id_event}{url_image}"
            scales = event["image_scales"]["image"][0]["scales"]
            for k, v in scales.items():
                download = v["download"]
                v["download"] = f"{id_event}/{download}"
            event["image"] = event["image_scales"]["image"][0]
            del event["image_scales"]
        event["has_leadimage"] = False
        if event.get("image", None):
            event["has_leadimage"] = True
        sponsor_items = event.get("event_sponsors") or []
        event["event_sponsors"] = [
            sponsors_by_uid[uid]
            for item in sponsor_items
            for uid in [_uid_from_sponsor_item(item)]
            if uid and uid in sponsors_by_uid
        ]
        # Ensure event start/end are in same date format than other json dates
        event["start"] = json_compatible(start_date)
        event["end"] = json_compatible(end_date)
        if event["whole_day"]:
            # whole_day ⇒ fin = 23:59:59 du dernier jour en TZ locale (Brussels).
            # L'ancienne formule (end-start)+24h doublait la durée quand Plone
            # avait déjà stocké end à 23:59 du dernier jour.
            end_basis = end_date if end_date else start_date
            event["end"] = json_compatible(
                end_basis.replace(hour=23, minute=59, second=59, microsecond=0)
            )
        if not event["recurrence"]:
            expanded_events.append(event)
            continue
        # Compute duration before recurrence_sequence_ical: it uses it in
        # rset.between(from_ - duration, until) so that ongoing occurrences
        # (started before now but not yet ended) are included.
        if event["whole_day"]:
            start_day = dateutil.parser.parse(first_start).date()
            end_day = dateutil.parser.parse(first_end).date()
            day_diff = (end_day - start_day).days
            duration = timedelta(days=day_diff, hours=23, minutes=59, seconds=59)
        else:
            duration = end_date - start_date
        # optimize query with "until" to avoid to go through all recurrences
        # if we want "future events", we get occurences to 1 years in the future
        # if we want "past events", we get occurences to 1 year in the past
        until = from_ = None
        until = start_date + timedelta(days=365)
        # for now min:max is only supported for future events
        if range == "min":
            from_ = datetime.now(brussels)
            until = from_ + timedelta(days=365)
        if range == "min:max":
            from_ = datetime.now(brussels)
        elif range == "max":
            from_ = start_date - timedelta(days=365)
            until = datetime.now(brussels)
        start_dates = recurrence_sequence_ical(
            start=start_date,
            recrule=event["recurrence"],
            from_=from_,
            until=until,
            duration=duration,
        )
        if is_log_active():
            logger.warning(
                f"FROM = {from_} , UNTIL = {until} , range = {range}, start_date = {start_date}, recrule = {event['recurrence']}"
            )
        for occurence_start in start_dates:
            new_event = {**event}
            new_event["start"] = json_compatible(occurence_start)
            new_event["end"] = json_compatible(occurence_start + duration)
            expanded_events.append(new_event)
    return expanded_events


def remove_zero_interval_from_recrule(recrule):
    if not recrule:
        return recrule
    recrule = recrule.replace(";INTERVAL=0", "")
    return recrule
