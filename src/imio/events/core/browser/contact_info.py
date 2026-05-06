# -*- coding: utf-8 -*-
import json

from imio.smartweb.common.config import DIRECTORY_URL
from imio.smartweb.common.utils import get_json
from Products.Five.browser import BrowserView


class DirectoryContactInfoView(BrowserView):
    """Return the linked contact's name/email/phone as JSON.

    Used by the Event edit form JS to autofill the IEventContact fields when
    the user picks an entry in ``directory_linked_contact``.
    """

    def __call__(self):
        self.request.response.setHeader("Content-Type", "application/json")
        uid = self.request.form.get("uid")
        if not uid:
            return json.dumps({})
        url = "{}/@search?UID={}&fullobjects=true".format(DIRECTORY_URL, uid)
        data = get_json(url, None, 12)
        items = (data or {}).get("items") or []
        if not items:
            return json.dumps({})
        contact = items[0]
        phones = contact.get("phones") or []
        mails = contact.get("mails") or []
        contact_title = contact.get("title") or ""
        contact_subtitle = contact.get("subtitle") or ""
        if contact_subtitle != "":
            contact_name = f"{contact_title}: {contact_subtitle}"
        else:
            contact_name = contact_title
        # IAddress fields are identical on Event and Contact; the country
        # field comes back as a token (e.g. "be") matching the Event select
        # options, and zipcode is an int so we coerce it to a string for the
        # text input.
        country = contact.get("country") or ""
        if isinstance(country, dict):
            country = country.get("token") or country.get("title") or ""
        zipcode = contact.get("zipcode")
        result = {
            "name": contact_name,
            "email": (mails[0].get("mail_address") if mails else "") or "",
            "phone": (phones[0].get("number") if phones else "") or "",
            "street": contact.get("street") or "",
            "number": contact.get("number") or "",
            "complement": contact.get("complement") or "",
            "zipcode": "" if zipcode is None else str(zipcode),
            "city": contact.get("city") or "",
            "country": country,
        }
        return json.dumps(result)
