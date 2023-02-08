# -*- coding: utf-8 -*-

from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.events.core.testing import IMIO_EVENTS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

import transaction
import unittest


class TestMultilingual(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests"""
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            title="Entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="imio.events.Agenda",
        )

    def test_create_multilingual_event(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Mon event que je vais tester en plusieurs langues",
        )
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertFalse(indexes.get("translated_in_nl"))
        self.assertFalse(indexes.get("translated_in_de"))
        self.assertFalse(indexes.get("translated_in_en"))

        event.title_en = "My event that I will test in several languages"
        event.reindexObject()
        transaction.commit()
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertFalse(indexes.get("translated_in_nl"))
        self.assertFalse(indexes.get("translated_in_de"))
        self.assertTrue(indexes.get("translated_in_en"))

        event.title_nl = "Mijn evenement die ik in verschillende talen zal testen"
        event.title_de = "Mein Veranstaltung, den ich in mehreren Sprachen testen werde"
        event.reindexObject()
        transaction.commit()
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertTrue(indexes.get("translated_in_nl"))
        self.assertTrue(indexes.get("translated_in_de"))
        self.assertTrue(indexes.get("translated_in_en"))

        event.title_en = None
        event.reindexObject()
        transaction.commit()
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertFalse(indexes.get("translated_in_en"))

    def test_multilingual_searchabletext_event(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Mon event que je vais tester en plusieurs langues",
        )
        event.title_en = "My event that I will test in several languages"
        event.title_nl = "Mijn evenement die ik in verschillende talen zal testen"
        event.title_de = "Mein Veranstaltung, den ich in mehreren Sprachen testen werde"
        event.description = "Ma description_fr"
        event.description_nl = "Mijn beschrijving"
        event.description_de = "Meine Beschreibung"
        event.description_en = "My description_en"
        event.text = RichTextValue("<p>Mon eventtexte</p>", "text/html", "text/html")
        event.text_en = RichTextValue("<p>My eventtext</p>", "text/html", "text/html")
        event.text_nl = RichTextValue(
            "<p>Mijn eventtekst</p>", "text/html", "text/html"
        )
        event.text_de = RichTextValue(
            "<p>Meine eventetext</p>", "text/html", "text/html"
        )
        event.reindexObject()
        transaction.commit()
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertIn("several", indexes.get("SearchableText_en"))
        self.assertIn("verschillende", indexes.get("SearchableText_nl"))
        self.assertIn("mehreren", indexes.get("SearchableText_de"))
        self.assertIn("eventtexte", indexes.get("SearchableText"))
        self.assertIn("eventtext", indexes.get("SearchableText_en"))
        self.assertIn("eventtekst", indexes.get("SearchableText_nl"))
        self.assertIn("eventetext", indexes.get("SearchableText_de"))
        metadatas = catalog.getMetadataForRID(brain.getRID())
        self.assertEqual(event.title_nl, metadatas.get("title_nl"))
        self.assertEqual(event.title_de, metadatas.get("title_de"))
        self.assertEqual(event.title_en, metadatas.get("title_en"))
        self.assertEqual(event.description_nl, metadatas.get("description_nl"))
        self.assertEqual(event.description_de, metadatas.get("description_de"))
        self.assertEqual(event.description_en, metadatas.get("description_en"))

        event.title_en = None
        event.reindexObject()
        transaction.commit()
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertNotIn("several", indexes.get("SearchableText_en"))

    def test_event_serializer(self):
        alsoProvides(self.request, IImioEventsCoreLayer)
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Mon event",
        )
        event.title_en = "My event"
        event.title_nl = "Mijn evenement"
        event.description = "Ma **description**"
        event.description_en = "My **description**"
        event.description_nl = "Mijn **beschrijving**"
        event.text = RichTextValue("<p>Mon texte</p>", "text/html", "text/html")
        event.text_en = RichTextValue("<p>My text</p>", "text/html", "text/html")
        event.text_nl = RichTextValue("<p>Mijn tekst</p>", "text/html", "text/html")

        serializer = getMultiAdapter((event, self.request), ISerializeToJson)
        json = serializer()
        self.assertEqual(json["title"], "Mon event")
        self.assertEqual(json["description"], "Ma **description**")
        self.assertEqual(json["title_fr"], "Mon event")
        self.assertEqual(json["description_fr"], "Ma **description**")

        catalog = api.portal.get_tool("portal_catalog")
        brain = catalog(UID=event.UID())[0]
        serializer = getMultiAdapter((brain, self.request), ISerializeToJsonSummary)
        json_summary = serializer()
        self.assertEqual(json_summary["title"], "Mon event")
        self.assertEqual(json_summary["description"], "Ma description")

        self.request.form["translated_in_nl"] = True
        serializer = getMultiAdapter((event, self.request), ISerializeToJson)
        json = serializer()
        self.assertEqual(json["title"], "Mijn evenement")
        self.assertEqual(json["description"], "Mijn **beschrijving**")
        self.assertEqual(json["text"]["data"], "<p>Mijn tekst</p>")
        self.assertEqual(json["title_fr"], "Mon event")
        self.assertEqual(json["description_fr"], "Ma **description**")
        self.assertEqual(json["text_fr"]["data"], "<p>Mon texte</p>")

        brain = catalog(UID=event.UID())[0]
        serializer = getMultiAdapter((brain, self.request), ISerializeToJsonSummary)
        json_summary = serializer()
        self.assertEqual(json_summary["title"], "Mijn evenement")
        self.assertEqual(json_summary["description"], "Mijn beschrijving")
