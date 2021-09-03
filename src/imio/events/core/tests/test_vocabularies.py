# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestVocabularies(unittest.TestCase):

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_news_categories(self):
        factory = getUtility(
            IVocabularyFactory, "imio.events.vocabulary.EventsCategories"
        )
        vocabulary = factory()
        self.assertEqual(len(vocabulary), 10)

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
        factory = getUtility(IVocabularyFactory, "imio.events.vocabulary.AgendasUIDs")
        vocabulary = factory(self.portal)
        self.assertEqual(len(vocabulary), 0)

        api.content.transition(agenda1, to_state="published")
        api.content.transition(agenda2, to_state="published")
        vocabulary = factory(self.portal)
        self.assertEqual(len(vocabulary), 2)

        vocabulary = factory(event1)
        self.assertEqual(len(vocabulary), 1)

        vocabulary = factory(event2)
        uid = agenda2.UID()
        vocabulary.getTerm(uid)
        self.assertEqual(vocabulary.getTerm(uid).title, agenda2.title)

        vocabulary = factory(self.portal)
        ordered_agendas = [a.title for a in vocabulary]
        self.assertEqual(ordered_agendas, [agenda1.title, agenda2.title])
        agenda1.title = "Change order!"
        agenda1.reindexObject()
        vocabulary = factory(self.portal)
        ordered_agendas = [a.title for a in vocabulary]
        self.assertEqual(ordered_agendas, [agenda2.title, agenda1.title])

    def test_event_categories_topics(self):
        factory = getUtility(
            IVocabularyFactory,
            "imio.events.vocabulary.EventsCategoriesAndTopicsVocabulary",
        )
        vocabulary = factory(event_item)
        self.assertEqual(len(vocabulary), 26)

    def test_news_categories_topics_local_cat(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="imio.events.Entity",
            local_categories="Foo\r\nbaz\r\nbar",
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
        self.assertEqual(len(vocabulary), 29)
