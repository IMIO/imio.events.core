# -*- coding: utf-8 -*-

from imio.smartweb.common.browser.forms import CustomAddForm
from imio.smartweb.common.browser.forms import CustomEditForm
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.events import EditFinishedEvent
from plone.dexterity.i18n import MessageFactory as DMF_
from plone.z3cform import layout
from Products.statusmessages.interfaces import IStatusMessage
from zope.interface import Invalid
from z3c.form import button
from z3c.form.interfaces import WidgetActionExecutionError
from zope.event import notify


class EventCustomEditForm(CustomEditForm):
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


class EventCustomAddForm(CustomAddForm):
    portal_type = "imio.events.Event"

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
