# -*- coding: utf-8 -*-

from datetime import datetime
from DateTime import DateTime
from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEntity
from imio.events.core.contents import IEvent
from imio.events.core.utils import get_agenda_for_event
from imio.events.core.utils import get_entity_for_obj
from imio.smartweb.common.rest.odwb import OdwbBaseEndpointGet
from imio.smartweb.common.utils import is_log_active
from imio.smartweb.common.utils import (
    activate_sending_data_to_odwb_for_staging as odwb_staging,
)
from plone import api
from plone.formwidget.geolocation.geolocation import Geolocation
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

import itertools
import json
import logging
import pytz

logger = logging.getLogger("imio.events.core")


def _batched(iterable, n):
    """Backport of itertools.batched (Python 3.12+) for older runtimes."""
    it = iter(iterable)
    while batch := list(itertools.islice(it, n)):
        yield batch


class OdwbEndpointGet(OdwbBaseEndpointGet):
    def __init__(self, context, request):
        imio_service = (
            "evenements-en-wallonie"
            if not odwb_staging()
            else "staging-evenements-en-wallonie"
        )
        pushkey = f"imio.events.core.odwb_{imio_service}_pushkey"
        super(OdwbEndpointGet, self).__init__(context, request, imio_service, pushkey)
        self.__datas_count__ = 0

    def _log_odwb_response(self, action, count, response_text):
        """Log the ODWB response at INFO (success) or WARNING (error).

        action  : "push" or "delete"
        count   : number of items in the batch
        """
        verb = "sent/updated" if action == "push" else "deleted"
        try:
            data = json.loads(response_text)
            success = data.get("ok") or data.get("status") == "ok"
            if success:
                logger.info(
                    "ODWB %s: %d events item(s) %s — ODWB response: %s",
                    action,
                    count,
                    verb,
                    response_text,
                )
            else:
                logger.warning(
                    "ODWB %s: %d events item(s) — ODWB returned an error: %s",
                    action,
                    count,
                    response_text,
                )
        except (json.JSONDecodeError, AttributeError):
            # odwb_query returns a plain error string on network/HTTP exceptions
            logger.warning(
                "ODWB %s: %d events item(s) — unexpected response: %s",
                action,
                count,
                response_text,
            )

    def reply(self):
        if not super(OdwbEndpointGet, self).available():
            logger.info(
                "ODWB push skipped (not available) for %s",
                self.context.absolute_url(),
            )
            return
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/push/?pushkey={self.odwb_pushkey}"
        if is_log_active():
            logger.info(f"ODWB push url: {url}")
        self.__datas_count__ = 0
        responses = []
        for batch in _batched(self.get_events(), 500):
            self.__datas_count__ += len(batch)
            payload = json.dumps(list(batch))
            response_text = self.odwb_query(url, payload)
            self._log_odwb_response("push", len(batch), response_text)
            responses.append(response_text)
        logger.info(
            "ODWB push complete: %d events item(s) sent from %s",
            self.__datas_count__,
            self.context.absolute_url(),
        )
        if not responses:
            return None
        unique = set(responses)
        return responses[-1] if len(unique) == 1 else responses

    def get_events(self):
        if IPloneSiteRoot.providedBy(self.context) or IAgenda.providedBy(self.context):
            brains = api.content.find(
                object_provides=IEvent.__identifier__, review_state="published"
            )
            for brain in brains:
                if IAgenda.providedBy(self.context):
                    if self.context.UID() not in brain.selected_agendas:
                        continue
                event_obj = brain.getObject()
                yield json.loads(Event(event_obj).to_json())
        elif IEntity.providedBy(self.context):
            brains = api.content.find(
                object_provides=IEvent.__identifier__,
                review_state="published",
                path={"query": "/".join(self.context.getPhysicalPath()), "depth": -1},
            )
            for brain in brains:
                event_obj = brain.getObject()
                yield json.loads(Event(event_obj).to_json())
        elif IEvent.providedBy(self.context):
            yield json.loads(Event(self.context).to_json())

    def remove(self):
        if not super(OdwbEndpointGet, self).available():
            logger.info(
                "ODWB delete skipped (not available) for %s",
                self.context.absolute_url(),
            )
            return
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/delete/?pushkey={self.odwb_pushkey}"
        if is_log_active():
            logger.info(f"ODWB delete url: {url}")
        deleted_count = 0
        responses = []
        for batch in _batched(self.get_events(), 500):
            deleted_count += len(batch)
            payload = json.dumps(list(batch))
            response_text = self.odwb_query(url, payload)
            self._log_odwb_response("delete", len(batch), response_text)
            responses.append(response_text)
        logger.info(
            "ODWB delete complete: %d events item(s) sent to ODWB delete endpoint from %s",
            deleted_count,
            self.context.absolute_url(),
        )
        if not responses:
            return None
        unique = set(responses)
        return responses[-1] if len(unique) == 1 else responses


class Event:

    def __init__(self, context):
        # ODWB fields = imio.events.core fields
        self.id = context.id
        self.start_datetime = context.start
        self.end_datetime = context.end
        self.recurrence = context.recurrence
        self.whole_day = context.whole_day
        self.open_end = context.open_end
        self.title = context.title
        self.description = context.description
        self.image = f"{context.absolute_url()}/@@images/image/preview"
        self.category = context.category
        self.topics = context.topics
        self.target_audience = context.local_category
        self.attendees = context.attendees if hasattr(context, "attendees") else ()
        self.text = context.text.raw if context.text else None
        self.reduced_mobility_facilities = context.reduced_mobility_facilities
        self.free_entry = context.free_entry
        self.coordinates = context.geolocation
        self.address_street_name = context.street
        self.address_house_number = context.number
        self.address_postal_code = context.zipcode
        self.address_city = context.city
        self.address_country = context.country
        self.online_meeting_url = context.online_participation
        self.contact_name = context.contact_name
        self.contact_email = context.contact_email
        self.contact_phone = context.contact_phone
        self.ticket_url = context.ticket_url
        self.event_url = context.event_url
        self.facebook_url = context.facebook
        self.instagram_url = context.instagram
        self.twitter_url = context.twitter
        self.video_url = context.video_url
        self.owner_id = get_entity_for_obj(context).UID()
        self.owner_name = get_entity_for_obj(context).Title()
        self.owner_diary_id = get_agenda_for_event(context).UID()
        self.owner_diary_name = get_agenda_for_event(context).Title()
        self.creation_datetime = context.creation_date
        self.modification_datetime = context.modification_date

        # In a first time, We don't send these fields to ODWB
        # self.street_number_complement = context.complement
        # self.description_de = context.description_de
        # self.description_en = context.description_en
        # self.description_nl = context.description_nl
        # self.effective_date = context.effective_date
        # self.event_type = context.event_type  # event-driven,
        # self.exclude_from_nav = context.exclude_from_nav
        # self.expiration_date = context.expiration_date
        # self.latitude = context.geolocation.latitude if context.geolocation else None
        # self.longitude = context.geolocation.longitude if context.geolocation else None
        # self.iam = context.iam
        # self.language = context.language
        # self.local_category = context.local_category
        # self.subjects = context.subject
        # self.taxonomy_event_public = context.taxonomy_event_public
        # self.text_de = context.text_de.raw if context.text_de else None
        # self.text_en = context.text_en.raw if context.text_en else None
        # self.text_nl = context.text_nl.raw if context.text_nl else None
        # self.title_de = context.title_de
        # self.title_en = context.title_en
        # self.title_nl = context.title_nl

    def to_json(self):
        return json.dumps(self.__dict__, cls=EventEncoder)


class EventEncoder(json.JSONEncoder):

    def default(self, attr):
        if isinstance(attr, Geolocation):
            return {
                "lon": attr.longitude,
                "lat": attr.latitude,
            }
        elif isinstance(attr, DateTime):
            iso_datetime = attr.ISO8601()
            return iso_datetime
        elif isinstance(attr, datetime):
            brussels = pytz.timezone("Europe/Brussels")
            if attr.tzinfo is not None:
                attr = attr.astimezone(brussels)
            return attr.isoformat()
        else:
            return super().default(attr)


class OdwbEntitiesEndpointGet(OdwbBaseEndpointGet):

    def __init__(self, context, request):
        imio_service = (
            "entites-des-agendas-en-wallonie"
            if not odwb_staging()
            else "staging-entites-des-agendas-en-wallonie"
        )
        pushkey = f"imio.events.core.odwb_{imio_service}_pushkey"
        super(OdwbEntitiesEndpointGet, self).__init__(
            context, request, imio_service, pushkey
        )

    def reply(self):
        if not super(OdwbEntitiesEndpointGet, self).available():
            return
        lst_entities = []
        brains = api.content.find(
            object_provides=IEntity.__identifier__, review_state="published"
        )
        for brain in brains:
            entity = {}
            entity["UID"] = brain.UID
            entity["id"] = brain.id
            entity["entity_title"] = brain.Title
            lst_entities.append(entity)
        self.__datas__ = lst_entities
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/push/?pushkey={self.odwb_pushkey}"
        if is_log_active():
            logger.info(f"ODWB push url: {url}")
        payload = json.dumps(lst_entities)
        return self.odwb_query(url, payload)
