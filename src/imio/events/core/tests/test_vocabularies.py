# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

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
