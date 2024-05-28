# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from imio.events.core.utils import expand_occurences
from imio.events.core.utils import get_start_date
from imio.smartweb.common.rest.search_filters import SearchFiltersHandler
from imio.smartweb.common.utils import is_log_active
from plone import api
from plone.memoize import ram
from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from zope.component import getMultiAdapter

import logging
import time

logger = logging.getLogger("imio.events.core")


class SearchFiltersGet(Service):
    """
    This is a temporary shortcut to calculate search-filters based on @events
    search results logic. We need to refactor & test (more) this module.
    """

    def reply(self):
        query = self.request.form.copy()
        if "metadata_fields" not in query:
            return {}
        query = unflatten_dotted_dict(query)
        results = EventsEndpointHandler(self.context, self.request).search(query)
        UIDs = [item["UID"] for item in results["items"]]
        query = {
            "UID": UIDs,
            "metadata_fields": ["category", "local_category", "topics"],
        }
        return SearchFiltersHandler(self.context, self.request).search(query)


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

    def _cache_key(func, instance, query):
        return (query, time.time() // 60)

    @ram.cache(_cache_key)
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
                    if hasattr(rv, "to_object"):
                        if (
                            rv.to_object is not None
                            and rv.to_object.UID() not in global_list
                        ):
                            obj = rv.to_object
                            status = api.content.get_state(obj)
                            if status == "published":
                                # to cover initial_agenda UID
                                populating_agendas.append(agenda_UID)
                                global_list.append(agenda_UID)

                                # to cover RelationValue agenda UID
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
        tps1 = time.time()
        self._constrain_query_by_path(query)
        # self.request.form["path"] = query["path"]
        tps2 = time.time()
        query = self._parse_query(query)
        tps3 = time.time()
        range = self.request.form.get("event_dates.range")

        # Try to optimize the query
        if range == "max":
            query["b_size"] = 1000
            now = datetime.now(timezone.utc)
            one_year_ago = now - timedelta(days=365)
            date_string = now.strftime("%Y-%m-%d")
            one_year_ago_string = one_year_ago.strftime("%Y-%m-%d")
            query["event_dates"]["query"] = [one_year_ago_string, date_string]
            query["event_dates"]["range"] = "min:max"
            self.request.form["event_dates.query"] = {
                "min": one_year_ago_string,
                "max": date_string,
            }
            self.request.form["event_dates.range"] = "min:max"
        lazy_resultset = self.catalog.searchResults(**query)
        tps4 = time.time()
        if "metadata_fields" not in self.request.form:
            self.request.form["metadata_fields"] = []
        self.request.form["metadata_fields"] += [
            "container_uid",
            "recurrence",
            "whole_day",
            "first_start",
            "first_end",
            "open_end",
        ]
        # ISerializeToJson use a default request batch so we force a "full" b_size and a "zero" b_start
        self.request.form["b_size"] = 10000
        self.request.form["b_start"] = 0

        # To do : cache all datas and get from cache ?
        results = getMultiAdapter((lazy_resultset, self.request), ISerializeToJson)(
            fullobjects=fullobjects
        )
        tps5 = time.time()
        expanded_occurences = expand_occurences(results.get("items"), range)
        tps6 = time.time()
        # range is None when we click on an occurence
        if range is None:
            sorted_expanded_occurences = expanded_occurences
        if range == "min":
            filter_expanded_occurences = []
            for occurrence in expanded_occurences:
                start_date = datetime.fromisoformat(occurrence["start"])
                end_date = datetime.fromisoformat(occurrence["end"])
                current_date = datetime.now(timezone.utc)
                if start_date >= current_date or end_date >= current_date:
                    filter_expanded_occurences.append(occurrence)
            sorted_expanded_occurences = sorted(
                filter_expanded_occurences, key=get_start_date
            )
        if range == "max":
            filter_expanded_occurences = []
            for occurrence in expanded_occurences:
                end_date = datetime.fromisoformat(occurrence["end"])
                current_date = datetime.now(timezone.utc)
                if end_date < current_date:
                    filter_expanded_occurences.append(occurrence)
            sorted_expanded_occurences = sorted(
                filter_expanded_occurences, key=get_start_date, reverse=True
            )
        if range == "min:max":
            filter_expanded_occurences = []
            for occurrence in expanded_occurences:
                min_date, max_date = self.request.form.get("event_dates.query")
                min_date = datetime.fromisoformat(min_date).replace(tzinfo=timezone.utc)
                max_date = (
                    datetime.strptime(max_date, "%Y-%m-%d")
                    .replace(hour=23, minute=59, second=59)
                    .replace(tzinfo=timezone.utc)
                )
                start_date = datetime.fromisoformat(occurrence["start"])
                end_date = datetime.fromisoformat(occurrence["end"])
                if (min_date <= start_date <= max_date) or (
                    start_date <= min_date and end_date >= min_date
                ):
                    filter_expanded_occurences.append(occurrence)
            sorted_expanded_occurences = sorted(
                filter_expanded_occurences, key=get_start_date
            )
        tps7 = time.time()
        # It's time to get real b_size/b_start from the smartweb query
        self.request.form["b_size"] = b_size
        self.request.form["b_start"] = b_start
        batch = HypermediaBatch(self.request, sorted_expanded_occurences)
        if is_log_active():
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
