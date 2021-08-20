# -*- coding: utf-8 -*-

from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IAgenda(model.Schema):
    """Marker interface and Dexterity Python Schema for Agenda"""


@implementer(IAgenda)
class Agenda(Container):
    """Agenda class"""
