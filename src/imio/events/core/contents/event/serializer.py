# -*- coding: utf-8 -*-

from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEvent
from imio.events.core.contents import IFolder
from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.smartweb.common.rest.utils import get_restapi_query_lang
from plone import api
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from plone.restapi.serializer.summary import DefaultJSONSummarySerializer
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory


def get_container_uid(event_uid, summary=None):
    if summary is not None:
        container_uid = summary.get("UID") or summary.get("container_uid")
        if container_uid:
            return container_uid
    brain = api.content.find(UID=event_uid)[0]
    container_uid = getattr(brain, "container_uid", None)
    return container_uid


@implementer(ISerializeToJson)
@adapter(IEvent, IImioEventsCoreLayer)
class SerializeEventToJson(SerializeFolderToJson):
    def __call__(self, version=None, include_items=True):
        result = super(SerializeEventToJson, self).__call__(version, include_items=True)
        query = self.request.form
        lang = get_restapi_query_lang(query)
        result["first_start"] = json_compatible(self.context.start)
        result["first_end"] = json_compatible(self.context.end)
        title = result["title"]
        text = result["text"]
        desc = result["description"]

        if lang and lang != "fr":
            result["title"] = result[f"title_{lang}"]
            result["description"] = result[f"description_{lang}"]
            result["text"] = result[f"text_{lang}"]
            if self.context.local_category:
                factory = getUtility(
                    IVocabularyFactory, "imio.events.vocabulary.EventsLocalCategories"
                )
                vocabulary = factory(self.context, lang=lang)
                term = vocabulary.getTerm(self.context.local_category)
                result["local_category"] = {
                    "token": self.context.local_category,
                    "title": term.title,
                }

        # Getting agenda title/id to use it in rest views
        if query.get("metadata_fields") is not None and "container_uid" in query.get(
            "metadata_fields"
        ):
            agenda = None
            event_uid = self.context.UID()
            container_uid = get_container_uid(event_uid)
            if container_uid is not None:
                # Agendas can be private (admin to access them). That doesn't stop events to be bring.
                with api.env.adopt_user(username="admin"):
                    agenda = api.content.get(UID=container_uid)
                # To make a specific agenda css class in smartweb carousel common template
                result["usefull_container_id"] = agenda.id
                # To display agenda title in smartweb carousel common template
                result["usefull_container_title"] = agenda.title

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
        # To get agenda title and use it in carousel,...
        if query.get("metadata_fields") is not None and "container_uid" in query.get(
            "metadata_fields"
        ):
            agenda = None
            if IEvent.providedBy(self.context):
                event_uid = self.context.UID()
                container_uid = get_container_uid(event_uid)
            elif IAgenda.providedBy(self.context) or IFolder.providedBy(self.context):
                container_uid = get_container_uid(None, summary)
            elif IEvent.providedBy(self.context.getObject()):
                # context can be a brain
                event_uid = self.context.UID
                container_uid = get_container_uid(event_uid)
            else:
                container_uid = get_container_uid(None, summary)
            # Agendas can be private (admin to access them). That doesn't stop events to be bring.
            with api.env.adopt_user(username="admin"):
                agenda = api.content.get(UID=container_uid)
            if not agenda:
                return summary
            # To make a specific agenda css class in smartweb carousel common template
            summary["usefull_container_id"] = agenda.id
            # To display agenda title in smartweb carousel common template
            summary["usefull_container_title"] = agenda.title
        lang = get_restapi_query_lang(query)
        if lang == "fr":
            # nothing to go, fr is the default language
            return summary

        obj = IContentListingObject(self.context)
        for orig_field in ["title", "description", "category_title", "local_category"]:
            field = f"{orig_field}_{lang}"
            accessor = self.field_accessors.get(field, field)
            value = getattr(obj, accessor, None) or None
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
