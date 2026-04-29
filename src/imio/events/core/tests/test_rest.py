# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from freezegun import freeze_time
from imio.events.core.rest.endpoint import EventsEndpointHandler
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.memoize.interfaces import ICacheChooser
from plone import api
from unittest.mock import patch
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.intid.interfaces import IIntIds

import unittest


# def clear_search_cache(query):
#     cache_key = EventsEndpointHandler._cache_key("func", "instance", query)
#     cache = getUtility(ICacheChooser)(cache_key)
#     storage = cache.ramcache._getStorage()._data
#     del storage["imio.events.core.rest.endpoint.search"]


def clear_search_cache(query):
    # Générer la clé de cache correcte
    cache_key, _ = EventsEndpointHandler._cache_key(
        None, None, query
    )  # Ignorer `func` et `instance`

    # Récupérer l'instance de cache
    cache = getUtility(ICacheChooser)(cache_key)

    # Vérifier si la clé est présente et la supprimer proprement
    try:
        storage = cache.ramcache._getStorage()._data
        del storage["imio.events.core.rest.endpoint._perform_search"]
        # cache.ramcache.invalidate(cache_key)
    except KeyError:
        pass  # La clé n'existe pas, donc rien à faire


class RestFunctionalTest(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.request = self.layer["request"]
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

    def test_query(self):
        endpoint = EventsEndpointHandler(self.portal, self.request)
        # None query
        query = None
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 0)
        clear_search_cache(query)

    @freeze_time("2023-03-18")
    def test_get_events_from_agenda(self):
        event1 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event1",
            title="Event 1",
        )
        event1.start = datetime(2023, 3, 27, 0, 0)
        event1.end = datetime(2023, 4, 27, 0, 0)
        event1.reindexObject()

        event2 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event2",
            title="Event 2",
        )
        event2.start = datetime(2023, 3, 18, 0, 0)
        event2.end = datetime(2023, 3, 18, 23, 59)
        event2_nb_occurences = 3
        event2.recurrence = f"RRULE:FREQ=WEEKLY;COUNT={event2_nb_occurences}"
        event2.reindexObject()

        event3 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event3",
            title="Event 3",
        )
        event3.start = datetime(2023, 3, 25, 0, 0)
        event3.end = datetime(2023, 3, 25, 23, 59)
        endpoint = EventsEndpointHandler(self.portal, self.request)
        query = {
            "b_size": 10,
            "b_start": 0,
        }

        # start in past , end in future
        event4 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event4",
            title="Event 4",
        )
        event4.start = datetime(2023, 3, 1, 0, 0)
        event4.end = datetime(2023, 4, 27, 0, 0)
        event4.reindexObject()

        # All tests below are done to retrieve FUTURE events
        self.request.form["event_dates.range"] = "min"

        response = endpoint.search(query)
        items = response.get("items")
        # Assert private event are not presents
        self.assertEqual(len(items), 0)
        clear_search_cache(query)

        # Assert published event are presents
        api.content.transition(event1, "publish")
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 1)
        clear_search_cache(query)

        # Assert event that began in past and end in future are presents
        api.content.transition(event4, "publish")
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 2)
        api.content.transition(event4, "retract")
        clear_search_cache(query)

        # Assert events occurrences are presents
        api.content.transition(event2, "publish")
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 1 + event2_nb_occurences)
        clear_search_cache(query)

        # Assert passed event aren't get anymore (start_date and end_date are in the past)
        # But future occurrences of this event are kept
        event2.start = datetime(2023, 3, 16, 0, 0)
        event2.reindexObject()
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 4)
        clear_search_cache(query)

        event4.start = datetime(2023, 3, 1, 0, 0)
        event4.end = datetime(2023, 3, 29, 0, 0)
        event4.recurrence = "RRULE:FREQ=WEEKLY;COUNT=5"
        api.content.transition(event4, "publish")
        event4.reindexObject()
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 9)
        api.content.transition(event4, "retract")
        event4.reindexObject()
        clear_search_cache(query)

        # Assert first_start index was updated
        item = list(
            set([i.get("first_start") for i in items if i.get("title") == "Event 2"])
        )
        self.assertEqual(item[0], "2023-03-16T00:00:00")

        api.content.transition(event3, "publish")
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 5)
        clear_search_cache(query)

        # Assert list is sorted by start date
        format_str = "%Y-%m-%dT%H:%M:%S%z"
        dates = [datetime.strptime(i.get("start"), format_str) for i in items]
        self.assertEqual(min(dates), dates[0])
        self.assertEqual(max(dates), dates[-1])

    @freeze_time("2023-03-18")
    @patch("requests.post")
    def test_batching_events_from_agenda(self, m):
        event1 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event1",
            title="Event 1",
        )
        event1.start = datetime(2023, 3, 27, 0, 0)
        event1.end = datetime(2023, 4, 27, 0, 0)
        event1.reindexObject()

        event2 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event2",
            title="Event 2",
        )
        event2.start = datetime(2023, 3, 18, 0, 0)
        event2.end = datetime(2023, 3, 18, 23, 59)
        event2_nb_occurences = 3
        event2.recurrence = f"RRULE:FREQ=WEEKLY;COUNT={event2_nb_occurences}"
        event2.reindexObject()

        event3 = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event3",
            title="Event 3",
        )
        event3.start = datetime(2023, 3, 25, 0, 0)
        event3.end = datetime(2023, 3, 25, 23, 59)
        event3.reindexObject()
        endpoint = EventsEndpointHandler(self.portal, self.request)
        api.content.transition(event1, "publish")
        api.content.transition(event2, "publish")
        api.content.transition(event3, "publish")

        query = {
            "b_size": 10,
            "b_start": 0,
        }
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 5)
        clear_search_cache(query)

        query = {
            "b_size": 3,
            "b_start": 0,
        }
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 3)
        clear_search_cache(query)

        query = {
            "b_size": 3,
            "b_start": 3,
        }
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 2)
        clear_search_cache(query)

    @freeze_time("2026-04-24")
    def test_ongoing_long_duration_event_retrieved_with_min_range(self):
        """Long-duration event (started months ago, ends months from now) must be
        returned for range=min even when event_dates index only has the start date
        (stale index scenario after upgrading the indexer)."""
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="long_event",
            title="Long Duration Event",
        )
        event.start = datetime(2025, 6, 1, 0, 0)
        event.end = datetime(2026, 6, 30, 0, 0)
        event.reindexObject()
        api.content.transition(event, "publish")

        # Simulate stale event_dates index: only the original start date is indexed,
        # not all the intermediate days that the current indexer would produce.
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=event.UID())[0]
        rid = brain.getRID()
        idx = catalog._catalog.indexes["event_dates"]
        idx.unindex_object(rid)

        class _StaleIndexData:
            event_dates = ("2025-06-01",)

        idx.index_object(rid, _StaleIndexData())

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min"
        # Pass event_dates in the query dict as the real endpoint does via
        # EventsEndpointGet.reply() → unflatten_dotted_dict(request.form.copy())
        query = {
            "b_size": 10,
            "b_start": 0,
            "event_dates": {"query": "2026-04-24", "range": "min"},
        }
        clear_search_cache({"event_dates": {"query": "2026-04-24", "range": "min"}})

        response = endpoint.search(query)
        items = response.get("items")
        titles = [i["title"] for i in items]
        self.assertIn("Long Duration Event", titles)

    @freeze_time("2026-04-24")
    def test_open_end_event_started_in_past_retrieved_with_min_range(self):
        """An open_end event has no defined end and must be considered ongoing
        once it has started. It must therefore be returned for range=min even
        when its explicit end date is in the past."""
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="open_end_event",
            title="Open End Event",
        )
        # Start 10 days ago, end same day (open_end means the explicit end is meaningless)
        event.start = datetime(2026, 4, 14, 0, 0)
        event.end = datetime(2026, 4, 14, 0, 0)
        event.whole_day = True
        event.open_end = True
        event.reindexObject()
        api.content.transition(event, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min"
        query = {"b_size": 10, "b_start": 0}

        response = endpoint.search(query)
        items = response.get("items")
        titles = [i["title"] for i in items]
        self.assertIn("Open End Event", titles)

    @freeze_time("2026-04-29")
    def test_min_range_does_not_truncate_future_events_when_many_published(self):
        """Regression: with sort_on=event_dates ASC, the catalog returns past
        events first. The previous code dropped event_dates from the catalog
        query (no date filter) and capped b_size to 400, so a large set of
        past events filled the slot before any future event made it through
        the Python filter. With the catalog filter restored and b_size tied
        to len(lazy_resultset), every future event must come back.
        """
        # 6 past events (would have filled the b_size cap under the old code
        # if it were lower; here we just verify nothing is dropped along the way).
        for i, start in enumerate(
            [
                datetime(2025, 1, 5),
                datetime(2025, 3, 10),
                datetime(2025, 6, 15),
                datetime(2025, 9, 20),
                datetime(2025, 12, 1),
                datetime(2026, 2, 14),
            ]
        ):
            evt = api.content.create(
                container=self.agenda,
                type="imio.events.Event",
                id=f"past_event_{i}",
                title=f"Past Event {i}",
            )
            evt.start = start
            evt.end = start + timedelta(hours=2)
            evt.reindexObject()
            api.content.transition(evt, "publish")

        # 2 future events
        for i, start in enumerate([datetime(2026, 7, 10), datetime(2026, 12, 25)]):
            evt = api.content.create(
                container=self.agenda,
                type="imio.events.Event",
                id=f"future_event_{i}",
                title=f"Future Event {i}",
            )
            evt.start = start
            evt.end = start + timedelta(hours=2)
            evt.reindexObject()
            api.content.transition(evt, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min"
        self.request.form["sort_on"] = "event_dates"
        query = {"b_size": 100, "b_start": 0, "sort_on": "event_dates"}
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            del self.request.form["sort_on"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Future Event 0", titles)
        self.assertIn("Future Event 1", titles)
        # All past events ended hours after their start in 2025/early 2026, so
        # _matches_min_range must reject them.
        for i in range(6):
            self.assertNotIn(f"Past Event {i}", titles)

    @freeze_time("2026-04-29")
    def test_max_range_returns_only_past_events_descending(self):
        """range=max returns events whose end date is before now, sorted
        most-recent-first. Future-only events must not appear."""
        past_recent = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="past_recent",
            title="Past Recent",
        )
        past_recent.start = datetime(2026, 3, 1)
        past_recent.end = datetime(2026, 3, 1, 23, 59)
        past_recent.reindexObject()
        api.content.transition(past_recent, "publish")

        past_older = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="past_older",
            title="Past Older",
        )
        past_older.start = datetime(2025, 8, 1)
        past_older.end = datetime(2025, 8, 1, 23, 59)
        past_older.reindexObject()
        api.content.transition(past_older, "publish")

        future = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="future_only",
            title="Future Only",
        )
        future.start = datetime(2026, 7, 1)
        future.end = datetime(2026, 7, 1, 23, 59)
        future.reindexObject()
        api.content.transition(future, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "max"
        query = {"b_size": 10, "b_start": 0}
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Past Recent", titles)
        self.assertIn("Past Older", titles)
        self.assertNotIn("Future Only", titles)
        # Descending sort: most recent past comes first
        self.assertLess(titles.index("Past Recent"), titles.index("Past Older"))

    @freeze_time("2026-04-29")
    def test_max_range_includes_ongoing_event(self):
        """The Python filter for range=max keeps events whose [start, end]
        bracket `now` (started in the past, not yet finished)."""
        ongoing = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="ongoing",
            title="Ongoing",
        )
        ongoing.start = datetime(2026, 1, 15)
        ongoing.end = datetime(2026, 12, 15)
        ongoing.reindexObject()
        api.content.transition(ongoing, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "max"
        query = {"b_size": 10, "b_start": 0}
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Ongoing", titles)

    @freeze_time("2026-04-29")
    def test_min_max_range_keeps_event_inside_window(self):
        """range=min:max with a custom window keeps events whose start falls
        inside [min_date, max_date]."""
        inside = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="inside",
            title="Inside Window",
        )
        inside.start = datetime(2026, 6, 10)
        inside.end = datetime(2026, 6, 12)
        inside.reindexObject()
        api.content.transition(inside, "publish")

        outside = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="outside",
            title="Outside Window",
        )
        outside.start = datetime(2026, 9, 1)
        outside.end = datetime(2026, 9, 2)
        outside.reindexObject()
        api.content.transition(outside, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min:max"
        self.request.form["event_dates.query"] = ["2026-05-01", "2026-08-31"]
        query = {
            "b_size": 10,
            "b_start": 0,
            "event_dates": {
                "query": ["2026-05-01", "2026-08-31"],
                "range": "min:max",
            },
        }
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            del self.request.form["event_dates.query"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Inside Window", titles)
        self.assertNotIn("Outside Window", titles)

    @freeze_time("2026-04-29")
    def test_min_max_range_keeps_event_spanning_window(self):
        """An event that starts before the window and ends after it must
        still be returned (is_within_range branches 2 & 3)."""
        spanning = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="spanning",
            title="Spanning",
        )
        spanning.start = datetime(2026, 5, 1)
        spanning.end = datetime(2026, 9, 30)
        spanning.reindexObject()
        api.content.transition(spanning, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min:max"
        self.request.form["event_dates.query"] = ["2026-06-01", "2026-08-01"]
        query = {
            "b_size": 10,
            "b_start": 0,
            "event_dates": {
                "query": ["2026-06-01", "2026-08-01"],
                "range": "min:max",
            },
        }
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            del self.request.form["event_dates.query"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Spanning", titles)

    @freeze_time("2026-04-29")
    def test_no_range_type_returns_all_published_events_unfiltered(self):
        """Without event_dates.range, filter_and_sort_occurrences short-
        circuits and returns everything the catalog gave (no date filter,
        no sort)."""
        past = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="past_no_range",
            title="Past",
        )
        past.start = datetime(2025, 6, 1)
        past.end = datetime(2025, 6, 1, 23, 59)
        past.reindexObject()
        api.content.transition(past, "publish")

        future = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="future_no_range",
            title="Future",
        )
        future.start = datetime(2026, 8, 1)
        future.end = datetime(2026, 8, 1, 23, 59)
        future.reindexObject()
        api.content.transition(future, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        # No event_dates.range in request.form
        query = {"b_size": 10, "b_start": 0}
        try:
            response = endpoint.search(query)
        finally:
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Past", titles)
        self.assertIn("Future", titles)

    @freeze_time("2026-04-29")
    def test_unpublished_events_are_excluded(self):
        """The catalog query forces review_state=published; private/draft
        events must never appear in @events results."""
        published = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="published",
            title="Published",
        )
        published.start = datetime(2026, 7, 1)
        published.end = datetime(2026, 7, 1, 23, 59)
        published.reindexObject()
        api.content.transition(published, "publish")

        private = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="private",
            title="Private",
        )
        private.start = datetime(2026, 7, 5)
        private.end = datetime(2026, 7, 5, 23, 59)
        private.reindexObject()
        # No transition → stays private

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min"
        query = {"b_size": 10, "b_start": 0}
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Published", titles)
        self.assertNotIn("Private", titles)

    @freeze_time("2026-04-29")
    def test_selected_agendas_cascade_via_populating_agendas(self):
        """An event published in agenda B must appear when querying agenda A
        if A has B in its populating_agendas relation. get_cascading_agendas
        walks that graph recursively."""
        secondary = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="secondary_agenda",
        )
        # Agendas use one_state_workflow → already in "published" state on creation.

        # Wire main agenda to consume from secondary
        intids = getUtility(IIntIds)
        self.agenda.populating_agendas = [
            RelationValue(intids.getId(secondary)),
        ]
        self.agenda.reindexObject()

        evt_in_secondary = api.content.create(
            container=secondary,
            type="imio.events.Event",
            id="evt_secondary",
            title="From Secondary",
        )
        evt_in_secondary.start = datetime(2026, 7, 10)
        evt_in_secondary.end = datetime(2026, 7, 10, 23, 59)
        evt_in_secondary.reindexObject()
        api.content.transition(evt_in_secondary, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min"
        query = {
            "b_size": 10,
            "b_start": 0,
            "selected_agendas": self.agenda.UID(),
        }
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("From Secondary", titles)

    @freeze_time("2026-04-29")
    def test_event_type_catalog_filter(self):
        """The event_type catalog index lets clients filter by event nature.
        Multiple values OR-combine at the catalog level."""
        evt_type_a = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="evt_type_a",
            title="Type A",
        )
        evt_type_a.start = datetime(2026, 7, 10)
        evt_type_a.end = datetime(2026, 7, 10, 23, 59)
        evt_type_a.event_type = "event-driven"
        evt_type_a.reindexObject()
        api.content.transition(evt_type_a, "publish")

        evt_type_b = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="evt_type_b",
            title="Type B",
        )
        evt_type_b.start = datetime(2026, 7, 12)
        evt_type_b.end = datetime(2026, 7, 12, 23, 59)
        evt_type_b.event_type = "courses"
        evt_type_b.reindexObject()
        api.content.transition(evt_type_b, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min"
        query = {
            "b_size": 10,
            "b_start": 0,
            "event_type": "event-driven",
        }
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            clear_search_cache(query)

        titles = [i["title"] for i in response.get("items", [])]
        self.assertIn("Type A", titles)
        self.assertNotIn("Type B", titles)

    @freeze_time("2026-04-29")
    def test_recurring_event_with_min_range_returns_future_occurrences_only(self):
        """A recurring event whose first start lies in the past must still
        emit its future occurrences. Past occurrences must be filtered out
        by _matches_min_range."""
        recurring = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="recurring",
            title="Weekly",
        )
        # First occurrence 2 weeks before now, then weekly for 6 occurrences.
        # With now=2026-04-29: occurrences at 2026-04-15, 2026-04-22 (past),
        # 2026-04-29 (today), 2026-05-06, 2026-05-13, 2026-05-20 (future).
        recurring.start = datetime(2026, 4, 15, 10, 0)
        recurring.end = datetime(2026, 4, 15, 12, 0)
        recurring.recurrence = "RRULE:FREQ=WEEKLY;COUNT=6"
        recurring.reindexObject()
        api.content.transition(recurring, "publish")

        endpoint = EventsEndpointHandler(self.portal, self.request)
        self.request.form["event_dates.range"] = "min"
        query = {"b_size": 20, "b_start": 0}
        try:
            response = endpoint.search(query)
        finally:
            del self.request.form["event_dates.range"]
            clear_search_cache(query)

        weekly_items = [i for i in response.get("items", []) if i["title"] == "Weekly"]
        # Today's occurrence is still ongoing (start <= now <= end fails since
        # end is 12:00 and freezegun is at 00:00, so start==today 10:00 >= now
        # 00:00 → True). 4 future ones expected: 04-29, 05-06, 05-13, 05-20.
        self.assertEqual(len(weekly_items), 4)


# <audit>
#   <file>test_rest.py</file>
#   <requirements_applied>R1, R2, R5, R6</requirements_applied>
#   <deviations>
#     R3 not applied: per-test events live in each test method (specific to
#     the scenario, not shared across classes). Matches existing pattern in
#     test_get_events_from_agenda / test_batching_events_from_agenda.
#
#     The class is named RestFunctionalTest but uses
#     IMIO_EVENTS_CORE_INTEGRATION_TESTING (integration, not functional).
#     Pre-existing; not renamed to preserve external references.
#
#     Each new test cleans request.form via try/finally to avoid leaking
#     event_dates.range / sort_on into sibling tests (the layer reuses the
#     request object). The pre-existing tests do not clean up; not retro-
#     fitted to keep the diff focused on the regression coverage.
#   </deviations>
#   <questions>None</questions>
# </audit>
