# -*- coding: utf-8 -*-

from datetime import date
from imio.events.core.utils import expand_occurences
from imio.events.core.utils import get_start_date
from plone import api
from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from zope.component import getMultiAdapter

import logging
import time

logger = logging.getLogger("imio.events.core")


class EventsEndpointGet(Service):
    def reply(self):
        query = self.request.form.copy()
        query = unflatten_dotted_dict(query)
        return EventsEndpointHandler(self.context, self.request).search(query)


class EventsEndpointHandler(SearchHandler):
    """ """

    # we receive b_size and b_start from smartweb with values already set
    # So we ignore these values but we must stock these to use it ...
    ignored_params = ["b_size", "b_start"]

    def search(self, query=None):
        if query is None:
            query = {}
        b_size = query.get("b_size") or 20
        b_start = query.get("b_start") or 0

        for param in self.ignored_params:
            if param in query:
                del query[param]

        if "fullobjects" in query:
            fullobjects = True
            del query["fullobjects"]
        else:
            fullobjects = False

        query["portal_type"] = "imio.events.Event"
        query["review_state"] = "published"
        query["b_size"] = 10000

        def cascading_agendas(initial_agenda):
            global_list = []

            def recursive_generator(agenda_UID):
                nonlocal global_list
                obj = api.content.get(UID=agenda_UID)
                populating_agendas = []
                for rv in obj.populating_agendas:
                    if rv.to_object.UID() not in global_list:
                        if rv.to_object is not None:
                            obj = rv.to_object
                            status = api.content.get_state(obj)
                            if status == "published":
                                populating_agendas.append(rv.to_object.UID())
                                global_list.append(rv.to_object.UID())
                for agenda_UID in populating_agendas:
                    yield from recursive_generator(agenda_UID)
                yield agenda_UID

            yield from recursive_generator(initial_agenda)

        # To cover cascading "populating_agendas" field
        if "selected_agendas" in query:
            selected_agendas = [
                agenda_UID
                for agenda_UID in cascading_agendas(query["selected_agendas"])
            ]
            all_agendas = list(set(selected_agendas))
            query["selected_agendas"] = all_agendas

        # Only future events
        today = date.today().isoformat()
        query["event_dates"] = {"query": today, "range": "min"}
        tps1 = time.time()
        self._constrain_query_by_path(query)
        tps2 = time.time()
        query = self._parse_query(query)
        tps3 = time.time()
        lazy_resultset = self.catalog.searchResults(**query)
        tps4 = time.time()
        if "metadata_fields" not in self.request.form:
            self.request.form["metadata_fields"] = []
        self.request.form["metadata_fields"] += [
            "recurrence",
            "whole_day",
            "first_start",
            "first_end",
            "open_end",
        ]
        # ISerializeToJson use a default request batch so we force a "full" b_size and a "zero" b_start
        self.request.form["b_size"] = 10000
        self.request.form["b_start"] = 0
        results = getMultiAdapter((lazy_resultset, self.request), ISerializeToJson)(
            fullobjects=fullobjects
        )
        tps5 = time.time()
        expanded_occurences = expand_occurences(results.get("items"))
        sorted_expanded_occurences = sorted(expanded_occurences, key=get_start_date)
        tps6 = time.time()

        # It's time to get real b_size/b_start from the smartweb query
        self.request.form["b_size"] = b_size
        self.request.form["b_start"] = b_start
        batch = HypermediaBatch(self.request, sorted_expanded_occurences)
        tps7 = time.time()
        logger.info(f"query : {results['@id']}")
        logger.info(f"time constrain_query_by_path : {tps2 - tps1}")
        logger.info(f"time _parse_query : {tps3 - tps2}")
        logger.info(f"time catalog lazy_resultset : {tps4 - tps3}")
        logger.info(f"time MultiAdapter fullobj : {tps5 - tps4}")
        logger.info(f"time occurences : {tps6 - tps5}")
        logger.info(f"time batch : {tps7 - tps6}")
        logger.info(f"time (total) : {tps7 - tps1}")

        results = {}
        results["@id"] = batch.canonical_url
        results["items_total"] = batch.items_total
        links = batch.links
        if links:
            results["batching"] = links
        results["items"] = [event for event in batch]
        return results
