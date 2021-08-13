# -*- coding: utf-8 -*-
from imio.events.core.contents.agenda.content import IAgenda  # NOQA E501
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class IAgendaIntegrationTest(unittest.TestCase):

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.authorized_types_in_agenda = [
            "imio.events.Folder",
            "imio.events.Event",
        ]
        self.unauthorized_types_in_agenda = [
            "imio.events.Agenda",
            "Document",
            "File",
            "Image",
        ]

        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.parent = self.portal
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="imio.events.Entity",
        )

    def test_ct_agenda_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Agenda")
        schema = fti.lookupSchema()
        self.assertEqual(IAgenda, schema)

    def test_ct_agenda_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Agenda")
        self.assertTrue(fti)

    def test_ct_agenda_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Agenda")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IAgenda.providedBy(obj),
            u"IAgenda not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_agenda_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="imio.events.Agenda",
        )

        self.assertTrue(
            IAgenda.providedBy(obj),
            u"IAgenda not provided by {0}!".format(
                obj.id,
            ),
        )

        parent = obj.__parent__
        self.assertIn("imio.events.Agenda", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("imio.events.Agenda", parent.objectIds())

    def test_ct_agenda_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Agenda")
        self.assertFalse(
            fti.global_allow, u"{0} is not globally addable!".format(fti.id)
        )

    def test_ct_agenda_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Agenda")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.entity,
            "imio.events.Agenda_id",
            title="imio.events.Agenda container",
        )
        folder = self.entity[parent_id]
        for t in self.unauthorized_types_in_agenda:
            with self.assertRaises(InvalidParameterError):
                api.content.create(
                    container=folder,
                    type=t,
                    title="My {}".format(t),
                )
        for t in self.authorized_types_in_agenda:
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
