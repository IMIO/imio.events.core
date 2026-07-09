# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from zope.interface import Interface


# Read-only-ish datagrid rows mirroring the imio.directory.Contact JSON
# (phones / mails / urls). Each row carries a "selected" checkbox: the editor
# ticks the lines to keep for this event. The data columns are plain TextLine
# (not Email/URI) so heterogeneous directory data never fails validation, and
# no imio.directory vocabulary is imported (the "type" is shown as-is). The
# data cells are turned read-only in the browser (see the edit-form JS); only
# the checkbox is interactive.
class IContactPhoneRow(Interface):
    selected = schema.Bool(title=_("Keep"), required=False, default=False)
    label = schema.TextLine(title=_("Label"), required=False)
    type = schema.TextLine(title=_("Type"), required=False)
    number = schema.TextLine(title=_("Number"), required=False)


class IContactMailRow(Interface):
    selected = schema.Bool(title=_("Keep"), required=False, default=False)
    label = schema.TextLine(title=_("Label"), required=False)
    type = schema.TextLine(title=_("Type"), required=False)
    mail_address = schema.TextLine(title=_("E-mail"), required=False)


class IContactUrlRow(Interface):
    selected = schema.Bool(title=_("Keep"), required=False, default=False)
    type = schema.TextLine(title=_("Type"), required=False)
    url = schema.TextLine(title=_("URL"), required=False)


class IContact(model.Schema):
    """Marker interface and Dexterity Python Schema for Contact"""

    # Own optional title field instead of the plone.basic behavior: this keeps
    # the title optional (plone.basic makes it required) and avoids bringing in
    # the description field. plone.namefromtitle still derives the id from it
    # when set, and falls back gracefully when it is left empty.
    title = schema.TextLine(
        title=_("Title"),
        required=False,
    )

    directives.widget(
        "related_contact",
        SelectFieldWidget,
        vocabulary="imio.events.vocabulary.RemoteDirectoryContact",
    )
    related_contact = schema.Choice(
        title=_("Contact"),
        description=_(
            "You can retrieve information from a contact record that already exists in your directory"
        ),
        source="imio.events.vocabulary.RemoteDirectoryContact",
        required=True,
    )

    model.fieldset(
        "contact_informations",
        label=_("Contact informations"),
        fields=["phones", "mails", "urls"],
    )

    directives.widget("phones", DataGridFieldFactory, auto_append=False)
    phones = schema.List(
        title=_("Phones"),
        description=_(
            "Retrieved from the linked directory contact. Tick the lines to keep."
        ),
        value_type=DictRow(title="phone", schema=IContactPhoneRow),
        required=False,
    )

    directives.widget("mails", DataGridFieldFactory, auto_append=False)
    mails = schema.List(
        title=_("E-mails"),
        description=_(
            "Retrieved from the linked directory contact. Tick the lines to keep."
        ),
        value_type=DictRow(title="mail", schema=IContactMailRow),
        required=False,
    )

    directives.widget("urls", DataGridFieldFactory, auto_append=False)
    urls = schema.List(
        title=_("URLs"),
        description=_(
            "Retrieved from the linked directory contact. Tick the lines to keep."
        ),
        value_type=DictRow(title="url", schema=IContactUrlRow),
        required=False,
    )


@implementer(IContact)
class Contact(Item):
    """Contact class"""
