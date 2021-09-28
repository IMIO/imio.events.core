# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Acquisition import aq_parent
from imio.events.core.contents import IAgenda


def get_agenda_for_event(event):
    obj = event
    while not IAgenda.providedBy(obj):
        parent = aq_parent(aq_inner(obj))
        obj = parent
    agenda = obj
    return agenda
