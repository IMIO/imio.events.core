# -*- coding: utf-8 -*-
from imio.events.core.ia.browser.categorization_button_edit import IACategorizeEditForm
from imio.events.core.ia.browser.categorization_button_add import IACategorizeAddForm

# from imio.smartweb.common.browser.forms import CustomAddForm
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.events import EditFinishedEvent
from plone.dexterity.i18n import MessageFactory as DMF_
from plone.z3cform import layout
from Products.statusmessages.interfaces import IStatusMessage
from zope.interface import Invalid
from z3c.form import button
from z3c.form.field import Fields
from z3c.form.group import Group
from z3c.form.interfaces import WidgetActionExecutionError
from zope.event import notify

GEO_FIELD_KEY = "IGeolocatable.geolocation"


TRANSLATION_GROUPS = {"de_translations", "nl_translations", "en_translations"}


def _update_event_form_fields(form):
    groups = list(form.groups)

    for group in groups:
        if group.__name__ == "address":
            group.label = _("Event location")
            break

    if GEO_FIELD_KEY in form.fields:
        geo_field = form.fields[GEO_FIELD_KEY]
        form.fields = form.fields.omit(GEO_FIELD_KEY)

        geo_group = Group(form.context, form.request, form)
        geo_group.__name__ = "geolocation"
        geo_group.label = ""
        geo_group.fields = Fields(geo_field)

        address_pos = next(
            (i for i, g in enumerate(groups) if g.__name__ == "address"), None
        )
        if address_pos is not None:
            groups.insert(address_pos + 1, geo_group)
        else:
            groups.append(geo_group)

    # Move translation groups to the end
    non_translation = [g for g in groups if g.__name__ not in TRANSLATION_GROUPS]
    translation = [g for g in groups if g.__name__ in TRANSLATION_GROUPS]
    form.groups = tuple(non_translation + translation)


class EventCustomEditForm(IACategorizeEditForm):
    def updateFields(self):
        super().updateFields()
        _update_event_form_fields(self)

    @button.buttonAndHandler(DMF_("Save"), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        end = data["IEventBasic.end"]
        start = data["IEventBasic.start"]
        days = (end - start).days
        # 3 years
        if days > 1095:
            self.status = self.formErrorsMessage
            msg = _("Your event must last less than 3 years.")
            raise WidgetActionExecutionError("IEventBasic.end", Invalid(msg))
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(self.success_message, "info")
        self.request.response.redirect(self.nextURL())
        notify(EditFinishedEvent(self.context))


EventCustomEditView = layout.wrap_form(EventCustomEditForm)


class EventCustomAddForm(IACategorizeAddForm):
    portal_type = "imio.events.Event"

    def updateFields(self):
        super().updateFields()
        _update_event_form_fields(self)

    @button.buttonAndHandler(DMF_("Save"), name="save")
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        end = data["IEventBasic.end"]
        start = data["IEventBasic.start"]
        days = (end - start).days
        # 3 years
        if days > 1095:
            self.status = self.formErrorsMessage
            msg = _("Your event must last less than 3 years.")
            raise WidgetActionExecutionError("IEventBasic.end", Invalid(msg))
        obj = self.createAndAdd(data)
        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            IStatusMessage(self.request).addStatusMessage(self.success_message, "info")


class EventCustomAddView(DefaultAddView):
    form = EventCustomAddForm
