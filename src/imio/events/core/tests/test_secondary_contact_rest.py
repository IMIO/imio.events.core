# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.events.core.rest.endpoint import EventsEndpointHandler
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.memoize.interfaces import ICacheChooser
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import alsoProvides

import unittest


def clear_search_cache(query):
    """Drop the @events RAM cache entry, as test_rest.py does.

    _perform_search is @ram.cache'd on a hash of the query plus a 240s bucket,
    so without this a previous test's result would be served here.
    """
    cache_key, _ = EventsEndpointHandler._cache_key(None, None, query)
    cache = getUtility(ICacheChooser)(cache_key)
    try:
        storage = cache.ramcache._getStorage()._data
        del storage["imio.events.core.rest.endpoint._perform_search"]
    except KeyError:
        pass


PHONE_ROW = {
    "contact_uid": "uid-1",
    "contact_title": "Service culture",
    "type_token": "work",
    "label": "Accueil",
    "type": "Telephone de travail",
    "number": "081 12 34 56",
    "visible_columns": ["number"],
}


class _EventFixture(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        alsoProvides(self.request, IImioEventsCoreLayer)
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event", title="Event"
        )
        self.event.start = datetime.now() + timedelta(days=10)
        self.event.end = datetime.now() + timedelta(days=11)
        # @events forces review_state=published, so an unpublished event would
        # simply not be found.
        api.content.transition(self.event, "publish")
        self.event.reindexObject()

    def _add_contact(self, contact_id="contact-1", uid="uid-1", title=""):
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id=contact_id,
        )
        contact.related_contact = uid
        contact.title = title
        contact.phones_display = [dict(PHONE_ROW, contact_uid=uid)]
        self.event.reindexObject()
        return contact

    def _expected(self, uid="uid-1", title="Reservations"):
        return {
            "uid": uid,
            "title": title,
            "phones": [{"number": "081 12 34 56"}],
            "mails": [],
            "urls": [],
        }


class TestFullSerializer(_EventFixture):
    def _serialize(self):
        return getMultiAdapter((self.event, self.request), ISerializeToJson)()

    def test_the_key_is_always_present(self):
        # A consumer never has to tell "absent" from "empty".
        self.assertEqual([], self._serialize()["secondary_contacts"])

    def test_the_snapshot_is_emitted(self):
        self._add_contact(title="Reservations")
        self.assertEqual([self._expected()], self._serialize()["secondary_contacts"])

    def test_several_contacts_keep_their_folder_order(self):
        self._add_contact("contact-1", "uid-a", "First")
        self._add_contact("contact-2", "uid-b", "Second")
        self.assertEqual(
            ["uid-a", "uid-b"],
            [item["uid"] for item in self._serialize()["secondary_contacts"]],
        )


class TestCatalogMetadata(_EventFixture):
    def _brain(self):
        return api.content.find(UID=self.event.UID())[0]

    def test_the_metadata_column_exists(self):
        catalog = api.portal.get_tool("portal_catalog")
        self.assertIn("secondary_contacts", catalog.schema())

    def test_an_event_without_children_has_an_empty_list(self):
        # The indexer returns [] rather than raising AttributeError, which would
        # store Missing.Value and break every consumer.
        self.assertEqual([], self._brain().secondary_contacts)

    def test_the_metadata_carries_the_snapshot(self):
        self._add_contact(title="Reservations")
        self.assertEqual([self._expected()], self._brain().secondary_contacts)


class TestParentReindexing(_EventFixture):
    """The metadata lives on the Event, the data lives in its children.

    Without a subscriber on the child, editing a Secondary contact leaves a
    stale snapshot in the catalog and downstream sites keep serving old rows.
    """

    def _metadata(self):
        return api.content.find(UID=self.event.UID())[0].secondary_contacts

    def _child(self, contact_id="contact-1", uid="uid-1"):
        # related_contact passed at creation, as the add form does: the
        # IObjectAddedEvent then fires with the field already set.
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id=contact_id,
            related_contact=uid,
        )
        contact.phones_display = [dict(PHONE_ROW, contact_uid=uid)]
        return contact

    def test_adding_a_child_refreshes_the_event_metadata(self):
        # No explicit reindex of the Event here: the subscriber must do it.
        self._child()
        self.assertEqual(["uid-1"], [item["uid"] for item in self._metadata()])

    def test_modifying_a_child_refreshes_the_event_metadata(self):
        from zope.lifecycleevent import modified

        contact = self._child()
        contact.title = "Reservations"
        modified(contact)
        self.assertEqual("Reservations", self._metadata()[0]["title"])

    def test_removing_a_child_refreshes_the_event_metadata(self):
        contact = self._child()
        self.assertEqual(1, len(self._metadata()))
        api.content.delete(obj=contact)
        self.assertEqual([], self._metadata())

    def test_removing_one_of_two_children_keeps_the_other(self):
        self._child("contact-1", "uid-a")
        second = self._child("contact-2", "uid-b")
        api.content.delete(obj=second)
        self.assertEqual(["uid-a"], [item["uid"] for item in self._metadata()])

    def test_the_handler_ignores_an_object_whose_parent_is_not_an_event(self):
        # Defensive: the FTI forbids it, but the handler must return quietly
        # rather than raise if a Secondary contact ever sits elsewhere.
        from imio.events.core.subscribers import reindex_event_secondary_contacts

        folder = api.content.create(
            container=self.agenda, type="imio.events.Folder", id="folder"
        )
        reindex_event_secondary_contacts(folder, None)

    def test_the_handler_ignores_an_orphan(self):
        from imio.events.core.contents.secondary_contact.content import SecondaryContact
        from imio.events.core.subscribers import reindex_event_secondary_contacts

        reindex_event_secondary_contacts(SecondaryContact(), None)


class TestEventsEndpoint(_EventFixture):
    """The path that actually serves downstream sites.

    @events serializes FULL objects only when the query carries a UID; the
    ordinary listing path builds summaries from catalog metadata. A key added to
    the full serializer alone would be invisible here.
    """

    def _query(self):
        return {"b_size": 10, "b_start": 0}

    def _items(self):
        # "min" = the next 365 days, which is where our event sits.
        self.request.form["event_dates.range"] = "min"
        query = self._query()
        clear_search_cache(query)
        endpoint = EventsEndpointHandler(self.portal, self.request)
        items = endpoint.search(dict(query)).get("items")
        clear_search_cache(query)
        return items

    def test_the_summary_carries_secondary_contacts(self):
        self._add_contact(title="Reservations")
        items = self._items()
        self.assertEqual(1, len(items))
        self.assertEqual([self._expected()], items[0]["secondary_contacts"])

    def test_an_event_without_contacts_still_carries_the_key(self):
        items = self._items()
        self.assertEqual(1, len(items))
        self.assertEqual([], items[0]["secondary_contacts"])
