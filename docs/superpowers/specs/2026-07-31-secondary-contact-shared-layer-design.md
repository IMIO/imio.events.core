# Design — `imio.events.SecondaryContact` and the shared contact layer in `imio.smartweb.common`

Date: 2026-07-31
Ticket: WEBBDC-2835
Supersedes: `2026-07-08-imio-events-contact-design.md`

## Goal

Add a Dexterity content type `imio.events.SecondaryContact`, labelled **"Secondary
contact"**, addable multiple times inside an `imio.events.Event`. Each object
references **one** contact of the remote directory and keeps a curated snapshot of
that contact's phones / e-mails / URLs. The result is exposed to downstream
Smartweb sites through the `@events` REST endpoint.

The Contact *section* of `imio.smartweb.core` (`contents/sections/contact/`)
already implements the same "load directory rows into read-only datagrids" idea.
Rather than copy it, the reusable part moves into `imio.smartweb.common`, which
both products already depend on. The section keeps the name **"Section
contact"** in `imio.smartweb.core`; the new type is **"Secondary contact"** in
`imio.events.core`. Those two names never converge.

## Scope

Three repositories, one ticket:

- `imio.smartweb.common` — receives the shared layer (branch `WEBBDC-2835`, an
  empty landing zone: its only contact-related commit, `6ff64ab`, is the earlier
  move of `imio.smartweb.vocabulary.ContactBlocks`, released in 1.2.57).
- `imio.smartweb.core` — its copies are deleted and replaced by imports from
  common. Its behaviour must not change. Branch `WEBBDC-2835`, commit `013b23d7`
  ("Add read-only phones/mails/urls datagrids to the contact section") is **not
  yet released**, so no site-facing migration is needed for this move.
- `imio.events.core` — the new type, on top of the shared layer. Branch
  `WEBBDC-2835`.

## Decisions

1. **One contact per object** (`related_contact`, `schema.Choice` +
   `SelectFieldWidget`). The type is already addable N times inside an Event, so
   a second multiplicity mechanism would make "3 contacts" representable three
   different ways with nothing designating a canonical one. The optional `title`
   ("Réservations", "Presse") only makes sense for a single contact, and this
   mirrors the Event's existing `directory_linked_contact` ("Main contact").
   The multi-valued `event_sponsors` stays the only list-shaped contact field.
2. **Stored snapshot, not a live fetch.** An event has a temporality; what must
   be published is the contact **as it was for that event**. The serializer
   reads the stored datagrid rows. This is a semantic choice, not merely a
   performance one — though it also keeps HTTP calls out of a heavily shared,
   RAM-cached endpoint. Consequence: in `imio.events.core` the stored data
   columns **are** the data. This is the deliberate inverse of
   `imio.smartweb.core`, where they are residue and the page render always
   re-reads the live directory payload.
3. **REST only, no Plone-side rendering.** `SecondaryContact` keeps the default
   Dexterity view. Display is the consuming Smartweb site's business. Nothing
   from the section's render path (`view.pt`, `macros.pt`, `ContactProperties`,
   `HashableJsonSectionView`) enters `imio.events.core`.
4. **`type` is exposed as a raw token, not a translated label.** See "The
   `type_token` column" below.
5. **Add permission**: the existing `imio.events.core.AddEvent`. No new
   permission, no rolemap change.
6. **Vocabulary**: the existing `imio.events.vocabulary.RemoteDirectoryContact`,
   already backing the Event's "Main contact" and `event_sponsors`. It is scoped
   to the parent Entity's `directory_linked_entities`.

## Non-goals

- No gallery / carousel / image-scale / `visible_blocks` options: those belong
  to the section's layout, which is not shared.
- No dependency of `imio.events.core` on `imio.smartweb.core`.
- No change to the section's stored data shape (beyond one extra hidden column)
  and no change to any vocabulary name, so no data migration in Smartweb sites.

---

## Part 1 — The shared layer in `imio.smartweb.common`

The dividing line: **common** owns the shape of a directory contact row and the
machinery to load it; **each product** owns where the object lives, how the
contact is picked, and how it is published.

### New subpackage `src/imio/smartweb/common/contact/`

| Module | Contents |
|---|---|
| `rows.py` | `IPhoneDisplayRow`, `IMailDisplayRow`, `IUrlDisplayRow`; `IContactInformationsGrids` |
| `directory.py` | `CONTACT_TYPE_LABELS`, `CONTACT_ROW_KEYS`, `CONTACT_ROW_COLUMNS`, `translated_type_label()`, `row_key()`, `build_display_rows()`, `get_remote_contacts()`, `visible_columns_map()`, `displayed_rows()` |
| `forms.py` | `ContactInformationsGridMixin`, `DISPLAY_FIELDS`, `KIND_BY_FIELD` |

`visible_columns_map()` and `displayed_rows()` become **free functions** taking
the context / payload explicitly, instead of methods on
`ContactProperties`: `imio.events.core` needs them in a serializer, not in a
render object. `ContactProperties` in `imio.smartweb.core` re-exposes them as
thin methods so its templates keep working unchanged.

`get_remote_contacts()` and `build_display_rows()` move verbatim except for
their imports, which switch from `imio.smartweb.core.config` /
`imio.smartweb.core.utils` to `imio.smartweb.common.config` /
`imio.smartweb.common.utils`. `DIRECTORY_URL` is the same expression in both
(`os.environ.get("DIRECTORY_URL", "https://annuaire.enwallonie.be")`). `get_json`
must be diffed between the two packages before the swap (see "Assumptions").

### `IContactInformationsGrids` — a schema mixin

A `model.Schema` interface carrying the three datagrid fields
(`phones_display`, `mails_display`, `urls_display`), their
`DataGridFieldFactory` directives (`allow_insert`, `allow_delete`,
`allow_reorder`, `auto_append` all `False`) and the
`model.fieldset("contact_informations", …)`. Both products inherit it:

- `ISectionContact(ISection, IContactInformationsGrids)`
- `ISecondaryContact(IContactInformationsGrids)`

This avoids duplicating ~60 lines of field declaration. The existing field
description msgids are kept **verbatim** (including their plural wording, "the
related contacts") so translations already authored in `imio.smartweb.locales`
stay valid.

The rows keep `contact_uid` and `contact_title` in both products. On the
mono-contact side both are strictly redundant — every row belongs to the same
contact — but `contact_uid` remains half of the `(contact_uid, row_key)`
preference key, and keeping `contact_title` lets the row schemas stay literally
identical. `contact_title` is left visible in the `imio.events.core` form:
suppressing one column of a `DataGridFieldFactory` per product is not worth the
machinery, and an extra column showing the contact's own name is harmless.
Neither is emitted in the REST payload.

### The `type_token` column

`build_display_rows()` writes the **already-translated** label into the `type`
column. In `imio.smartweb.core` that is harmless: the value is residue, and the
render re-translates the raw token from the live payload. In
`imio.events.core`, where the stored value **is** the data, it would freeze the
editor's language — an NL site would receive "Téléphone de travail".

Fix: the three row schemas gain a hidden `type_token` column (like
`contact_uid`) holding the raw token. The visible `type` column stays the
translated label, which is what the editor wants to read. The
`imio.events.core` serializer emits the **token**, and the consuming site
translates it through the shared `imio.smartweb` domain — consistent with how
`@events` already emits `category`, `country`, `event_type` as tokens. On the
`imio.smartweb.core` side this is one more residue column: no effect.

### Two adaptations of `ContactInformationsGridMixin`

1. `_hide_hide_title()` **leaves common**. It walks `self.groups` for the
   `layout` fieldset and forces the section's `hide_title` field, which does not
   exist on `SecondaryContact`. It moves down into an
   `imio.smartweb.core`-specific subclass.
2. The field holding the UIDs becomes a class attribute
   `contact_uids_field` (`"related_contacts"` for the section,
   `"related_contact"` for the new type). `_submitted_contact_uids()` keeps
   accepting both submission shapes: a string joined by
   `TranslatedAjaxSelectWidget.separator` (multi-valued ajax select) or a plain
   single value (`SelectFieldWidget`).

### Two moves into common

- `common/widgets/frozen_label.py`, moved from
  `core/widgets/frozen_label.py`. This is the hard blocker: `imio.events.core`
  cannot import it without depending on `imio.smartweb.core`.
- `ContactDisplayColumnsVocabularyFactory` and its three subclasses into
  `common/vocabularies.py`, registered in `common/vocabularies.zcml` under the
  **same** names `imio.smartweb.vocabulary.PhoneDisplayColumns`,
  `…MailDisplayColumns`, `…UrlDisplayColumns`. `imio.smartweb.core` must drop
  its own registrations, otherwise the two compete for the same utility name.
  Unchanged names mean zero impact on stored data.

### What stays in `imio.smartweb.core`

Everything about layout and rendering, which has no meaning in
`imio.events.core`: `ISection` / `Section`, `can_toggle_title_visibility`,
`hide_title`, `visible_blocks`, `gallery_mode`, `nb_results_by_batch`,
`nb_contact_by_line`, `image_scale`, `view.pt`, `macros.pt`, `ContactView` /
`HashableJsonSectionView`, the `ContactProperties` class (logo, leadimage,
images, geojson, itinerary, formatted address), and the `related_contacts` field
with its `imio.smartweb.vocabulary.RemoteContacts` vocabulary.

### What stays in `imio.events.core`

The FTI, the `related_contact` field on
`imio.events.vocabulary.RemoteDirectoryContact` (the irreducible divergence:
that vocabulary is scoped to the parent Entity's `directory_linked_entities`,
while the section's is global), containment inside `imio.events.Event`, and the
whole REST exposure.

---

## Part 2 — `imio.events.core`

### 1. Content type — `contents/secondary_contact/`

`content.py`:

```python
class ISecondaryContact(IContactInformationsGrids):
    title = schema.TextLine(title=_("Title"), required=False)

    directives.widget(
        "related_contact",
        SelectFieldWidget,
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


@implementer(ISecondaryContact)
class SecondaryContact(Item):
    """SecondaryContact class"""
```

`Item`, not `Container`: a SecondaryContact holds no sub-content. `title` is
declared on the schema and optional — `plone.basic` is deliberately not enabled,
as it would make the title required and add a description field. With an empty
title, Plone's `NormalizingNameChooser` derives an id from the portal type.

Registered in `contents/__init__.py`
(`from .secondary_contact.content import ISecondaryContact, SecondaryContact`)
and included from `contents/configure.zcml`. The current WIP
`contents/__init__.py` line re-imports `IFolder, Folder` from the new module and
must be fixed.

### 2. Forms — `contents/secondary_contact/forms.py`

An add form and an edit form, both carrying the **"Load contact information"**
button, built on the shared mixin:

```python
class SecondaryContactGridMixin(ContactInformationsGridMixin):
    contact_uids_field = "related_contact"
```

then the two concrete forms, each copying `buttons` **and** `handlers` before
the `@buttonAndHandler` decorator runs (the reason is documented in the
section's forms and the comment is carried over: without the copies the
decorator's `setdefault` creates fresh empty managers that shadow the base ones,
silently losing Save/Cancel and their handlers). No `_hide_hide_title` here.
Standard Dexterity add/edit forms, no Section styling.

`configure.zcml` registers, on the `IImioEventsCoreLayer` layer: the
`++add++imio.events.SecondaryContact` adapter (with the `cmf.AddPortalContent`
`<class>` requirement) and the `edit` page (`cmf.ModifyPortalContent`). **No**
`view` page — the default Dexterity view is used.

Editor workflow: add a SecondaryContact, pick the contact, press "Load contact
information" to fill the grids, tick the columns to keep, Save. Pressing Load
again rebuilds the grids from the currently selected contact while preserving
recorded preferences, keyed by `(contact_uid, row_key)`.

### 3. FTI — `profiles/default/types/imio.events.SecondaryContact.xml`

The WIP file must be corrected: `klass` and `schema` still point at
`Event` / `IEvent`, and `allowed_content_types` is missing.

Target:

- `title` = `Secondary contact`, `description` = short sentence,
  `i18n:domain="imio.smartweb"`.
- `icon_expr` = `string:person-plus`.
- `global_allow` = `False`, `filter_content_types` = `True`,
  `allowed_content_types` empty (leaf type).
- `add_permission` = `imio.events.core.AddEvent`.
- `klass` = `imio.events.core.contents.SecondaryContact`.
- `schema` = `imio.events.core.contents.ISecondaryContact`.
- behaviors: `plone.namefromtitle`, `plone.shortname`, `plone.locking`,
  `plone.excludefromnavigation`.

Then: register `imio.events.SecondaryContact` in `profiles/default/types.xml`,
and add it to `allowed_content_types` in
`profiles/default/types/imio.events.Event.xml` alongside `File` and `Image`
(already done in the WIP diff).

### 4. REST exposure — two paths, not one

`rest/endpoint.py::_perform_search` serializes **full objects only when the
query carries a `UID`**. In the ordinary case — a site listing events — items
are summaries built from catalog metadata, and the endpoint injects
`metadata_fields += ["container_uid", "recurrence", …, "event_sponsors"]`.
Adding a key to `SerializeEventToJson` alone would therefore only surface it on
single-event queries. Both paths are needed:

| Path | Mechanism |
|---|---|
| Ordinary `@events` query (summaries) | A `secondary_contacts` **indexer** on `IEvent`, a catalog **metadata column**, and `"secondary_contacts"` appended to the `metadata_fields` injected by `rest/endpoint.py` |
| Query with `UID` / `fullobjects` | `SerializeEventToJson.__call__` sets `result["secondary_contacts"]` |

Both call the same serialization function, so there is exactly one output
shape:

```json
"secondary_contacts": [
  {"uid": "a1b2c3…",
   "title": "Réservations",
   "phones": [{"label": "Accueil", "type": "work", "number": "081 12 34 56"}],
   "mails":  [{"mail_address": "resa@ville.be"}],
   "urls":   []}
]
```

Rules:

- Order = the order of the child objects inside the Event, which the editor
  controls.
- A row whose `visible_columns` is an **empty list** is omitted: "explicitly
  hidden".
- A row whose `visible_columns` is **`None`** is emitted in full: "no preference
  recorded". The None-vs-empty distinction defined in common is preserved
  end-to-end and must never be normalised into one case.
- Each emitted row carries only its retained columns, so a phone kept for its
  number alone is `{"number": "…"}`.
- `type` is emitted as the raw token, read from the hidden `type_token` column.
- Unlike `event_sponsors`, no remote resolution happens in
  `expand_occurences()`: the snapshot is already complete. That is the point of
  decision 2.
- An Event with no SecondaryContact child emits `"secondary_contacts": []`. The
  key is always present, so consumers never have to distinguish "absent" from
  "empty".
- A child whose `related_contact` is unset is skipped entirely. The field is
  required, so this can only arise from data predating a schema change, but the
  serializer must not emit an entry with a null `uid`.

### 5. Metadata freshness

The metadata lives on the Event; the data lives in its children. A **subscriber**
must reindex the parent Event's `secondary_contacts` when a `ISecondaryContact`
is added, modified or removed. `subscribers.py` already hosts handlers of this
kind (Agenda deletion cleaning up Event references, Event creation fixing
`selected_agendas`).

### 6. Migration — profile 1026 → 1027

- Bump `profiles/default/metadata.xml` from `1026` to `1027`.
- New `profiles/1026_to_1027/` containing `types.xml`, the two type files
  (`imio.events.SecondaryContact.xml` and the updated
  `imio.events.Event.xml`) and `catalog.xml` (the new column).
- Register the upgrade in `upgrades/configure.zcml` following the 1025→1026
  pattern exactly: a `registerProfile` + an `upgradeSteps` block with an
  `upgradeDepends` importing the profile, then an `upgradeStep` handler
  `add_secondary_contacts_metadata` modelled on `add_event_sponsors_metadata`
  (add the column if absent, then reindex).

---

## Part 3 — `imio.smartweb.core` adaptation

| File | Change |
|---|---|
| `widgets/frozen_label.py` | deleted (moved to common) |
| `vocabularies.py`, `vocabularies.zcml` | the three `*DisplayColumns` factories and their registrations removed |
| `contents/sections/contact/content.py` | the three row schemas and the three grid declarations removed; `ISectionContact(ISection, IContactInformationsGrids)`; the `frozen_label` import disappears with the rows |
| `contents/sections/contact/utils.py` | constants and functions imported from common; `ContactProperties` keeps its own methods and delegates `translated_type`, `visible_columns_map`, `displayed_rows` |
| `contents/sections/contact/forms.py` | `SectionContactGridMixin(ContactInformationsGridMixin)` with `contact_uids_field = "related_contacts"` and `_hide_hide_title()` |
| `setup.py`, `CHANGES.rst` | minimum version on `imio.smartweb.common` |

No behaviour change is intended: templates untouched, vocabulary names
untouched, stored shape untouched apart from the extra hidden `type_token`
column, which is residue on this side.

`imio.events.core/setup.py` likewise gains a minimum version on
`imio.smartweb.common`. Both packages currently declare it unpinned.

---

## Tests

- **`imio.smartweb.common`** — new: the None-vs-empty semantics of
  `build_display_rows()`, `row_key()`, `translated_type_label()` (including the
  unknown-token degradation to the raw token), `get_remote_contacts()` (order
  preserved, directory failure → `[]`), and the mixin helpers
  (`_submitted_contact_uids()` on both submission shapes,
  `_extract_preferences()`, `_write_grid()` and its `.count` marker). Those
  helpers only touch `self.request.form` and `self.prefix`, so they are tested
  against a small stub — no test content type is needed in common.
  `test_frozen_label.py` moves over from core unchanged.
- **`imio.smartweb.core`** — `test_section_contact.py` and
  `test_section_contact_forms.py` stay and must pass **without modification**.
  They are the regression net proving the extraction is behaviour-preserving,
  and they are the primary verification for Part 3.
- **`imio.events.core`** — new `tests/test_secondary_contact.py`: the FTI is
  installed; the type is addable inside an Event and several times over; it is
  not addable elsewhere (`global_allow` false); `related_contact` is a
  single-valued `Choice` on `imio.events.vocabulary.RemoteDirectoryContact`;
  `title` is optional and an object without one is valid; the Load button fills
  the grids against a mocked directory; the serializer output shape, covering
  None-vs-empty `visible_columns` and the `type` token; the indexer / metadata
  path; the subscriber reindexing the parent Event.

Test placement and fixtures follow the existing testing layers
(`imio/events/core/tests/testing.py`) and, for `imio.smartweb.core`, the
project's `plone-testing` skill.

## Order of work

`imio.smartweb.common` is checked out **twice**, both clones at `f1d16b1`: one
under `buildout.events` (clean tree, on `WEBBDC-2835`) and one under
`buildout.smartweb` (carrying unrelated uncommitted changes —
`test_registry_export.py`, `CHANGES.rst`, `common/__init__.py` — which must not
be touched).

1. Build the shared layer in the `buildout.events` clone of
   `imio.smartweb.common`.
2. Propagate it to the `buildout.smartweb` clone (a git operation the author
   performs).
3. Adapt `imio.smartweb.core`, run its test suite.
4. Implement `imio.events.core`, run its test suite.

No commits are made by the implementation: the author commits. This includes
this spec document.

## Assumptions to verify, not presume

1. **Load-bearing**: that `plone.autoform` merges `model.fieldset` and
   `directives.widget` tagged values inherited from a base schema interface
   (`mergedTaggedValueList` walks the interface bases). The
   `IContactInformationsGrids` mixin rests entirely on this. Verify it with a
   test early. Fallback if it misbehaves: duplicate the three field
   declarations in each package — the row schemas and the helper functions stay
   shared regardless.
2. That `imio.smartweb.core.utils.get_json` and
   `imio.smartweb.common.utils.get_json` are equivalent. Diff them before
   switching the moved code over to the common one.
3. That a catalog metadata column holding a list of dicts is acceptable. Any
   picklable value is supported; the cost is catalog size, and the payload is a
   handful of rows per event. Acceptable, recorded here so it is a decision
   rather than an oversight.

## i18n

New user-facing strings use the `imio.smartweb` domain via
`SmartwebMessageFactory`. English msgids are authored in the code; FR/NL/DE
translations live in `imio.smartweb.locales` and are added there separately.
Existing msgids reused from the section are kept byte-identical so their
translations still apply.

## Housekeeping

`src/imio/events/core/contents/contact/` contains nothing but an untracked
`__pycache__/`, left over from the abandoned `imio.events.Contact` attempt
described in the superseded spec. It is removed.
