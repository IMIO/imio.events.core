# -*- coding: utf-8 -*-

from eea.facetednavigation.settings.interfaces import IHidePloneLeftColumn
from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEntity
from imio.smartweb.common.faceted.utils import configure_faceted
from plone import api
from Products.CMFPlone.utils import parent
from zope.component import getMultiAdapter
from zope.interface import noLongerProvides

import logging
import os

logger = logging.getLogger("imio.events.core")


def get_entity_for_obj(obj):
    logger.info(f"Getting entity for obj : {obj.absolute_url()}")
    while not IEntity.providedBy(obj):
        obj = parent(obj)
        if obj is None:
            logger.error("Infinite looping in while statement !", stack_info=True)
            raise Exception
    entity = obj
    return entity


def get_agenda_for_event(event):
    logger.info(f"Getting agenda for event : {event.absolute_url()}")
    obj = event
    while not IAgenda.providedBy(obj):
        obj = parent(obj)
        if obj is None:
            logger.error("Infinite looping in while statement !", stack_info=True)
            raise Exception
    agenda = obj
    return agenda


def get_agendas_uids_for_faceted(obj):
    if IAgenda.providedBy(obj):
        return [obj.UID()]
    elif IEntity.providedBy(obj):
        brains = api.content.find(context=obj, portal_type="imio.events.Agenda")
        return [b.UID for b in brains]
    else:
        raise NotImplementedError


def reload_faceted_config(obj, request):
    faceted_config_path = "{}/faceted/config/events.xml".format(
        os.path.dirname(__file__)
    )
    configure_faceted(obj, faceted_config_path)
    agendas_uids = "\n".join(get_agendas_uids_for_faceted(obj))
    request.form = {
        "cid": "agenda",
        "faceted.agenda.default": agendas_uids,
    }
    handler = getMultiAdapter((obj, request), name="faceted_update_criterion")
    handler.edit(**request.form)
    if IHidePloneLeftColumn.providedBy(obj):
        noLongerProvides(obj, IHidePloneLeftColumn)
