# -*- coding: utf-8 -*-

from collective.geolocationbehavior.geolocation import IGeolocatable
from imio.smartweb.common.adapters import BaseCroppingProvider
from imio.smartweb.common.interfaces import IAddress
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.app.content.namechooser import NormalizingNameChooser
from plone.app.textfield import RichText
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform import directives
from plone.autoform.directives import read_permission
from plone.autoform.directives import write_permission
from plone.dexterity.content import Container
from plone.supermodel import model
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.container.interfaces import INameChooser
from zope.interface import implementer

# from collective.geolocationbehavior.geolocation import IGeolocatable
# from plone.supermodel.interfaces import FIELDSETS_KEY
# from plone.supermodel.model import Fieldset

# # Move geolocation field to our Address fieldset
# address_fieldset = Fieldset(
#     "address",
#     fields=["geolocation"],
# )
# IGeolocatable.setTaggedValue(FIELDSETS_KEY, [address_fieldset])


class EventCroppingProvider(BaseCroppingProvider):
    def get_scales(self, fieldname, request=None):
        if fieldname == "image":
            # scales used for lead image field
            return [
                "portrait_affiche",
                "paysage_affiche",
                "carre_affiche",
            ]
        return []


class IDETranslations(model.Schema):
    model.fieldset(
        "de_translations",
        label=_("German translations"),
        fields=["title_de", "description_de", "text_de"],
    )
    title_de = schema.TextLine(
        title=_("Title"),
        description=_(
            "This field is required if the content must be available in this language"
        ),
        required=False,
    )
    description_de = schema.Text(title=_("Description"), required=False)
    text_de = RichText(title=_("Text"), required=False)


class IENTranslations(model.Schema):
    model.fieldset(
        "en_translations",
        label=_("English translations"),
        fields=["title_en", "description_en", "text_en"],
    )
    title_en = schema.TextLine(
        title=_("Title"),
        description=_(
            "This field is required if the content must be available in this language"
        ),
        required=False,
    )
    description_en = schema.Text(title=_("Description"), required=False)
    text_en = RichText(title=_("Text"), required=False)


class INLTranslations(model.Schema):
    model.fieldset(
        "nl_translations",
        label=_("Dutch translations"),
        fields=["title_nl", "description_nl", "text_nl"],
    )
    title_nl = schema.TextLine(
        title=_("Title"),
        description=_(
            "This field is required if the content must be available in this language"
        ),
        required=False,
    )
    description_nl = schema.Text(title=_("Description"), required=False)
    text_nl = RichText(title=_("Text"), required=False)


class ITranslations(IENTranslations, IDETranslations, INLTranslations):
    """ """


class IEvent(IAddress, ITranslations):
    """Marker interface and Dexterity Python Schema for Event"""

    directives.order_before(event_type="IBasic.title")
    directives.widget(event_type=RadioFieldWidget)
    event_type = schema.Choice(
        title=_("Event type"),
        source="imio.events.vocabulary.EventTypes",
        default="event-driven",
        required=True,
    )

    online_participation = schema.URI(
        title=_("Online participation url"),
        description=_("Link to online participation"),
        required=False,
    )

    ticket_url = schema.URI(
        title=_("Ticket url"),
        description=_("Ticket url to subscribe to this event"),
        required=False,
    )

    video_url = schema.URI(
        title=_("Video url"),
        description=_("Video url from youtube, vimeo"),
        required=False,
    )

    facebook = schema.URI(
        title=_("Facebook"),
        description=_("Facebook url for this event"),
        required=False,
    )

    twitter = schema.URI(
        title=_("Twitter"),
        description=_("Twitter url for this event"),
        required=False,
    )

    instagram = schema.URI(
        title=_("Instagram"),
        description=_("Instagram url for this event"),
        required=False,
    )

    free_entry = schema.Bool(
        title=_("Free entry"),
        description=_("Check if entry is free"),
        required=False,
        default=False,
    )

    reduced_mobility_facilities = schema.Bool(
        title=_("Facilities for person with reduced mobility"),
        description=_("Check if there is facilities for person with reduced mobility"),
        required=False,
        default=False,
    )

    model.fieldset(
        "categorization",
        label=_("Categorization"),
        fields=["selected_agendas", "category", "local_category"],
    )
    directives.widget(selected_agendas=SelectFieldWidget)
    selected_agendas = schema.List(
        title=_("Selected agendas"),
        description=_(
            "Select agendas where this event will be displayed. Current agenda is always selected."
        ),
        value_type=schema.Choice(vocabulary="imio.events.vocabulary.AgendasUIDs"),
        default=[],
        required=False,
    )

    category = schema.Choice(
        title=_("Category"),
        description=_(
            "Important! These categories are used to supplement the information provided by the topics"
        ),
        source="imio.events.vocabulary.EventsCategories",
        required=False,
    )

    local_category = schema.Choice(
        title=_("Specific category"),
        description=_(
            "Important! These categories allow you to use criteria that are specific to your organization"
        ),
        source="imio.events.vocabulary.EventsLocalCategories",
        required=False,
    )

    read_permission(selected_agendas="imio.events.core.AddEntity")
    write_permission(selected_agendas="imio.events.core.AddEntity")


@implementer(IEvent)
class Event(Container):
    """Event class"""

    @property
    def is_geolocated(obj):
        coordinates = IGeolocatable(obj).geolocation
        if coordinates is None:
            return False
        return all([coordinates.latitude, coordinates.longitude])


@implementer(INameChooser)
class EventNameChooser(NormalizingNameChooser):
    def chooseName(self, name, obj):
        if IEvent.providedBy(obj):
            return obj.UID()
        return super(EventNameChooser, self).chooseName(name, obj)
