# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield.row import DictRow
from imio.events.core import utils
from imio.events.core.contents.contact.content import IContact  # NOQA E501
from imio.events.core.contents.contact.content import IContactPhoneRow
from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from plone.restapi.interfaces import ISerializeToJson
from unittest import mock
from zope import schema
from zope.component import createObject
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.interface import alsoProvides

import unittest


class TestContact(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="imio.events.Entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="imio.events.Agenda",
        )
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="imio.events.Event",
        )

    def test_ct_contact_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Contact")
        schema = fti.lookupSchema()
        self.assertEqual(IContact, schema)

    def test_ct_contact_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Contact")
        self.assertTrue(fti)

    def test_ct_contact_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Contact")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IContact.providedBy(obj),
            "IContact not provided by {0}!".format(
                obj,
            ),
        )

    def test_title_is_optional(self):
        """The title field exists on the type and is not required."""
        self.assertIn("title", IContact)
        self.assertFalse(IContact["title"].required)

    def test_no_description_field(self):
        """No description is exposed (plone.basic is intentionally not used)."""
        self.assertNotIn("description", IContact)
        fti = queryUtility(IDexterityFTI, name="imio.events.Contact")
        self.assertNotIn("plone.basic", fti.behaviors)

    def test_reimport_purges_plone_basic(self):
        """A re-import removes a lingering plone.basic (purge='true').

        Reproduces the "two titles + description" case: a site where
        plone.basic had been imported on the Contact FTI before. Re-importing
        the type info must drop it instead of appending the new list.
        """
        fti = queryUtility(IDexterityFTI, name="imio.events.Contact")
        fti.behaviors = tuple(fti.behaviors) + ("plone.basic",)
        self.assertIn("plone.basic", fti.behaviors)

        setup = api.portal.get_tool("portal_setup")
        setup.runImportStepFromProfile(
            "profile-imio.events.core:default", "typeinfo"
        )

        fti = queryUtility(IDexterityFTI, name="imio.events.Contact")
        self.assertNotIn("plone.basic", fti.behaviors)
        self.assertEqual(
            tuple(fti.behaviors),
            ("plone.namefromtitle", "plone.excludefromnavigation"),
        )

    def test_ct_contact_adding_without_title(self):
        """A contact is valid without a title (the title field is optional)."""
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        contact = api.content.create(
            container=self.event,
            type="imio.events.Contact",
            id="contact-without-title",
        )
        self.assertTrue(IContact.providedBy(contact))
        self.assertFalse(contact.title)
        self.assertIn(contact.id, self.event.objectIds())

    def test_ct_contact_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Contact")
        self.assertFalse(
            fti.global_allow, "{0} is not globally addable!".format(fti.id)
        )

    def test_related_contact_is_single_choice(self):
        """The directory contact select is a single-value Choice (not a List)."""
        field = IContact["related_contact"]
        self.assertIsInstance(field, schema.Choice)
        self.assertFalse(isinstance(field, schema.List))
        self.assertEqual(
            field.vocabularyName, "imio.events.vocabulary.RemoteDirectoryContact"
        )
        self.assertTrue(field.required)

    def test_ct_contact_adding_multiple_in_event(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        contact1 = api.content.create(
            container=self.event,
            type="imio.events.Contact",
            title="First contact",
        )
        contact2 = api.content.create(
            container=self.event,
            type="imio.events.Contact",
            title="Second contact",
        )

        self.assertTrue(
            IContact.providedBy(contact1),
            "IContact not provided by {0}!".format(contact1.id),
        )
        # Several secondary contacts can live in the same event.
        self.assertIn(contact1.id, self.event.objectIds())
        self.assertIn(contact2.id, self.event.objectIds())

        api.content.delete(obj=contact1)
        self.assertNotIn(contact1.id, self.event.objectIds())

    def test_ct_contact_not_addable_in_agenda(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.agenda,
                type="imio.events.Contact",
                title="My Contact",
            )

    def test_datagrid_fields(self):
        """phones/mails/urls are datagrids and each row has a 'Keep' checkbox."""
        for name in ("phones", "mails", "urls"):
            self.assertIn(name, IContact)
            self.assertIsInstance(IContact[name], schema.List)
            self.assertIsInstance(IContact[name].value_type, DictRow)
        self.assertIn("selected", IContactPhoneRow)
        self.assertIsInstance(IContactPhoneRow["selected"], schema.Bool)

    def test_get_directory_contact_lines(self):
        """The directory JSON is parsed into the columns we display."""
        fake = {
            "items": [
                {
                    "phones": [
                        {"label": "YOLO", "number": "+3223841982", "type": "work"},
                        {"label": None, "number": "+32778123456", "type": "fax"},
                    ],
                    "mails": [
                        {"label": None, "mail_address": "x@y.be", "type": "work"}
                    ],
                    "urls": [{"type": "facebook", "url": "https://www.test.be"}],
                }
            ]
        }
        with mock.patch.object(utils, "get_json", return_value=fake):
            lines = utils.get_directory_contact_lines("some-uid")
        self.assertEqual(len(lines["phones"]), 2)
        self.assertEqual(
            lines["phones"][0],
            {"label": "YOLO", "type": "work", "number": "+3223841982"},
        )
        self.assertEqual(lines["phones"][1]["label"], "")  # None -> ""
        self.assertEqual(lines["mails"][0]["mail_address"], "x@y.be")
        self.assertEqual(
            lines["urls"][0], {"type": "facebook", "url": "https://www.test.be"}
        )

    def test_get_directory_contact_lines_no_uid(self):
        self.assertEqual(
            utils.get_directory_contact_lines(None),
            {"phones": [], "mails": [], "urls": []},
        )

    def test_refresh_contact_informations_preserves_selection(self):
        """Refreshing keeps the lines that were ticked (matched by value)."""
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        contact = api.content.create(
            container=self.event,
            type="imio.events.Contact",
            title="c",
        )
        contact.related_contact = "uid-1"
        contact.phones = [
            {"selected": True, "label": "", "type": "work", "number": "+3211"}
        ]
        fake = {
            "items": [
                {
                    "phones": [
                        {"label": "", "number": "+3211", "type": "work"},
                        {"label": "", "number": "+3299", "type": "fax"},
                    ],
                    "mails": [],
                    "urls": [],
                }
            ]
        }
        with mock.patch.object(utils, "get_json", return_value=fake):
            utils.refresh_contact_informations(contact)
        self.assertEqual(len(contact.phones), 2)
        ticked = {row["number"]: row["selected"] for row in contact.phones}
        self.assertTrue(ticked["+3211"])  # previously ticked, still ticked
        self.assertFalse(ticked["+3299"])  # new line, not ticked
        self.assertEqual(contact.mails, [])
        self.assertEqual(contact.urls, [])

    def test_event_serializer_includes_secondary_contacts(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        contact1 = api.content.create(
            container=self.event,
            type="imio.events.Contact",
            title="First contact",
        )
        contact1.related_contact = "uid-contact-1"
        contact1.phones = [
            {"selected": True, "label": "", "type": "work", "number": "+3211"},
            {"selected": False, "label": "", "type": "fax", "number": "+3299"},
        ]
        contact1.mails = [
            {"selected": True, "label": "", "type": "work", "mail_address": "a@b.be"}
        ]
        contact1.urls = [
            {"selected": False, "type": "facebook", "url": "https://x.be"}
        ]
        contact2 = api.content.create(
            container=self.event,
            type="imio.events.Contact",
            title="Second contact",
        )
        contact2.related_contact = "uid-contact-2"
        # A contact without a linked reference is skipped.
        api.content.create(
            container=self.event,
            type="imio.events.Contact",
            title="Empty contact",
        )

        alsoProvides(self.request, IImioEventsCoreLayer)
        serializer = getMultiAdapter((self.event, self.request), ISerializeToJson)
        result = serializer()

        secondary = result["secondary_contacts"]
        self.assertEqual(len(secondary), 2)
        by_uid = {entry["uid"]: entry for entry in secondary}
        entry1 = by_uid["uid-contact-1"]
        self.assertEqual(entry1["title"], "First contact")
        # Only the ticked lines, with the internal 'selected' flag stripped.
        self.assertEqual(
            entry1["phones"],
            [{"label": "", "type": "work", "number": "+3211"}],
        )
        self.assertEqual(
            entry1["mails"],
            [{"label": "", "type": "work", "mail_address": "a@b.be"}],
        )
        self.assertEqual(entry1["urls"], [])
        self.assertEqual(by_uid["uid-contact-2"]["phones"], [])

    def test_event_serializer_secondary_contacts_empty(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        alsoProvides(self.request, IImioEventsCoreLayer)
        serializer = getMultiAdapter(
            (self.event, self.request), ISerializeToJson
        )
        result = serializer()
        self.assertEqual(result["secondary_contacts"], [])
