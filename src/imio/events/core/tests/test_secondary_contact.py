# -*- coding: utf-8 -*-

from imio.events.core.contents import ISecondaryContact
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class TestSecondaryContact(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="agenda",
        )
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )

    def _fti(self):
        return queryUtility(IDexterityFTI, name="imio.events.SecondaryContact")

    def test_ct_secondary_contact_fti(self):
        self.assertTrue(self._fti())

    def test_ct_secondary_contact_schema(self):
        self.assertEqual(ISecondaryContact, self._fti().lookupSchema())

    def test_ct_secondary_contact_factory(self):
        obj = createObject(self._fti().factory)
        self.assertTrue(
            ISecondaryContact.providedBy(obj),
            "ISecondaryContact not provided by {0}!".format(obj),
        )

    def test_ct_secondary_contact_globally_not_addable(self):
        self.assertFalse(self._fti().global_allow)

    def test_ct_secondary_contact_addable_in_event(self):
        obj = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        self.assertTrue(ISecondaryContact.providedBy(obj))

    def test_ct_secondary_contact_addable_several_times(self):
        # The multiplicity is the number of objects, not a multi-valued field.
        api.content.create(
            container=self.event, type="imio.events.SecondaryContact", id="contact-1"
        )
        api.content.create(
            container=self.event, type="imio.events.SecondaryContact", id="contact-2"
        )
        children = self.event.listFolderContents(
            contentFilter={"portal_type": "imio.events.SecondaryContact"}
        )
        self.assertEqual(2, len(children))

    def test_ct_secondary_contact_not_addable_in_agenda(self):
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.agenda,
                type="imio.events.SecondaryContact",
                id="contact-1",
            )

    def test_ct_secondary_contact_not_addable_in_portal(self):
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.portal,
                type="imio.events.SecondaryContact",
                id="contact-1",
            )

    def test_ct_secondary_contact_is_a_leaf(self):
        fti = self._fti()
        self.assertTrue(fti.filter_content_types)
        self.assertEqual((), tuple(fti.allowed_content_types))

    def test_ct_secondary_contact_add_permission(self):
        # Reuses the existing AddEvent permission: no new plumbing.
        self.assertEqual("imio.events.core.AddEvent", self._fti().add_permission)

    def test_event_allows_secondary_contact(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        self.assertIn("imio.events.SecondaryContact", fti.allowed_content_types)

    def test_related_contact_is_single_valued_on_the_events_vocabulary(self):
        field = ISecondaryContact["related_contact"]
        self.assertEqual(
            "imio.events.vocabulary.RemoteDirectoryContact", field.vocabularyName
        )
        self.assertTrue(field.required)

    def test_title_is_optional_and_an_untitled_object_is_valid(self):
        self.assertFalse(ISecondaryContact["title"].required)
        obj = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-no-title",
        )
        self.assertFalse(obj.title)

    def test_no_description_field(self):
        # plone.basic is deliberately not enabled: it would make the title
        # required and expose a description.
        self.assertNotIn("description", ISecondaryContact.names(all=True))

    def test_plone_basic_is_not_enabled(self):
        self.assertNotIn("plone.basic", self._fti().behaviors)

    def test_namefromtitle_is_enabled(self):
        self.assertIn("plone.namefromtitle", self._fti().behaviors)

    def test_the_three_grids_are_present(self):
        for name in ("phones_display", "mails_display", "urls_display"):
            self.assertIn(name, ISecondaryContact.names(all=True))

    def test_the_grids_live_in_their_own_fieldset(self):
        from plone.supermodel.interfaces import FIELDSETS_KEY
        from plone.supermodel.utils import mergedTaggedValueList

        fieldsets = mergedTaggedValueList(ISecondaryContact, FIELDSETS_KEY)
        names = [fieldset.__name__ for fieldset in fieldsets]
        self.assertIn("contact_informations", names)

    def test_workflow_chain_is_one_state(self):
        # Without this binding the type falls on the site's default chain, is
        # created private, and listFolderContents hides it from the anonymous
        # downstream site -- so @events would publish an empty list while every
        # Manager-run test passed.
        chain = api.portal.get_tool("portal_workflow").getChainFor(
            "imio.events.SecondaryContact"
        )
        self.assertEqual(("one_state_workflow",), tuple(chain))

    def test_a_created_contact_is_immediately_viewable(self):
        obj = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        self.assertEqual("published", api.content.get_state(obj))
