# -*- coding: utf-8 -*-

from imio.smartweb.common.browser.forms import CustomAddForm
from imio.smartweb.common.browser.forms import CustomEditForm
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.browser.add import DefaultAddView
from plone.z3cform import layout
from zope.interface import Invalid
from z3c.form import button
from z3c.form.interfaces import WidgetActionExecutionError


class BaseValidationForm:
    @button.buttonAndHandler(_("Apply"), name="apply")
    def handleApply(self, action):
        data, errors = self.extractData()
        end = data["IEventBasic.end"]
        start = data["IEventBasic.start"]
        days = (end - start).days
        # 3 years
        if days > 1095:
            self.status = self.formErrorsMessage
            msg = _("Your event must last less than 3 years.")
            raise WidgetActionExecutionError("IEventBasic.end", Invalid(msg))
        changes = self.applyChanges(data)
        if changes:
            self.status = self.successMessage
        else:
            self.status = self.noChangesMessage


class EventCustomEditForm(BaseValidationForm, CustomEditForm):
    """ """


EventCustomEditView = layout.wrap_form(EventCustomEditForm)


class EventCustomAddForm(BaseValidationForm, CustomAddForm):
    portal_type = "imio.events.Event"


class EventCustomAddView(DefaultAddView):
    form = EventCustomAddForm
