# -*- coding: utf-8 -*-
from plone.dexterity.browser.view import DefaultView
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.contenttypes.browser.folder import FolderView
from plone.app.event.browser.event_view import EventView
from plone.event.interfaces import IEventAccessor


class View(EventView, FolderView):

    GALLERY_IMAGES_NUMBER = 3

    def description(self):
        """Description with html carriage return"""
        description = self.context.description
        description = "<br/>".join(description.split("\r\n"))
        return description

    def files(self):
        return self.context.listFolderContents(contentFilter={"portal_type": "File"})

    def images(self):
        images = self.context.listFolderContents(contentFilter={"portal_type": "Image"})
        rows = []
        for i in range(0, len(images)):
            if i % self.GALLERY_IMAGES_NUMBER == 0:
                rows.append(images[i : i + self.GALLERY_IMAGES_NUMBER])  # NOQA
        return rows

    def has_leadimage(self):
        if ILeadImage.providedBy(self.context) and getattr(
            self.context, "image", False
        ):
            return True
        return False
