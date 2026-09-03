# -*- coding: utf-8 -*-

from datetime import datetime
from imio.events.core.testing import IMIO_EVENTS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser
from unittest.mock import MagicMock
from unittest.mock import patch
from urllib.parse import parse_qs
from urllib.parse import urlparse

import json
import transaction
import unittest

# Only the remote directory is mocked (see test_contact_info.py): the vocabulary,
# the widget, the converter and the form are exercised for real.
REQUESTS_GET = "imio.smartweb.common.utils.requests.get"

LINKED_ENTITY_UID = "11111111111111111111111111111111"
OTHER_ENTITY_UID = "22222222222222222222222222222222"
CONTACT_UID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
FOREIGN_CONTACT_UID = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

DIRECTORY_CONTACTS = [
    {
        "UID": CONTACT_UID,
        "breadcrumb": "Amay » Bibliothèque",
        "entity": LINKED_ENTITY_UID,
    },
    {
        "UID": FOREIGN_CONTACT_UID,
        "breadcrumb": "Ans » Piscine",
        "entity": OTHER_ENTITY_UID,
    },
]


def fake_directory_search(url, headers=None, timeout=None):
    """Answer a directory ``@search`` the way the real one does.

    Filters on the ``UID`` and ``selected_entities`` criteria the vocabulary
    builds, so a contact outside the Entity's linked directory entities is not
    found -- which is what makes it invalid for the field.
    """
    query = parse_qs(urlparse(url).query)
    uids = query.get("UID")
    entities = query.get("selected_entities")
    items = [
        contact
        for contact in DIRECTORY_CONTACTS
        if (uids is None or contact["UID"] in uids)
        and (entities is None or contact["entity"] in entities)
    ]
    response = MagicMock()
    response.status_code = 200
    response.text = json.dumps({"items": items, "items_total": len(items)})
    return response


class TestAjaxSelectChoiceConverter(unittest.TestCase):
    """``directory_linked_contact`` is a single-valued Choice on an ajax select
    widget: without a dedicated converter its value can never be saved."""

    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity",
            title="Entity",
        )
        self.entity.directory_linked_entities = [LINKED_ENTITY_UID]
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="agenda",
            title="Agenda",
        )
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
            title="Event",
        )
        self.event.start = datetime(2026, 9, 10, 10, 0)
        self.event.end = datetime(2026, 9, 10, 12, 0)
        transaction.commit()

    def save_edit_form(self, uid):
        """Pick ``uid`` as main contact on the edit form and save it."""
        browser = Browser(self.app)
        browser.addHeader(
            "Authorization", "Basic {}:{}".format(TEST_USER_NAME, TEST_USER_PASSWORD)
        )
        with patch(REQUESTS_GET, side_effect=fake_directory_search):
            browser.open("{}/edit".format(self.event.absolute_url()))
            browser.getControl(name="form.widgets.directory_linked_contact").value = uid
            browser.getControl(name="form.buttons.save").click()
        return browser

    def test_a_selected_contact_can_be_saved(self):
        browser = self.save_edit_form(CONTACT_UID)
        self.assertNotIn("Constraint not satisfied", browser.contents)
        self.assertEqual(self.event.directory_linked_contact, CONTACT_UID)

    def test_a_contact_outside_the_linked_entities_is_refused(self):
        # The scoping to the Entity's directory_linked_entities must survive:
        # the converter hands unknown tokens over to the field validator.
        browser = self.save_edit_form(FOREIGN_CONTACT_UID)
        self.assertIn("Constraint not satisfied", browser.contents)
        self.assertIsNone(self.event.directory_linked_contact)

    def test_no_contact_is_stored_as_missing_value(self):
        browser = self.save_edit_form("")
        self.assertNotIn("Constraint not satisfied", browser.contents)
        self.assertIsNone(self.event.directory_linked_contact)
