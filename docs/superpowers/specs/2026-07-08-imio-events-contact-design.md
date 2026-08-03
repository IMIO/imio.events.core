# Design — `imio.events.Contact` ("Secondary contact")

> **SUPERSEDED (2026-07-31)** by
> `2026-07-31-secondary-contact-shared-layer-design.md`. Kept for the record
> only — do not implement from this document. What changed: the type is named
> `imio.events.SecondaryContact`; the reusable machinery lives in
> `imio.smartweb.common` instead of being local; rows carry a `visible_columns`
> list instead of a `selected` boolean; the REST payload is a stored snapshot
> served through catalog metadata, not a live directory fetch at serialization
> time.

Date: 2026-07-08

## Goal

Add a new Dexterity content type `imio.events.Contact`, labelled **"Secondary
contact"**, that can be added **multiple times** inside an `imio.events.Event`.
Each `imio.events.Contact` holds a **single** reference to a contact from the
directory (a *simple* select, not a multi-select), plus a user-entered title.

Inspired by the Contact *section* of `imio.smartweb.core`
(`contents/sections/contact/`), but reduced to the "simple" field only: the
gallery / image / scaling display options of that section are intentionally
**left out**, and `imio.smartweb.core` is **not** added as a dependency.

## Non-goals

- No gallery/carousel layout options (`gallery_mode`, `nb_results_by_batch`,
  `nb_contact_by_line`).
- No image scale option (`image_scale`).
- No `visible_blocks` option.
- No dependency on `imio.smartweb.core`.

## Decisions (confirmed with user)

1. **Add permission**: reuse the existing `imio.events.core.AddEvent`
   permission (no new permission plumbing).
2. **Title**: the type has an **optional** `title` field defined directly on
   the `IContact` schema (NOT `plone.basic`, which would make the title
   required and also expose a description). `plone.namefromtitle` is kept so
   the id is derived from the title when set and falls back cleanly (via the
   existing `NormalizingNameChooser`) when it is empty. No description field.
   No custom NameChooser and no title-deriving subscriber.
3. **REST output**: expose a list of contact **UIDs** (same shape as the
   Event's existing `directory_linked_contact` / `event_sponsors` fields).
4. Contact is addable **inside `imio.events.Event`** (multiple allowed).
5. Reuse the **existing** `imio.events.vocabulary.RemoteDirectoryContact`
   vocabulary (the one already backing the Event's "Main contact").

## Components

### 1. Content type module — `contents/contact/`

Follows the one-folder-per-type convention already used by
`agenda/`, `entity/`, `event/`, `folder/`.

- `contents/contact/__init__.py`
- `contents/contact/content.py`:

  ```python
  # -*- coding: utf-8 -*-

  from imio.smartweb.locales import SmartwebMessageFactory as _
  from plone.app.z3cform.widget import SelectFieldWidget
  from plone.autoform import directives
  from plone.dexterity.content import Item
  from plone.supermodel import model
  from zope import schema
  from zope.interface import implementer


  class IContact(model.Schema):
      """Marker interface and Dexterity Python Schema for Contact"""

      # Optional title defined here instead of via plone.basic (which would
      # make it required and add a description field).
      title = schema.TextLine(
          title=_("Title"),
          required=False,
      )

      directives.widget(
          "related_contact",
          SelectFieldWidget,  # single-value select (not multiple)
          vocabulary="imio.events.vocabulary.RemoteDirectoryContact",
      )
      related_contact = schema.Choice(
          title=_("Contact"),
          description=_(
              "You can retrieve information from a contact record that "
              "already exists in your directory"
          ),
          source="imio.events.vocabulary.RemoteDirectoryContact",
          required=True,
      )


  @implementer(IContact)
  class Contact(Item):
      """Contact class"""
  ```

  - `Item` (not folderish): a Contact holds no sub-content.
  - `SelectFieldWidget` = single-value select, consistent with the Event's
    existing "Main contact" (`directory_linked_contact`).

- `contents/contact/configure.zcml`: minimal/empty `<configure/>` — no custom
  browser view; the default Dexterity view is used.

- Register in `contents/__init__.py`:
  `from .contact.content import IContact, Contact  # NOQA`

- Include in `contents/configure.zcml`: `<include package=".contact" />`

### 2. FTI — `profiles/default/types/imio.events.Contact.xml`

- `title` = `Secondary contact`, `i18n:domain="imio.smartweb"`.
- `description` = short description.
- `global_allow` = `False`; `filter_content_types` = `True`;
  `allowed_content_types` empty (leaf type).
- `add_permission` = `imio.events.core.AddEvent`.
- `klass` = `imio.events.core.contents.Contact`.
- `schema` = `imio.events.core.contents.IContact`.
- `behaviors` (minimal):
  - `plone.namefromtitle` (derives the id from the optional title)
  - `plone.excludefromnavigation`

  Note: `plone.basic` is intentionally **not** enabled — the optional `title`
  field is declared on `IContact` itself, and no description field is exposed.

### 3. Register the type — `profiles/default/types.xml`

Add:
```xml
<object meta_type="Dexterity FTI" name="imio.events.Contact"/>
```

### 4. Allow Contact inside Event — `profiles/default/types/imio.events.Event.xml`

Add to `allowed_content_types`:
```xml
<element value="imio.events.Contact" />
```
(keeping the existing `File` and `Image` entries).

### 5. REST exposure — `contents/event/serializer.py`

Extend `SerializeEventToJson.__call__` to add:

```python
result["secondary_contacts"] = [
    child.related_contact
    for child in self.context.listFolderContents(
        contentFilter={"portal_type": "imio.events.Contact"}
    )
    if child.related_contact
]
```

- Output is a list of directory-contact **UIDs** (the vocabulary value),
  consistent with how `directory_linked_contact` / `event_sponsors` are already
  serialized (plain UIDs).

### 6. Migration — profile upgrade

- Bump `profiles/default/metadata.xml` version `1026` → `1027`.
- Add `profiles/1026_to_1027/` (typeinfo reimport) and register an upgrade step
  in `upgrades/configure.zcml` (source `1026`, destination `1027`) that
  reimports type information so existing sites get:
  - the new `imio.events.Contact` FTI, and
  - the updated `allowed_content_types` on `imio.events.Event`.

### 7. Tests — `tests/test_contact.py`

Written using the `plone-testing` skill / existing `testing.py` layer. Cover:

- The `imio.events.Contact` FTI is installed.
- A Contact can be added inside an `imio.events.Event` (and multiple are
  allowed).
- A Contact is **not** addable where it shouldn't be (e.g. not `global_allow`).
- `related_contact` is a single-value `Choice` field bound to
  `imio.events.vocabulary.RemoteDirectoryContact`.
- `title` exists and is **optional**; no `description` field and no
  `plone.basic` behavior. A Contact is valid without a title.
- The Event REST serialization includes `secondary_contacts` as a list of the
  child Contacts' `related_contact` UIDs.

## i18n

New user-facing strings use the `imio.smartweb` domain via
`SmartwebMessageFactory`. English msgids are authored here; FR/NL/DE
translations live in `imio.smartweb.locales` and can be added there separately.

## Files touched (summary)

New:
- `contents/contact/__init__.py`
- `contents/contact/content.py`
- `contents/contact/configure.zcml`
- `profiles/default/types/imio.events.Contact.xml`
- `profiles/1026_to_1027/` (typeinfo)
- `tests/test_contact.py`

Modified:
- `contents/__init__.py`
- `contents/configure.zcml`
- `profiles/default/types.xml`
- `profiles/default/types/imio.events.Event.xml`
- `profiles/default/metadata.xml`
- `upgrades/configure.zcml` (+ possibly `upgrades/upgrades.py` if a handler is needed)
- `contents/event/serializer.py`

## Increment — retrieve the directory contact's phones / mails / urls

Goal: on `imio.events.Contact`, retrieve and selectively keep the linked
directory contact's phones, e-mails and urls, presented like the datagrids of
`imio.directory.core`'s Contact.

Decisions (confirmed with user):

- **Three read-only datagrids** `phones` / `mails` / `urls`, mirroring the
  `imio.directory.Contact` JSON columns. Row schemas are defined **locally**
  (`IContactPhoneRow` / `IContactMailRow` / `IContactUrlRow`) as plain
  `TextLine` columns — no `imio.directory` vocabulary imported. Each row adds a
  `selected` (Bool) **"Keep"** checkbox so the editor picks which lines to keep.
- **Server-side refresh** (not client-side JS row building): a custom edit form
  `ContactCustomEditForm` adds a **"Refresh contact informations from
  directory"** button. It saves the form, then `utils.refresh_contact_informations`
  fetches the linked contact (`get_directory_contact_lines`, reusing
  `DIRECTORY_URL` + `get_json` + `fullobjects=true`) and rewrites the datagrids,
  **preserving previously-ticked lines** (matched by value:
  number / mail_address / url). This was chosen over client-side JS because the
  datagridfield 3.0.4 widget is a minified bundle and building rows client-side
  is fragile and untestable.
- The data cells are made **read-only in the browser** by a small addition to
  the existing `directory_contact_autofill.js` (sets `readonly` on the data
  inputs, which still submit; the `selected` checkbox stays interactive). No new
  JS bundle — the existing member-scoped bundle already loads it.
- **REST**: `secondary_contacts` is a **list of objects**
  `{uid, title, phones, mails, urls}`, where each list contains only the ticked
  rows (with the internal `selected` flag stripped).

Files (increment):

- Modified `contents/contact/content.py` (row schemas + 3 datagrids)
- New `contents/contact/forms.py` (`ContactCustomEditForm` + refresh button)
- Modified `contents/contact/configure.zcml` (register the custom edit view)
- Modified `utils.py` (`get_directory_contact_lines`, `merge_directory_lines`,
  `refresh_contact_informations`)
- Modified `contents/event/serializer.py` (rich `secondary_contacts` shape)
- Modified `browser/static/directory_contact_autofill.js` (read-only cells)
- Extended `tests/test_contact.py`

Known limitation: the refresh button lives on the **edit** form only. Workflow:
create the Contact (pick `related_contact`, Save), then Edit → Refresh to pull
the lines and tick the ones to keep.
