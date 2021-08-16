# -*- coding: utf-8 -*-
from imio.events.core.contents.event.content import IEvent  # NOQA E501
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import getUtility
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class IEventIntegrationTest(unittest.TestCase):

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.authorized_types_in_event = [
            "File",
            "Image",
        ]
        self.unauthorized_types_in_event = [
            "imio.events.Agenda",
            "imio.events.Folder",
            "imio.events.Event",
            "Document",
        ]

        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.parent = self.portal
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
        self.folder = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            id="imio.events.Folder",
        )

    def test_ct_event_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        schema = fti.lookupSchema()
        self.assertEqual(IEvent, schema)

    def test_ct_event_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        self.assertTrue(fti)

    def test_ct_event_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(
            IEvent.providedBy(obj),
            u"IEvent not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_event_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="imio.events.Event",
        )

        self.assertTrue(
            IEvent.providedBy(obj),
            u"IEvent not provided by {0}!".format(
                obj.id,
            ),
        )

        parent = obj.__parent__
        self.assertIn("imio.events.Event", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("imio.events.Event", parent.objectIds())

    def test_ct_event_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        self.assertFalse(
            fti.global_allow, u"{0} is not globally addable!".format(fti.id)
        )

    def test_ct_event_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.folder,
            "imio.events.Event_id",
            title="imio.events.Event container",
        )
        folder = self.folder[parent_id]
        for t in self.unauthorized_types_in_event:
            with self.assertRaises(InvalidParameterError):
                api.content.create(
                    container=folder,
                    type=t,
                    title="My {}".format(t),
                )
        for t in self.authorized_types_in_event:
            api.content.create(
                container=folder,
                type=t,
                title="My {}".format(t),
            )
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=folder,
                type="imio.events.Entity",
                title="My Entity",
            )

    def test_event_local_category(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        factory = getUtility(
            IVocabularyFactory, "imio.events.vocabulary.EventsLocalCategories"
        )
        vocabulary = factory(event)
        self.assertEqual(len(vocabulary), 0)

        self.entity.local_categories = "First\nSecond\nThird"
        vocabulary = factory(event)
        self.assertEqual(len(vocabulary), 3)
