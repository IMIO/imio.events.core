# -*- coding: utf-8 -*-
from imio.events.core.contents.event.content import IEvent  # NOQA E501
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class IEventIntegrationTest(unittest.TestCase):

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.parent = self.portal
        self.agenda = api.content.create(
            container=self.portal,
            type="imio.events.Agenda",
            id="imio.events.Agenda",
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
            container=self.agenda,
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
            self.portal,
            "imio.events.Event_id",
            title="imio.events.Event container",
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type="Document",
                title="My Content",
            )
