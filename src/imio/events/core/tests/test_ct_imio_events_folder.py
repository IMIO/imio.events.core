# -*- coding: utf-8 -*-
from imio.events.core.contents.folder.content import IFolder  # NOQA E501
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class IFolderIntegrationTest(unittest.TestCase):

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

    def test_ct_folder_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Folder")
        schema = fti.lookupSchema()
        self.assertEqual(IFolder, schema)

    def test_ct_folder_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Folder")
        self.assertTrue(fti)

    def test_ct_folder_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Folder")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IFolder.providedBy(obj),
            u"IFolder not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_folder_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            id="imio.events.Folder",
        )

        self.assertTrue(
            IFolder.providedBy(obj),
            u"IFolder not provided by {0}!".format(
                obj.id,
            ),
        )

        parent = obj.__parent__
        self.assertIn("imio.events.Folder", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("imio.events.Folder", parent.objectIds())

    def test_ct_folder_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Folder")
        self.assertFalse(
            fti.global_allow, u"{0} is not globally addable!".format(fti.id)
        )

    def test_ct_folder_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Folder")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.portal,
            "imio.events.Folder_id",
            title="imio.events.Folder container",
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type="Document",
                title="My Content",
            )
