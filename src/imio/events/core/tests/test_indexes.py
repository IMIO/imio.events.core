# -*- coding: utf-8 -*-

from datetime import datetime
from imio.events.core.indexers import event_dates
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


def search_all_from_vocabulary(vocabulary, context, catalog):
    factory = getUtility(
        IVocabularyFactory,
        vocabulary,
    )
    output = {}
    vocabulary = factory(context)
    for v in vocabulary.by_value:
        result = catalog.searchResults(**{"category_and_topics": v})
        if len(result) == 0:
            continue
        output[v] = [r.getObject().id for r in result]
    return output


class TestIndexes(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.portal_catalog = api.portal.get_tool("portal_catalog")

        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="imio.events.Entity",
            local_categories=[
                {"fr": "Foo", "nl": "", "de": "", "en": ""},
                {"fr": "baz", "nl": "", "de": "", "en": ""},
                {"fr": "bar", "nl": "", "de": "", "en": ""},
                {"fr": "Local category", "nl": "", "de": "", "en": ""},
            ],
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="imio.events.Agenda",
        )

    def test_category_and_topics_index(self):
        # Without category
        api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="imio.events.Event",
        )
        search_result = search_all_from_vocabulary(
            "imio.events.vocabulary.EventsCategoriesAndTopicsVocabulary",
            self.agenda,
            self.portal_catalog,
        )
        self.assertEqual(len(search_result), 0)

        # With categories and topics
        api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="id_event",
            category="stroll_discovery",
            local_category="Foo",
            topics=["culture", "health"],
        )

        api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="id_event2",
            category="theater_show",
            local_category="baz",
            topics=["tourism", "health"],
        )

        search_result = search_all_from_vocabulary(
            "imio.events.vocabulary.EventsCategoriesAndTopicsVocabulary",
            self.agenda,
            self.portal_catalog,
        )

        # check if right number of result
        self.assertEqual(len(search_result), 7)

        # check for good result number
        self.assertEqual(len(search_result["stroll_discovery"]), 1)
        self.assertEqual(len(search_result["Foo"]), 1)
        self.assertEqual(len(search_result["baz"]), 1)
        self.assertEqual(len(search_result["culture"]), 1)
        self.assertEqual(len(search_result["health"]), 2)
        self.assertEqual(len(search_result["theater_show"]), 1)
        self.assertEqual(len(search_result["tourism"]), 1)

        # check for good return object
        self.assertEqual(search_result["stroll_discovery"], ["id_event"])
        self.assertEqual(search_result["Foo"], ["id_event"])
        self.assertEqual(search_result["baz"], ["id_event2"])
        self.assertEqual(search_result["culture"], ["id_event"])
        self.assertEqual(sorted(search_result["health"]), ["id_event", "id_event2"])
        self.assertEqual(search_result["theater_show"], ["id_event2"])
        self.assertEqual(search_result["tourism"], ["id_event2"])

    def test_category_title_index(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Title",
        )
        event.category = "stroll_discovery"
        event.reindexObject()
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("category_title"), "Balade et découverte")
        metadatas = catalog.getMetadataForRID(brain.getRID())
        self.assertEqual(metadatas.get("category_title"), "Balade et découverte")
        self.assertEqual(metadatas.get("category_title_nl"), "Wandeling en ontdekking")
        self.assertEqual(
            metadatas.get("category_title_de"), "Spaziergang und Entdeckung"
        )
        self.assertEqual(metadatas.get("category_title_en"), "Stroll and discovery")
        event.local_category = "Local category"
        event.reindexObject()
        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("category_title"), "Balade et découverte")

    def test_selected_agendas_index(self):
        event1 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Event1",
        )
        agenda2 = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            title="Agenda2",
        )
        event2 = api.content.create(
            container=agenda2,
            type="imio.events.Event",
            title="Event2",
        )
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event1.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("container_uid"), self.agenda.UID())

        # On va requêter sur self.agenda et trouver les 2 événements car event2 vient de s'ajouter dedans aussi.
        event2.selected_agendas = [self.agenda.UID()]
        event2.reindexObject()
        brains = api.content.find(selected_agendas=self.agenda.UID())
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [event1.UID(), event2.UID()])

        # On va requêter sur agenda2 et trouver uniquement event2 car event2 est dans les 2 agendas mais event1 n'est que dans self.agenda
        event2.selected_agendas = [agenda2.UID(), self.agenda.UID()]
        event2.reindexObject()
        brains = api.content.find(selected_agendas=agenda2.UID())
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [event2.UID()])

        # Via une recherche catalog sur les agenda, on va trouver les 2 événements
        brains = api.content.find(selected_agendas=[agenda2.UID(), self.agenda.UID()])
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [event1.UID(), event2.UID()])

        # On va requêter sur les 2 agendas et trouver les 2 événements car 1 dans chaque
        event2.selected_agendas = [agenda2.UID()]
        event2.reindexObject()
        brains = api.content.find(selected_agendas=[agenda2.UID(), self.agenda.UID()])
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [event1.UID(), event2.UID()])

        api.content.move(event1, agenda2)
        brain = api.content.find(UID=event1.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("container_uid"), agenda2.UID())

    def test_searchable_text_index(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Title",
        )
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("SearchableText"), ["title"])

        event.description = "Description"
        event.topics = ["agriculture"]
        event.category = "stroll_discovery"
        event.text = RichTextValue("<p>Text</p>", "text/html", "text/html")
        event.reindexObject()

        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            indexes.get("SearchableText"),
            [
                "title",
                "description",
                "text",
                "agriculture",
                "balade",
                "et",
                "decouverte",
            ],
        )

        event.title_nl = "Titel"
        event.description_nl = "Descriptie"
        event.text_nl = RichTextValue("<p>Tekst</p>", "text/html", "text/html")
        event.reindexObject()

        brain = api.content.find(UID=event.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            indexes.get("SearchableText_nl"),
            [
                "titel",
                "descriptie",
                "tekst",
                "landbouw",
                "wandeling",
                "en",
                "ontdekking",
            ],
        )

    def test_event_dates_index(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="My event",
        )
        event.start = datetime(2022, 2, 13, 12, 30)
        event.end = datetime(2022, 2, 14, 12, 30)
        event.open_end = False
        dates = sorted(event_dates(event)())
        self.assertEqual(dates, ["2022-02-13", "2022-02-14"])

        # event with open end
        event.start = datetime(2022, 2, 13, 12, 30)
        event.end = datetime(2022, 2, 14, 12, 30)
        event.open_end = True
        dates = sorted(event_dates(event)())
        self.assertEqual(dates, ["2022-02-13"])

        # event with recurrence
        event.start = datetime(2022, 2, 13, 12, 30)
        event.end = datetime(2022, 2, 13, 12, 30)
        event.open_end = False
        event.recurrence = "RRULE:FREQ=MONTHLY;COUNT=3"
        dates = sorted(event_dates(event)())
        self.assertEqual(dates, ["2022-02-13", "2022-03-13", "2022-04-13"])

    def test_first_dates_indexes(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="My event",
        )
        event.start = datetime(2022, 2, 13, 12, 30)
        event.end = datetime(2022, 2, 13, 14, 30)
        event.open_end = False
        event.recurrence = "RRULE:FREQ=WEEKLY;COUNT=5"
        event.reindexObject()

        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        self.assertEqual(brain.first_start, datetime(2022, 2, 13, 12, 30))
        self.assertEqual(brain.first_end, datetime(2022, 2, 13, 14, 30))
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("first_start"), datetime(2022, 2, 13, 12, 30))
        self.assertEqual(indexes.get("first_end"), datetime(2022, 2, 13, 14, 30))
