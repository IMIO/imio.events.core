# -*- coding: utf-8 -*-
from imio.events.core.contents import IEvent
from imio.events.core.subscribers import send_to_odwb
from imio.events.core.utils import reload_faceted_config
from imio.smartweb.common.upgrades import upgrades
from plone import api
from zope.globalrequest import getRequest

import logging
import pytz
import transaction

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
    catalog = api.portal.get_tool("portal_catalog")

    new_indexes = ["translated_in_nl", "translated_in_de", "translated_in_en"]
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

    new_metadatas = ["title_fr", "title_nl", "title_de", "title_en"]
    metadatas = list(catalog.schema())
    must_reindex = False
    for new_metadata in new_metadatas:
        if new_metadata in metadatas:
            continue
        catalog.addColumn(new_metadata)
        must_reindex = True
        logger.info(f"Added {new_metadata} metadata")
    if must_reindex:
        logger.info("Reindexing catalog for new metadatas")
        catalog.clearFindAndRebuild()


def reindex_catalog(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.clearFindAndRebuild()


def remove_searchabletext_fr(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.manage_delIndex("SearchableText_fr")


def remove_title_description_fr(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.delColumn("title_fr")
    catalog.delColumn("description_fr")


def reindex_event_dates_index(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.manage_reindexIndex(ids=["event_dates"])
    logger.info("Reindexed event_dates index")


def add_dates_indexes(context):
    catalog = api.portal.get_tool("portal_catalog")

    new_indexes = ["first_start", "first_end"]
    indexes = catalog.indexes()
    indexables = []
    for new_index in new_indexes:
        if new_index in indexes:
            continue
        catalog.addIndex(new_index, "FieldIndex")
        indexables.append(new_index)
        logger.info(f"Added FieldIndex for field {new_index}")
    if len(indexables) > 0:
        logger.info(f"Indexing new indexes {', '.join(indexables)}")
        catalog.manage_reindexIndex(ids=indexables)

    new_metadatas = ["first_start", "first_end"]
    metadatas = list(catalog.schema())
    must_reindex = False
    for new_metadata in new_metadatas:
        if new_metadata in metadatas:
            continue
        catalog.addColumn(new_metadata)
        must_reindex = True
        logger.info(f"Added {new_metadata} metadata")
    if must_reindex:
        logger.info("Reindexing catalog for new metadatas")
        catalog.clearFindAndRebuild()


def migrate_local_categories(context):
    brains = api.content.find(portal_type=["imio.events.Entity"])
    for brain in brains:
        obj = brain.getObject()
        if obj.local_categories:
            categories = obj.local_categories.splitlines()
            datagrid_categories = [
                {"fr": cat, "nl": "", "de": "", "en": ""} for cat in categories
            ]
            obj.local_categories = datagrid_categories
            logger.info(
                "Categories migrated to Datagrid for entity {}".format(obj.Title())
            )


def unpublish_events_in_private_agendas(context):
    brains = api.content.find(
        portal_type=["imio.events.Agenda"], review_state="private"
    )
    for brain in brains:
        evt_brains = api.content.find(
            context=brain.getObject(),
            portal_type=["imio.events.Event"],
            review_state="published",
        )
        for evt_brain in evt_brains:
            event = evt_brain.getObject()
            api.content.transition(event, "retract")
            logger.info("Event {} go to private status".format(event.absolute_url()))


def reindex_agendas_and_folders(context):
    brains = api.content.find(portal_type=["imio.events.Agenda", "imio.events.Folder"])
    for brain in brains:
        brain.getObject().reindexObject()


def migrate_events_to_brussels_timezone(context):
    _brussels = pytz.timezone("Europe/Brussels")
    brains = api.content.find(object_provides=IEvent.__identifier__)
    count = 0
    batch_size = 100
    for brain in brains:
        event = brain.getObject()
        if getattr(event, "timezone", None) not in ("UTC", "Etc/UTC", None):
            continue
        if event.start is None or event.end is None:
            continue
        if event.start.year < 100 or event.end.year < 100:
            logger.warning(f"Skipping event with sentinel date: {brain.getPath()}")
            continue
        try:
            # pytz.timezone.localize() attaches a timezone to a naive datetime
            event.start = _brussels.localize(event.start.replace(tzinfo=None))
            event.end = _brussels.localize(event.end.replace(tzinfo=None))
            event.reindexObject(
                idxs=["start", "end", "first_start", "first_end", "event_dates"]
            )
            count += 1
        except Exception:
            logger.exception(f"Failed to migrate event {brain.getPath()}, skipping")
            continue
        if count % batch_size == 0:
            transaction.commit()
            logger.info(f"Committed batch, {count} events migrated so far")
    logger.info(f"Migrated {count} events to Europe/Brussels timezone")
    site = api.portal.get()
    # Update all published events in ODWB after final commit
    transaction.get().addAfterCommitHook(send_to_odwb, kws={"obj": site})


def migrate_members_timezone_to_brussels(context):
    """Reset member timezone preferences that are set to UTC.

    User timezone preferences override the portal timezone (plone.app.event
    checks member.getProperty("timezone") first). Members with UTC set will
    keep creating events in UTC even after the portal timezone switch.
    """
    membership = api.portal.get_tool("portal_membership")
    members = membership.listMembers()
    count = 0
    utc_zones = {"UTC", "Etc/UTC"}
    for member in members:
        tz = member.getProperty("timezone", None)
        if tz in utc_zones or tz is None or tz == "":
            member.setMemberProperties({"timezone": "Europe/Brussels"})
            count += 1
            logger.info(
                f"Reset timezone for member {member.getId()}: UTC → Europe/Brussels"
            )
    logger.info(f"Updated timezone for {count} members")
