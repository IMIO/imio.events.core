# -*- coding: utf-8 -*-

from datetime import datetime
from DateTime import DateTime
from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEntity
from imio.events.core.contents import IEvent
from imio.events.core.utils import get_agenda_for_event
from imio.events.core.utils import get_entity_for_obj
from imio.smartweb.common.rest.odwb import OdwbBaseEndpointGet
from imio.smartweb.common.utils import (
    activate_sending_data_to_odwb_for_staging as odwb_staging,
)
from plone import api
from plone.formwidget.geolocation.geolocation import Geolocation
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

import json
import logging
import requests

logger = logging.getLogger("imio.events.core")


class OdwbEndpointGet(OdwbBaseEndpointGet):
    def __init__(self, context, request):
        imio_service = (
            "evenements-en-wallonie"
            if not odwb_staging()
            else "staging-evenements-en-wallonie"
        )
        pushkey = f"imio.events.core.odwb_{imio_service}_pushkey"
        super(OdwbEndpointGet, self).__init__(context, request, imio_service, pushkey)

    def reply(self):
        if not super(OdwbEndpointGet, self).available():
            return
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/push/?pushkey={self.odwb_pushkey}"
        self.__datas__ = self.get_events()
        batched_lst = [
            self.__datas__[i : i + 1000] for i in range(0, len(self.__datas__), 1000)
        ]
        for elem in batched_lst:
            payload = json.dumps(elem)
            response_text = self.odwb_query(url, payload)
            logger.info(response_text)
        return response_text

    def get_events(self):
        lst_events = []
        if IPloneSiteRoot.providedBy(self.context) or IAgenda.providedBy(self.context):
            brains = api.content.find(
                object_provides=IEvent.__identifier__, review_state="published"
            )
            for brain in brains:
                if IAgenda.providedBy(self.context):
                    if self.context.UID() not in brain.selected_agendas:
                        continue
                event_obj = brain.getObject()
                event = Event(event_obj)
                lst_events.append(json.loads(event.to_json()))
        elif IEvent.providedBy(self.context):
            event = Event(self.context)
            lst_events.append(json.loads(event.to_json()))
        return lst_events

    def remove(self):
        if not super(OdwbEndpointGet, self).available():
            return
        lst_events = []
        if IEvent.providedBy(self.context):
            event = Event(self.context)
            lst_events.append(json.loads(event.to_json()))
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/delete/?pushkey={self.odwb_pushkey}"
        payload = json.dumps(lst_events)
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text


class Event:

    def __init__(self, context):
        self.attendees = context.attendees if hasattr(context, "attendees") else ()
        self.category = context.category
        self.city = context.city
        self.street_number_complement = context.complement
        self.contact_email = context.contact_email
        self.contact_name = context.contact_name
        self.contact_phone = context.contact_phone
        self.country = context.country
        # DateTime(2024/02/14 13:59:7.829612 GMT+1),
        self.creation_date = context.creation_date
        self.description_fr = context.description
        self.description_de = context.description_de
        self.description_en = context.description_en
        self.description_nl = context.description_nl
        # DateTime(2024/02/14 13:59:00 GMT+1),
        self.effective_date = context.effective_date
        # datetime.datetime(2024, 2, 14, 13, 0, tzinfo=<UTC>),
        self.end = context.end
        self.event_type = context.event_type  # event-driven,
        self.event_url = context.event_url
        self.exclude_from_nav = context.exclude_from_nav
        self.expiration_date = context.expiration_date
        self.facebook_url = context.facebook
        self.free_entry = context.free_entry
        self.geolocation = context.geolocation
        self.latitude = context.geolocation.latitude if context.geolocation else None
        self.longitude = context.geolocation.longitude if context.geolocation else None
        self.iam = context.iam
        # 2126b6ef314a4b3d9712732d5f036afc,
        self.id = context.id
        self.instagram_url = context.instagram
        self.language = context.language
        self.local_category = context.local_category
        # DateTime(2024/02/14 15:51:52.128648 GMT+1),
        self.modification_date = context.modification_date
        self.street_number = context.number
        self.online_participation = context.online_participation
        self.open_end = context.open_end
        self.recurrence = context.recurrence
        self.reduced_mobility_facilities = context.reduced_mobility_facilities
        # datetime.datetime(2024, 2, 14, 12, 0, tzinfo=<UTC>),
        self.start = context.start
        self.street = context.street
        self.subjects = context.subject
        self.taxonomy_event_public = context.taxonomy_event_public
        self.text_fr = context.text.raw if context.text else None
        self.text_de = context.text_de.raw if context.text_de else None
        self.text_en = context.text_en.raw if context.text_en else None
        self.text_nl = context.text_nl.raw if context.text_nl else None
        self.ticket_url = context.ticket_url
        self.title_fr = context.title
        self.title_de = context.title_de
        self.title_en = context.title_en
        self.title_nl = context.title_nl
        self.topics = context.topics
        self.twitter_url = context.twitter
        self.video_url = context.video_url
        self.whole_day = context.whole_day
        self.zipcode = context.zipcode
        self.agenda_uid = get_agenda_for_event(context).UID()
        self.agenda_title = get_agenda_for_event(context).Title()
        self.entity_uid = get_entity_for_obj(context).UID()
        self.entity_title = get_entity_for_obj(context).Title()

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
        payload = json.dumps(lst_entities)
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text
