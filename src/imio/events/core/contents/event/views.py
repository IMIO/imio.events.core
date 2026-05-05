# -*- coding: utf-8 -*-

from collective.geolocationbehavior.geolocation import IGeolocatable
from embeddify import Embedder
from imio.smartweb.common.config import DIRECTORY_URL
from imio.smartweb.common.contact_utils import formatted_schedule
from imio.smartweb.common.utils import get_json
from imio.smartweb.common.utils import show_warning_for_scales
from imio.smartweb.common.utils import translate_vocabulary_term
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.contenttypes.browser.folder import FolderView
from plone.app.event.browser.event_view import EventView
from Products.CMFPlone.resources import add_bundle_on_request
from zope.i18n import translate

import json


class View(EventView, FolderView):
    def __call__(self):
        show_warning_for_scales(self.context, self.request)
        images = self.context.listFolderContents(contentFilter={"portal_type": "Image"})
        if len(images) > 0:
            add_bundle_on_request(self.request, "spotlightjs")
            add_bundle_on_request(self.request, "flexbin")
        return self.index()

    def files(self):
        return self.context.listFolderContents(contentFilter={"portal_type": "File"})

    def images(self):
        return self.context.listFolderContents(contentFilter={"portal_type": "Image"})

    def has_leadimage(self):
        if ILeadImage.providedBy(self.context) and getattr(
            self.context, "image", False
        ):
            return True
        return False

    def get_embed_video(self):
        embedder = Embedder(width=800, height=600)
        return embedder(self.context.video_url, params=dict(autoplay=False))

    def category(self):
        title = translate_vocabulary_term(
            "imio.events.vocabulary.EventsCategories", self.context.category
        )
        if title:
            return title

    def topics(self):
        topics = self.context.topics
        if not topics:
            return
        items = []
        for item in topics:
            title = translate_vocabulary_term("imio.smartweb.vocabulary.Topics", item)
            items.append(title)
        return ", ".join(items)

    def iam(self):
        iam = self.context.iam
        if not iam:
            return
        items = []
        for item in iam:
            title = translate_vocabulary_term("imio.smartweb.vocabulary.IAm", item)
            items.append(title)
        return ", ".join(items)

    def data_geojson(self):
        """Return the contact geolocation as GeoJSON string."""
        current_lang = api.portal.get_current_language()[:2]
        coordinates = IGeolocatable(self.context).geolocation
        longitude = coordinates.longitude
        latitude = coordinates.latitude
        link_text = translate(_("Itinerary"), target_language=current_lang)
        geo_json = {
            "type": "Feature",
            "properties": {
                "popup": '<a href="{}">{}</a>'.format(
                    self.get_itinerary_link(), link_text
                ),
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    longitude,
                    latitude,
                ],
            },
        }
        return json.dumps(geo_json)

    def get_itinerary_link(self):
        if not self.context.is_geolocated:
            return
        if not self.address or self.address() == "":
            return
        return "https://www.google.com/maps/dir/?api=1&destination={}".format(
            self.address("+")
        )

    def address(self, separator=" "):
        address_parts = [
            self.context.street,
            self.context.number and str(self.context.number) or "",
            self.context.complement,
            self.context.zipcode and str(self.context.zipcode) or "",
            self.context.city,
        ]
        if self.context.country:
            term = translate_vocabulary_term(
                "imio.smartweb.vocabulary.Countries", self.context.country
            )
            address_parts.append(term)
        address = f"{separator}".join(filter(None, address_parts))
        return address

    def has_contact(self):
        name = self.context.contact_name
        mail = self.context.contact_email
        phone = self.context.contact_phone
        return True if name or mail or phone is not None else False

    def linked_contacts(self):
        uids = getattr(self.context, "directory_linked_contact", None) or []
        if not uids:
            return []
        params = [
            "portal_type=imio.directory.Contact",
            "fullobjects=1",
            "b_size=1000",
        ]
        params.extend("UID={}".format(uid) for uid in uids)
        url = "{}/@search?{}".format(DIRECTORY_URL, "&".join(params))
        response = get_json(url, None, 12)
        if not response:
            return []
        contacts = []
        for item in response.get("items", []):
            item_url = item.get("@id")
            has_image = bool((item.get("image_scales") or {}).get("image"))
            contacts.append(
                {
                    "url": item_url,
                    "title": item.get("title") or "",
                    "subtitle": item.get("subtitle") or "",
                    "description": item.get("description") or "",
                    "image_url": (
                        "{}/@@images/image/preview".format(item_url)
                        if has_image and item_url
                        else None
                    ),
                    "address": self._compose_contact_address(item),
                    "phones": self._normalize_phones(item.get("phones") or []),
                    "mails": self._normalize_mails(item.get("mails") or []),
                    "urls": self._normalize_urls(item.get("urls") or []),
                    "table_date": self._normalize_table_date(item.get("table_date")),
                    "multi_schedule": self._format_multi_schedule(
                        item.get("multi_schedule") or []
                    ),
                    "exceptional_closures": self._normalize_exceptional_closures(
                        item.get("exceptional_closure") or []
                    ),
                }
            )
        return contacts

    @staticmethod
    def _choice_label(value):
        if isinstance(value, dict):
            return value.get("title") or value.get("token") or ""
        return value or ""

    def _compose_contact_address(self, item):
        parts = [
            item.get("street") or "",
            str(item.get("number")) if item.get("number") else "",
            item.get("complement") or "",
            str(item.get("zipcode")) if item.get("zipcode") else "",
            item.get("city") or "",
            self._choice_label(item.get("country")),
        ]
        return " ".join(p for p in parts if p)

    def _normalize_phones(self, rows):
        return [
            {
                "label": row.get("label") or "",
                "type": self._choice_label(row.get("type")),
                "number": row.get("number") or "",
            }
            for row in rows
            if row.get("number")
        ]

    def _normalize_mails(self, rows):
        return [
            {
                "label": row.get("label") or "",
                "type": self._choice_label(row.get("type")),
                "mail_address": row.get("mail_address") or "",
            }
            for row in rows
            if row.get("mail_address")
        ]

    def _normalize_urls(self, rows):
        return [
            {
                "type": self._choice_label(row.get("type")),
                "url": row.get("url") or "",
            }
            for row in rows
            if row.get("url")
        ]

    @staticmethod
    def _normalize_table_date(table_date):
        if not table_date:
            return []
        result = []
        for entry in table_date:
            if not isinstance(entry, dict) or not entry:
                continue
            day, value = next(iter(entry.items()))
            result.append({"day": day, "value": value})
        return result

    def _format_multi_schedule(self, items):
        result = []
        for ms in items:
            schedule = ms.get("schedule") or {}
            formatted_days = []
            for day, value in schedule.items():
                if isinstance(value, dict):
                    formatted_days.append(
                        {"day": day, "value": formatted_schedule(value)}
                    )
            dates = []
            for date_range in ms.get("dates") or []:
                start = date_range.get("start_date") or ""
                end = date_range.get("end_date") or ""
                if start or end:
                    dates.append({"start": start, "end": end})
            result.append(
                {
                    "title": ms.get("title") or "",
                    "dates": dates,
                    "schedule": formatted_days,
                }
            )
        return result

    @staticmethod
    def _normalize_exceptional_closures(items):
        return [
            {"title": e.get("title") or "", "date": e.get("date") or ""}
            for e in items
            if e.get("date") or e.get("title")
        ]
