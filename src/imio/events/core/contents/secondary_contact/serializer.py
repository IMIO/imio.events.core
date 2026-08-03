# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.directory import CONTACT_ROW_COLUMNS
from imio.smartweb.common.contact.directory import row_key

PORTAL_TYPE = "imio.events.SecondaryContact"


def kept_rows(obj, kind):
    """Stored rows of `kind`, reduced to the columns the editor retained.

    Reads the STORED snapshot, not the live directory: an event has a
    temporality and must publish the contact as it was for that event. See
    ISecondaryContact.

    `visible_columns` semantics, which must not be collapsed:
      * None -> no preference recorded -> every column
      * []   -> explicitly hidden      -> row dropped

    `type` is emitted as the RAW token, read from `type_token`, never as the
    translated label: the consuming site translates it itself, the way @events
    already hands out `category`, `country` and `event_type`.
    """
    all_columns = CONTACT_ROW_COLUMNS[kind]
    rows = []
    for stored in getattr(obj, "{}_display".format(kind), None) or []:
        if not row_key(kind, stored):
            continue
        columns = stored.get("visible_columns")
        if columns is None:
            columns = all_columns
        else:
            # Intersect in canonical order: the stored order is the editor's
            # checkbox order and must not leak into the payload.
            columns = [column for column in all_columns if column in columns]
            if not columns:
                continue
        row = {}
        for column in columns:
            if column == "type":
                row["type"] = stored.get("type_token") or ""
            else:
                row[column] = stored.get(column) or ""
        rows.append(row)
    return rows


def serialize_secondary_contact(obj):
    """One Secondary contact as published, or None if it has no contact.

    `related_contact` is a required field, so a missing value can only be
    legacy data; the payload must never carry an entry with a null uid.
    """
    uid = getattr(obj, "related_contact", None)
    if not uid:
        return None
    return {
        "uid": uid,
        "title": obj.title or "",
        "phones": kept_rows(obj, "phones"),
        "mails": kept_rows(obj, "mails"),
        "urls": kept_rows(obj, "urls"),
    }


def get_secondary_contacts(event):
    """The event's Secondary contacts, in folder order (the editor's order).

    Always a list, so a consumer never has to tell "absent" from "empty".
    """
    result = []
    for child in event.listFolderContents(contentFilter={"portal_type": PORTAL_TYPE}):
        data = serialize_secondary_contact(child)
        if data is not None:
            result.append(data)
    return result
