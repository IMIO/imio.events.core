# -*- coding: utf-8 -*-

from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IEvent(model.Schema):
    """Marker interface and Dexterity Python Schema for Event"""


@implementer(IEvent)
class Event(Container):
    """Event class"""
