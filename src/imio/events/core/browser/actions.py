from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.app.content.browser.actions import (
    DeleteConfirmationForm as BaseDeleteConfirmationForm,
)
from plone.app.content.browser.contents.delete import (
    DeleteActionView as BaseDeleteActionView,
)


class DeleteConfirmationForm(BaseDeleteConfirmationForm):

    @property
    def items_to_delete(self):
        count = super(
            DeleteConfirmationForm, self
        ).items_to_delete  # len(self.context.items())
        if count >= 1:
            msg = f"Agenda {self.context.Title()} can't be removed because it contains {count} event(s)"
            api.portal.show_message(_(msg), self.request, type="warn")
            self.request.response.redirect(self.context.absolute_url())
            return 0
        return count


class DeleteActionView(BaseDeleteActionView):

    def action(self, obj):
        count = len(obj.items())
        if count >= 1:
            msg = f"Agenda '{obj.title}' can't be removed because it contains {count} event(s)."
            self.errors.append(_(msg))
            return
        return super(DeleteActionView, self).action(obj)
