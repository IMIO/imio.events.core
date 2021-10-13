# -*- coding: utf-8 -*-

from imio.events.core.contents import IAgenda
from Products.CMFPlone.utils import parent


def get_agenda_for_event(event):
    obj = event
    while not IAgenda.providedBy(obj):
        obj = parent(obj)
    agenda = obj
    return agenda
