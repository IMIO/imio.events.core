from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.app.content.browser.actions import (
    DeleteConfirmationForm as BaseDeleteConfirmationForm,
)
from plone.app.content.browser.contents.delete import (
    DeleteActionView as BaseDeleteActionView,
)
from zope.i18n import translate


class DeleteConfirmationForm(BaseDeleteConfirmationForm):

    @property
    def items_to_delete(self):
        count = len(self.context.items())
        if count >= 1:
            txt = _(
                "Agenda ${val1} can't be removed because it contains ${val2} event(s)",
                mapping={"val1": self.context.Title(), "val2": count},
            )
            msg = translate(txt, context=self.request)
            api.portal.show_message(msg, self.request, type="warn")
            self.request.response.redirect(self.context.absolute_url())
            return 0
        return count


class DeleteActionView(BaseDeleteActionView):

    def action(self, obj):
        count = len(obj.items())
        if count >= 1:
            txt = _(
                "Agenda ${val1} can't be removed because it contains ${val2} event(s)",
                mapping={"val1": obj.Title(), "val2": count},
            )
            msg = translate(txt, context=self.request)
            self.errors.append(msg)
            return
        return super(DeleteActionView, self).action(obj)
