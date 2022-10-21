# -*- coding: utf-8 -*-

from imio.events.core.contents import IEvent
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IEvent, Interface)
class SerializeEventToJson(SerializeFolderToJson):
    def __call__(self, version=None, include_items=True):
        result = super(SerializeEventToJson, self).__call__(version, include_items=True)
        return result
