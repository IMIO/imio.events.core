# -*- coding: utf-8 -*-

from datetime import date
from imio.events.core.utils import expand_occurences
from imio.events.core.utils import get_start_date
from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from zope.component import getMultiAdapter


class EventsEndpointGet(Service):
    def reply(self):
        query = self.request.form.copy()
        query = unflatten_dotted_dict(query)
        return EventsEndpointHandler(self.context, self.request).search(query)


class EventsEndpointHandler(SearchHandler):
    """ """

    # we receive b_size and b_start from smartweb with values already set
    # So we ignore these values but we must stock these to use it ...
    ignored_params = ["fullobjects", "b_size", "b_start"]

    def search(self, query=None):
        if query is None:
            query = {}

        b_size = query.get("b_size") or 20
        b_start = query.get("b_start") or 0

        for param in self.ignored_params:
            if param in query:
                del query[param]

        query["portal_type"] = "imio.events.Event"
        query["review_state"] = "published"
        query["b_size"] = 10000
        # Only future events
        today = date.today().isoformat()
        query["event_dates"] = {"query": today, "range": "min"}
        use_site_search_settings = False
        if "use_site_search_settings" in query:
            use_site_search_settings = True
            del query["use_site_search_settings"]

        if use_site_search_settings:
            query = self.filter_query(query)

        self._constrain_query_by_path(query)
        query = self._parse_query(query)
        lazy_resultset = self.catalog.searchResults(**query)

        self.request.form["metadata_fields"] = [
            "recurrence",
            "whole_day",
            "first_start",
            "first_end",
            "open_end",
        ]

        # ISerializeToJson use a default request batch so we force a "full" b_size and a "zero" b_start
        self.request.form["b_size"] = 10000
        self.request.form["b_start"] = 0
        results = getMultiAdapter((lazy_resultset, self.request), ISerializeToJson)()
        expanded_occurences = expand_occurences(results.get("items"))
        sorted_expanded_occurences = sorted(expanded_occurences, key=get_start_date)

        # It's time to get real b_size/b_start from the smartweb query
        self.request.form["b_size"] = b_size
        self.request.form["b_start"] = b_start
        batch = HypermediaBatch(self.request, sorted_expanded_occurences)

        results = {}
        results["@id"] = batch.canonical_url
        results["items_total"] = batch.items_total
        links = batch.links
        if links:
            results["batching"] = links
        results["items"] = [event for event in batch]
        return results