# -*- coding: utf-8 -*-

from datetime import datetime
from freezegun import freeze_time
from imio.events.core.rest.endpoint import EventsEndpointHandler
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.memoize.interfaces import ICacheChooser
from plone import api
from unittest.mock import patch
from zope.component import getUtility

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
        self.assertEqual(len(items), 3)
        clear_search_cache(query)

        event4.start = datetime(2023, 3, 1, 0, 0)
        event4.end = datetime(2023, 3, 29, 0, 0)
        event4.recurrence = "RRULE:FREQ=WEEKLY;COUNT=5"
        api.content.transition(event4, "publish")
        event4.reindexObject()
        response = endpoint.search(query)
        items = response.get("items")
        self.assertEqual(len(items), 5)
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
        self.assertEqual(len(items), 4)
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
