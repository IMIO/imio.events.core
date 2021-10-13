# -*- coding: utf-8 -*-

from imio.events.core.contents.event.content import IEvent
from imio.events.core.utils import get_agenda_for_event
from plone.indexer import indexer

import copy


@indexer(IEvent)
def category_and_topics_indexer(obj):
    values = []
    if obj.topics is not None:
        values = copy.deepcopy(obj.topics)

    if obj.category is not None:
        values.append(obj.category)

    if obj.local_category is not None:
        values.append(obj.local_category)

    return values


@indexer(IEvent)
def container_uid(obj):
    uid = get_agenda_for_event(obj).UID()
    return uid
