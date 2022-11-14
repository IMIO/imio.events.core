# -*- coding: utf-8 -*-

from imio.events.core.contents import IEvent
from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.smartweb.common.rest.utils import get_restapi_query_lang
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from plone.restapi.serializer.summary import DefaultJSONSummarySerializer
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IEvent, IImioEventsCoreLayer)
class SerializeEventToJson(SerializeFolderToJson):
    def __call__(self, version=None, include_items=True):
        result = super(SerializeEventToJson, self).__call__(version, include_items=True)
        query = self.request.form
        lang = get_restapi_query_lang(query)
        title = result["title"]
        text = result["text"]
        desc = result["description"]

        if lang and lang != "fr":
            result["title"] = result[f"title_{lang}"]
            result["description"] = result[f"description_{lang}"]
            result["text"] = result[f"text_{lang}"]

        # maybe not necessary :
        result["title_fr"] = title
        result["description_fr"] = desc
        result["text_fr"] = text
        return result


@implementer(ISerializeToJsonSummary)
@adapter(Interface, IImioEventsCoreLayer)
class EventJSONSummarySerializer(DefaultJSONSummarySerializer):
    def __call__(self):
        summary = super(EventJSONSummarySerializer, self).__call__()

        query = self.request.form
        lang = get_restapi_query_lang(query)
        if lang == "fr":
            # nothing to go, fr is the default language
            return summary

        obj = IContentListingObject(self.context)
        for orig_field in ["title", "description"]:
            field = f"{orig_field}_{lang}"
            accessor = self.field_accessors.get(field, field)
            value = getattr(obj, accessor, None)
            try:
                if callable(value):
                    value = value()
            except WorkflowException:
                summary[orig_field] = None
                continue
            if orig_field == "description" and value is not None:
                value = value.replace("**", "")
            summary[orig_field] = json_compatible(value)

        return summary
