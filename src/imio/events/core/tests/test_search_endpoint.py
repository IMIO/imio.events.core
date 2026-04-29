# -*- coding: utf-8 -*-

from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.events.core.rest.search.endpoint import SearchGet
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getSiteManager
from zope.interface import Interface, alsoProvides

import unittest


def _make_service(cls, context, request):
    """
    Instantiate a plone.rest Service subclass without going through the full
    Zope adapter machinery.  Service has no __init__, so we use __new__ and
    set context / request explicitly — the same attributes that the traversal
    layer sets when a real HTTP request reaches the service.
    """
    service = cls.__new__(cls)
    service.context = context
    service.request = request
    return service


class TestSearchGet(unittest.TestCase):
    """Tests for SearchGet.reply (the @search plone.restapi service override)."""

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        alsoProvides(self.request, IImioEventsCoreLayer)
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

    def test_reply_returns_plone_restapi_search_structure(self):
        """reply() delegates to BaseSearchGet and returns the standard search envelope."""
        service = _make_service(SearchGet, self.portal, self.request)
        result = service.reply()
        self.assertIn("items", result)
        self.assertIn("items_total", result)

    def test_reply_includes_published_events(self):
        """reply() returns published events visible to the current user."""
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
            title="Published Event",
        )
        api.content.transition(event, "publish")
        self.request.form["portal_type"] = "imio.events.Event"
        try:
            service = _make_service(SearchGet, self.portal, self.request)
            result = service.reply()
        finally:
            del self.request.form["portal_type"]
        ids = [item["@id"] for item in result["items"]]
        self.assertTrue(any(event.getId() in url for url in ids))

    def test_layer_service_resolves_to_custom_class(self):
        """The @search service for GET/JSON on the events layer wraps our SearchGet."""
        # plone.rest registers services as multi-adapters keyed by
        # "<METHOD>_<type>_<subtype>_<name>", e.g. "GET_application_json_@search".
        # The directive creates a new class inheriting from (factory, BrowserView),
        # so the registered factory is a subclass of SearchGet, not SearchGet itself.
        sm = getSiteManager()
        factory = sm.adapters.lookup(
            (Interface, IImioEventsCoreLayer),
            Interface,
            "GET_application_json_@search",
        )
        self.assertIsNotNone(factory)
        self.assertTrue(issubclass(factory, SearchGet))


# <audit>
#   <file>test_search_endpoint.py</file>
#   <requirements_applied>R1, R2, R3, R5, R6</requirements_applied>
#   <deviations>
#     plone.rest.Service has no __init__; Zope sets context/request after adapter
#     lookup.  Direct instantiation is done via __new__ + attribute injection in
#     _make_service(), mirroring exactly what the traversal layer does at runtime.
#     This is not a mock — the real service, context and request are used.
#
#     portal_type is set/deleted inside a try/finally to avoid leaking form state
#     into the shared layer request.
#
#     The plone:service ZCML directive wraps the factory in a new class inheriting
#     from (factory, BrowserView) before registering it.  The adapter is registered
#     providing zope.interface.Interface (not IService), so the lookup uses Interface
#     as the provided spec and issubclass() to verify the ancestry.
#   </deviations>
#   <questions>None</questions>
# </audit>
