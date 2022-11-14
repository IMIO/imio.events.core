# -*- coding: utf-8 -*-

from imio.events.core.utils import reload_faceted_config
from imio.smartweb.common.upgrades import upgrades
from plone import api
from zope.globalrequest import getRequest

import logging

logger = logging.getLogger("imio.events.core")


def refresh_objects_faceted(context):
    request = getRequest()
    brains = api.content.find(portal_type=["imio.events.Entity", "imio.events.Agenda"])
    for brain in brains:
        obj = brain.getObject()
        reload_faceted_config(obj, request)
        logger.info("Faceted refreshed on {}".format(obj.Title()))


def add_event_dates_index(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.addIndex("event_dates", "KeywordIndex")
    catalog.manage_reindexIndex(ids=["event_dates"])
    logger.info("Added and indexed event_dates KeywordIndex")


def reindex_searchable_text(context):
    upgrades.reindex_searchable_text(context)


def add_translations_indexes(context):
    new_indexes = ["translated_in_nl", "translated_in_de", "translated_in_en"]
    catalog = api.portal.get_tool("portal_catalog")
    indexes = catalog.indexes()
    indexables = []
    for new_index in new_indexes:
        if new_index in indexes:
            continue
        catalog.addIndex(new_index, "BooleanIndex")
        indexables.append(new_index)
        logger.info(f"Added BooleanIndex for field {new_index}")
    if len(indexables) > 0:
        logger.info(f"Indexing new indexes {', '.join(indexables)}")
        catalog.manage_reindexIndex(ids=indexables)
