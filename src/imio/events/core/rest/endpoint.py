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

import hashlib
import json
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

    def _cache_key(func, instance, query):
        query_str = json.dumps(
            query, sort_keys=True
        )  # Tri pour éviter les variations d'ordre
        query_hash = hashlib.md5(
            query_str.encode("utf-8")
        ).hexdigest()  # Hash MD5 pour éviter une clé trop longue
        return (query_hash, time.time() // 240)

    @ram.cache(_cache_key)
    def _perform_search(self, query):
        """Cette méthode effectue la recherche et l'expansion des occurrences avant le tri."""
        if "fullobjects" in query:
            del query["fullobjects"]
        fullobjects = False
        query["portal_type"] = "imio.events.Event"
        query["review_state"] = "published"
        query["b_size"] = 400

        if "selected_agendas" in query:
            query["selected_agendas"] = sorted(
                set(self.get_cascading_agendas(query["selected_agendas"]))
            )

        self._constrain_query_by_path(query)
        query = self._parse_query(query)
        range_type = self.request.form.get("event_dates.range")
        if range_type == "max":
            self.optimize_max_range(query)
        lazy_resultset = self.catalog.searchResults(**query)

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
        self.request.form["b_size"] = query["b_size"]
        self.request.form["b_start"] = 0
        results = getMultiAdapter((lazy_resultset, self.request), ISerializeToJson)(
            fullobjects=fullobjects
        )
        expanded_occurrences = expand_occurences(results.get("items"), range_type)
        return expanded_occurrences, range_type

    def search(self, query=None):
        if is_log_active():
            tps1 = time.time()
        if not query:
            return {"items": []}

        b_size = query.pop("b_size", 20)
        b_start = query.pop("b_start", 0)
        # Appel à la nouvelle méthode pour obtenir les résultats de la recherche avant le tri et l'expansion
        # expanded_occurrences, range_type, b_size, b_start = self._perform_search(query)
        expanded_occurrences, range_type = self._perform_search(query)
        sorted_occurrences = self.filter_and_sort_occurrences(
            expanded_occurrences, range_type
        )

        self.request.form["b_start"] = b_start
        self.request.form["b_size"] = b_size
        if len(expanded_occurrences) < int(b_size):
            self.request.form["b_size"] = str(len(expanded_occurrences))

        batch = HypermediaBatch(self.request, sorted_occurrences)

        if is_log_active():
            tps2 = time.time()
            logger.info(f"=====> query : {results['@id']}")
            logger.info(f"=====> time (total) : {tps2 - tps1}")
        results = {
            "@id": batch.canonical_url,
            "items_total": batch.items_total,
            "batching": batch.links if batch.links else None,
            "items": list(batch),
        }
        return results

    def get_cascading_agendas(self, initial_agenda):
        global_list = []

        def recursive_generator(agenda_UID):
            # obj est l'agenda
            obj = api.content.get(UID=agenda_UID)
            populating_agendas = [agenda_UID]
            global_list.append(agenda_UID)

            for rv in getattr(obj, "populating_agendas", []):
                if (
                    getattr(rv, "to_object", None)
                    and rv.to_object.UID() not in global_list
                ):
                    if api.content.get_state(rv.to_object) == "published":
                        populating_agendas.append(rv.to_object.UID())
                        global_list.append(rv.to_object.UID())
                        yield from recursive_generator(rv.to_object.UID())

            yield from populating_agendas

        return recursive_generator(initial_agenda)

    def optimize_max_range(self, query):
        now = datetime.now(timezone.utc)
        one_year_ago = now - timedelta(days=365)
        query["event_dates"] = {
            "query": [one_year_ago.isoformat(), now.isoformat()],
            "range": "min:max",
        }

    def filter_and_sort_occurrences(self, occurrences, range_type):
        if not range_type:
            return occurrences

        current_date = datetime.now(timezone.utc)
        filter_func = {
            "min": lambda occ: datetime.fromisoformat(occ["start"]) >= current_date
            or (
                datetime.fromisoformat(occ["start"])
                <= current_date
                <= datetime.fromisoformat(occ["end"])
            ),
            "max": lambda occ: datetime.fromisoformat(occ["end"]) < current_date
            or (
                datetime.fromisoformat(occ["start"])
                <= current_date
                <= datetime.fromisoformat(occ["end"])
            ),
            "min:max": lambda occ: self.is_within_range(occ),
        }.get(range_type, lambda occ: True)

        if is_log_active():
            # DEBUG : log all events occurrences that not conserved (excluded)
            excluded_occurrences = []
            filtered_occurrences = []
            for occ in occurrences:
                if filter_func(occ):
                    filtered_occurrences.append(occ)
                else:
                    excluded_occurrences.append(occ)

            if excluded_occurrences:
                logger.warning(
                    f"=====> Événements exclus ({range_type}): {excluded_occurrences}"
                )
            return sorted(
                filtered_occurrences, key=get_start_date, reverse=(range_type == "max")
            )
        else:
            return sorted(
                filter(filter_func, occurrences),
                key=get_start_date,
                reverse=(range_type == "max"),
            )

    def is_within_range(self, occurrence):
        min_date, max_date = self.request.form.get("event_dates.query", [None, None])
        if min_date and max_date:
            min_date = datetime.fromisoformat(min_date).replace(tzinfo=timezone.utc)
            max_date = datetime.fromisoformat(max_date).replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
            start_date = datetime.fromisoformat(occurrence["start"])
            end_date = datetime.fromisoformat(occurrence["end"])
            return (
                (min_date <= start_date <= max_date)
                or (start_date <= min_date and end_date >= min_date)
                or (start_date <= max_date and end_date >= max_date)
            )
        return True
