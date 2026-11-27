# -*- coding: utf-8 -*-


from imio.smartweb.common.interfaces import ILocalManagerAware
from imio.smartweb.locales import SmartwebMessageFactory as _
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone import schema
from plone.app.z3cform.widget import SelectFieldWidget
from plone.app.z3cform.widgets.select import AjaxSelectWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from urllib.parse import urlsplit
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid


def is_website_url(value):
    """An http(s) URL with a host, no credentials, query nor fragment: the base URL of a website."""
    parts = urlsplit(value)
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or any(char.isspace() for char in value)
    ):
        raise Invalid(
            _("Enter the address of a website, starting with https:// or http://")
        )
    return True


class ILocalCategoryRowSchema(Interface):

    fr = schema.TextLine(
        title=_("French"),
        required=True,
    )

    nl = schema.TextLine(
        title=_("Dutch"),
        required=False,
    )

    de = schema.TextLine(
        title=_("Deutsch"),
        required=False,
    )

    en = schema.TextLine(
        title=_("English"),
        required=False,
    )


class IEntity(model.Schema):
    """Marker interface and Dexterity Python Schema for Entity"""

    directives.widget(zip_codes=SelectFieldWidget)
    zip_codes = schema.List(
        title=_("Zip codes and cities"),
        description=_("Choose zip codes for this entity"),
        value_type=schema.Choice(vocabulary="imio.smartweb.vocabulary.Cities"),
    )

    model.fieldset("categorization", fields=["local_categories"])
    local_categories = schema.List(
        title=_("Specific events categories"),
        description=_(
            "List of events categories values available for this entity (one per line)"
        ),
        value_type=DictRow(title="Value", schema=ILocalCategoryRowSchema),
        required=False,
    )
    directives.widget(
        "local_categories", DataGridFieldFactory, allow_reorder=True, auto_append=False
    )

    directives.read_permission(
        authorize_to_bring_event_anywhere="imio.events.core.BringEventIntoPersonnalAgenda"
    )
    directives.write_permission(
        authorize_to_bring_event_anywhere="imio.events.core.BringEventIntoPersonnalAgenda"
    )
    authorize_to_bring_event_anywhere = schema.Bool(
        title=_("Authorize to bring event anywhere"),
        description=_(
            "If selected, contributor of this entity can bring event in any agenda independently of agenda subscribing feature"
        ),
        required=False,
        default=False,
    )

    directives.widget(
        "directory_linked_entities",
        AjaxSelectWidget,
        vocabulary="imio.smartweb.vocabulary.RemoteDirectoryEntities",
        pattern_options={"multiple": True},
    )
    directory_linked_entities = schema.List(
        title=_("Directory entities"),
        description=_(
            "Select entity/ies from which you want to link contacts on your events."
        ),
        value_type=schema.Choice(
            source="imio.smartweb.vocabulary.RemoteDirectoryEntities"
        ),
        required=False,
    )

    # Technical configuration, which only a Manager changes; everyone reads it (mcp-omnia, anonymously).
    directives.write_permission(smartweb_site_url="cmf.ManagePortal")
    smartweb_site_url = schema.TextLine(
        title=_("SmartWeb site URL"),
        description=_("URL of the public SmartWeb site of this entity."),
        required=False,
        constraint=is_website_url,
    )


@implementer(IEntity, ILocalManagerAware)
class Entity(Container):
    """Entity content type"""
