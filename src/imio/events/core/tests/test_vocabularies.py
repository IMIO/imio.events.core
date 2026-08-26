# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest.mock import patch
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from urllib.parse import parse_qs
from urllib.parse import urlparse
import unittest


class TestVocabularies(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_event_categories(self):
        factory = getUtility(
            IVocabularyFactory, "imio.events.vocabulary.EventsCategories"
        )
        vocabulary = factory()
        self.assertEqual(len(vocabulary), 10)

    def test_events_local_categories_on_root(self):
        factory = getUtility(
            IVocabularyFactory, "imio.events.vocabulary.EventsLocalCategories"
        )
        vocabulary = factory(self.portal)
        self.assertEqual(len(vocabulary), 0)

    def test_event_categories_topics(self):
        entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="imio.events.Entity",
            local_categories=[],
        )

        factory = getUtility(
            IVocabularyFactory,
            "imio.events.vocabulary.EventsCategoriesAndTopicsVocabulary",
        )
        vocabulary = factory(entity)
        self.assertEqual(len(vocabulary), 27)  # must be updated if add new vocabulary

    def test_event_categories_topics_local_cat(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="imio.events.Entity",
            local_categories=[
                {"fr": "Foo", "nl": "", "de": "", "en": ""},
                {"fr": "baz", "nl": "", "de": "", "en": ""},
                {"fr": "bar", "nl": "", "de": "", "en": ""},
            ],
        )
        agenda = api.content.create(
            container=entity,
            type="imio.events.Agenda",
            id="imio.events.Agenda",
        )
        event_item = api.content.create(
            container=agenda,
            type="imio.events.Event",
            id="imio.events.Event",
        )

        factory = getUtility(
            IVocabularyFactory,
            "imio.events.vocabulary.EventsCategoriesAndTopicsVocabulary",
        )
        vocabulary = factory(event_item)
        self.assertEqual(len(vocabulary), 30)  # must be updated if add new vocabulary

    def test_agendas_UIDs(self):
        entity1 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            title="Entity1",
        )
        entity2 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            title="Entity2",
        )
        agenda1 = api.content.create(
            container=entity1,
            type="imio.events.Agenda",
            title="Agenda1",
        )
        agenda2 = api.content.create(
            container=entity2,
            type="imio.events.Agenda",
            title="Agenda2",
        )
        folder = api.content.create(
            container=agenda1,
            type="imio.events.Folder",
            title="Folder",
        )
        event1 = api.content.create(
            container=folder,
            type="imio.events.Event",
            title="Event1",
        )
        event2 = api.content.create(
            container=agenda2,
            type="imio.events.Event",
            title="Event2",
        )

        all_agendas = []
        ag_entity1 = entity1.listFolderContents(
            contentFilter={"portal_type": "imio.events.Agenda"}
        )
        ag_entity2 = entity2.listFolderContents(
            contentFilter={"portal_type": "imio.events.Agenda"}
        )
        all_agendas = [*set(ag_entity1 + ag_entity2)]

        factory = getUtility(IVocabularyFactory, "imio.events.vocabulary.AgendasUIDs")
        vocabulary = factory(self.portal)
        self.assertEqual(len(vocabulary), len(all_agendas))

        vocabulary = factory(event1)
        self.assertEqual(len(vocabulary), len(all_agendas))

        vocabulary = factory(event2)
        uid = agenda2.UID()
        vocabulary.getTerm(uid)
        self.assertEqual(vocabulary.getTerm(uid).title, "Entity2 » Agenda2")

        vocabulary = factory(self.portal)
        ordered_agendas = [a.title for a in vocabulary]
        titles = []
        for agenda in ag_entity1 + ag_entity2:
            titles.append(f"{agenda.aq_parent.Title()} » {agenda.Title()}")
        titles.sort()
        ordered_agendas.sort()
        self.assertEqual(ordered_agendas, titles)
        agenda1.title = "Z Change order!"
        agenda1.reindexObject()
        vocabulary = factory(self.portal)
        ordered_agendas = [a.title for a in vocabulary]
        # "Entity2 » Agenda2", "Z Change order! » Agenda1"
        self.assertIn("Entity1 » Z Change order!", ordered_agendas)

    def test_event_types(self):
        factory = getUtility(IVocabularyFactory, "imio.events.vocabulary.EventTypes")
        vocabulary = factory(self.portal)
        self.assertEqual(len(vocabulary), 2)


class TestRemoteDirectoryContactVocabulary(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="directory-entity",
            title="Entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="directory-agenda",
            title="Agenda",
        )
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="directory-event",
            title="Event",
        )
        self.entity.directory_linked_entities = ["entity one", "entity-two"]
        self.factory = getUtility(
            IVocabularyFactory,
            "imio.events.vocabulary.RemoteDirectoryContact",
        )

    def payload(self, uid="contact-uid", title="Entity / Contact"):
        return {"items": [{"UID": uid, "breadcrumb": title}]}

    @patch("imio.events.core.vocabularies.get_json")
    def test_search_is_remote_and_bounded(self, get_json):
        get_json.return_value = self.payload()

        terms = self.factory(self.event).search("Jean + Jeanne")

        self.assertEqual(
            [(term.value, term.title) for term in terms],
            [("contact-uid", "Entity / Contact")],
        )
        query = parse_qs(urlparse(get_json.call_args[0][0]).query)
        self.assertEqual(query["b_size"], ["20"])
        self.assertEqual(query["SearchableText"], ["Jean* AND Jeanne*"])
        self.assertEqual(query["selected_entities"], ["entity one", "entity-two"])

    @patch("imio.events.core.vocabularies.get_json")
    def test_existing_value_is_resolved_by_uid(self, get_json):
        get_json.return_value = self.payload()

        term = self.factory(self.event).getTermByToken("contact-uid")

        self.assertEqual(term.title, "Entity / Contact")
        query = parse_qs(urlparse(get_json.call_args[0][0]).query)
        self.assertEqual(query["UID"], ["contact-uid"])
        self.assertEqual(query["b_size"], ["20"])

    @patch("imio.events.core.vocabularies.get_json")
    def test_opening_vocabulary_fetches_a_bounded_first_page(self, get_json):
        get_json.return_value = self.payload()
        vocabulary = self.factory(self.event)

        self.assertEqual([term.value for term in vocabulary], ["contact-uid"])
        query = parse_qs(urlparse(get_json.call_args[0][0]).query)
        self.assertEqual(query["b_size"], ["20"])
        self.assertNotIn("SearchableText", query)
        self.assertNotIn("UID", query)

    @patch("imio.events.core.vocabularies.get_json")
    def test_empty_search_fetches_the_same_bounded_first_page(self, get_json):
        get_json.return_value = self.payload()

        terms = self.factory(self.event).search("")

        self.assertEqual([term.value for term in terms], ["contact-uid"])
        query = parse_qs(urlparse(get_json.call_args[0][0]).query)
        self.assertEqual(query["b_size"], ["20"])
        self.assertNotIn("SearchableText", query)
