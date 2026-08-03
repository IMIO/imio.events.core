# Secondary Contact + shared contact layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `imio.events.SecondaryContact` content type to `imio.events.core`, built on a contact-row layer extracted into `imio.smartweb.common` and adopted by `imio.smartweb.core` in place of its own copies.

**Architecture:** `imio.smartweb.common` gains a `contact/` subpackage owning the shape of a directory contact row (row schemas, a schema mixin carrying the three datagrids, the pure row-building functions) and the form mixin that reloads those grids from the directory. `imio.smartweb.core` keeps its section and its whole render path but imports the shared pieces. `imio.events.core` adds a leaf content type inside `imio.events.Event` and publishes a stored snapshot of the retained rows through `@events`, via both the full serializer and a catalog metadata column.

**Tech Stack:** Plone 6.1, Dexterity, `plone.autoform` / `plone.supermodel`, `collective.z3cform.datagridfield` 3.x, `z3c.form`, `plone.restapi`, `zope.testrunner` via `./bin/test`.

**Spec:** `docs/superpowers/specs/2026-07-31-secondary-contact-shared-layer-design.md` (in `imio.events.core`).

## Global Constraints

- **Never run `git commit`, `git add`, or `git push`.** The author commits. Every "Checkpoint" step means: run the suite, report the result, stop. This overrides the commit steps the plan template would normally use.
- Three working copies, absolute paths used throughout:
  - `COMMON` = `/home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common` (clean, branch `WEBBDC-2835`)
  - `CORE` = `/home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core` (branch `WEBBDC-2835`, commit `013b23d7`)
  - `EVENTS` = `/home/cboulanger/iasmartweb/buildout.events/src/imio.events.core` (branch `WEBBDC-2835`)
- **FOUR clones of `imio.smartweb.common` exist** (discovered during Task 1/2 — the original plan wrongly assumed two):

  | Path | Branch | Consumed by |
  |---|---|---|
  | `COMMON` (`buildout.events/src/imio.smartweb.common`) | `WEBBDC-2835` | its own `bin/test` — **the one we edit** |
  | `buildout.smartweb/src/imio.smartweb.common` | `main` | nothing. **Do not touch** (unrelated uncommitted changes) |
  | `CORE/devel/imio.smartweb.common` | `main` | **`imio.smartweb.core`'s tests** |
  | `EVENTS/devel/imio.smartweb.common` | `main` | **`imio.events.core`'s tests** |

  Both consumers pull their own `mr.developer` checkout (`imio.smartweb.common = auto`) into `devel/`, so they do **not** see edits made in `COMMON` until propagated.

- **Propagation mechanism (author's decision): symlinks.** Each consumer's
  `devel/imio.smartweb.common` has been moved aside to
  `devel/imio.smartweb.common.orig-checkout` and replaced by a symlink to
  `COMMON`. Both consumers therefore see `COMMON` edits live, with no push
  required. **This must be undone before the author's final verification and
  before any `make buildout`** — see Task 14 Step 6.

- **Task order revised** for the same reason: all `COMMON` work lands first
  (Tasks 2a, 3, 4a, 5, 6), then all `CORE` work (Tasks 2b, 4b, 7), then all
  `EVENTS` work (Tasks 8-13). Task 2 and Task 4 each split into an `a` half
  (write in `COMMON`) and a `b` half (delete from `CORE`, retarget imports).
  No content changes, only sequencing.
- Vocabulary names are kept **byte-identical**: `imio.smartweb.vocabulary.PhoneDisplayColumns`, `imio.smartweb.vocabulary.MailDisplayColumns`, `imio.smartweb.vocabulary.UrlDisplayColumns`.
- Existing msgids reused from the section are kept **byte-identical**, including plural wording such as `"Read-only rows loaded from the related contacts with the button at the bottom of this form. Check the columns you want to display; uncheck them all to hide the row."` New strings use `SmartwebMessageFactory as _` (domain `imio.smartweb`).
- Type label is **`Secondary contact`** in `imio.events.core`; the section stays **`Section contact`** in `imio.smartweb.core`. These never converge.
- `imio.events.core` must **not** import anything from `imio.smartweb.core`.
- The None-vs-empty semantics of `visible_columns` is load-bearing everywhere: **absent / `None` ⇒ no preference recorded ⇒ every column**; **empty list ⇒ explicitly hidden ⇒ row dropped**. Never normalise one into the other.
- Test runners: `cd <REPO> && ./bin/test -t <TestClass-or-test_method>`, or `-m <dotted.module>` for a whole module. `COMMON` and `CORE` already have `bin/test`; `EVENTS` does not (see Task 1).

---

## File Structure

### `COMMON` — new and modified

| Path | Responsibility |
|---|---|
| `src/imio/smartweb/common/widgets/frozen_label.py` | **new** (moved from `CORE`) — read-only-looking TextLine widget that still submits |
| `src/imio/smartweb/common/contact/__init__.py` | **new** — empty package marker |
| `src/imio/smartweb/common/contact/rows.py` | **new** — 3 row schemas + `IContactInformationsGrids` schema mixin |
| `src/imio/smartweb/common/contact/directory.py` | **new** — row constants, `row_key`, `translated_type_label`, `build_display_rows`, `get_remote_contacts`, `visible_columns_map`, `displayed_rows` |
| `src/imio/smartweb/common/contact/forms.py` | **new** — `ContactInformationsGridMixin`, `DISPLAY_FIELDS`, `KIND_BY_FIELD`, `CONTACT_UIDS_SEPARATOR` |
| `src/imio/smartweb/common/vocabularies.py` | **modify** — add the 4 `*DisplayColumns` factory classes |
| `src/imio/smartweb/common/vocabularies.zcml` | **modify** — register the 3 vocabularies |
| `src/imio/smartweb/common/tests/test_frozen_label.py` | **new** (moved from `CORE`) |
| `src/imio/smartweb/common/tests/test_contact_directory.py` | **new** |
| `src/imio/smartweb/common/tests/test_contact_rows.py` | **new** — guards the schema-mixin inheritance assumption |
| `src/imio/smartweb/common/tests/test_contact_forms.py` | **new** — stub-based mixin helper tests |
| `CHANGES.rst` | **modify** |

### `CORE` — modified only

| Path | Change |
|---|---|
| `src/imio/smartweb/core/widgets/frozen_label.py` | **delete** |
| `src/imio/smartweb/core/tests/test_frozen_label.py` | **delete** (moved to `COMMON`) |
| `src/imio/smartweb/core/vocabularies.py` | remove the 4 `*DisplayColumns` classes |
| `src/imio/smartweb/core/vocabularies.zcml` | remove the 3 registrations |
| `src/imio/smartweb/core/contents/sections/contact/content.py` | drop the 3 row schemas and 3 grid declarations; inherit the mixin |
| `src/imio/smartweb/core/contents/sections/contact/utils.py` | import the shared helpers; `ContactProperties` delegates |
| `src/imio/smartweb/core/contents/sections/contact/forms.py` | `SectionContactGridMixin` on the shared mixin |
| `setup.py`, `CHANGES.rst` | version floor on `imio.smartweb.common` |

### `EVENTS` — new and modified

| Path | Responsibility |
|---|---|
| `src/imio/events/core/contents/secondary_contact/__init__.py` | **rewrite** — empty package marker |
| `src/imio/events/core/contents/secondary_contact/content.py` | **rewrite** — `ISecondaryContact` / `SecondaryContact` |
| `src/imio/events/core/contents/secondary_contact/forms.py` | **rewrite** — add/edit forms with the Load button |
| `src/imio/events/core/contents/secondary_contact/serializer.py` | **new** — `kept_rows`, `serialize_secondary_contact`, `get_secondary_contacts` |
| `src/imio/events/core/contents/secondary_contact/configure.zcml` | **rewrite** — add adapter + edit page |
| `src/imio/events/core/contents/secondary_contact/utils.py` | **delete** — superseded by `COMMON` |
| `src/imio/events/core/contents/secondary_contact/view.py` | **delete** — REST only, no view |
| `src/imio/events/core/contents/secondary_contact/view.pt` | **delete** |
| `src/imio/events/core/contents/secondary_contact/macros.pt` | **delete** |
| `src/imio/events/core/contents/__init__.py` | **modify** — fix the broken WIP import |
| `src/imio/events/core/indexers.py`, `indexers.zcml` | **modify** — `secondary_contacts` indexer |
| `src/imio/events/core/subscribers.py`, `subscribers.zcml` | **modify** — reindex parent Event |
| `src/imio/events/core/contents/event/serializer.py` | **modify** — emit the key |
| `src/imio/events/core/rest/endpoint.py` | **modify** — add to `metadata_fields` |
| `src/imio/events/core/profiles/default/types/imio.events.SecondaryContact.xml` | **rewrite** |
| `src/imio/events/core/profiles/default/types.xml`, `catalog.xml`, `workflows.xml`, `metadata.xml` | **modify** |
| `src/imio/events/core/upgrades/profiles/1026_to_1027/*` | **new** |
| `src/imio/events/core/upgrades/configure.zcml`, `upgrades/upgrades.py` | **modify** |
| `src/imio/events/core/tests/test_secondary_contact.py` | **new** |
| `setup.py`, `CHANGES.rst` | **modify** |

---

## Task 1: Bootstrap and verify the two load-bearing assumptions

The `IContactInformationsGrids` mixin rests entirely on `plone.autoform` merging
tagged values across interface bases. Prove it before building on it. Also prove
the two `get_json` implementations are equivalent before swapping callers over.

**Files:**
- Create: `COMMON/src/imio/smartweb/common/tests/test_contact_rows.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a green `EVENTS` buildout (`EVENTS/bin/test` exists); a permanent test guarding tagged-value inheritance.

- [ ] **Step 1: Build the `EVENTS` sandbox (it has no `bin/` yet)**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && make buildout`
Expected: succeeds and creates `bin/test`. This is slow (several minutes). If it fails, stop and report — every later `EVENTS` task depends on it.

- [ ] **Step 2: Diff the two `get_json` implementations**

Run:
```bash
cd /home/cboulanger/iasmartweb
diff <(sed -n '/^def get_json/,/^def /p' buildout.smartweb/src/imio.smartweb.core/src/imio/smartweb/core/utils.py) \
     <(sed -n '/^def get_json/,/^def /p' buildout.events/src/imio.smartweb.common/src/imio/smartweb/common/utils.py)
```
Expected: no differences, or only differences that provably do not change behaviour (identical headers, identical timeout default, identical `None` on error). **If they differ materially, stop and report** — the moved code's behaviour would silently change, and that decision is the author's.

- [ ] **Step 3: Write the failing test for tagged-value inheritance**

Create `COMMON/src/imio/smartweb/common/tests/test_contact_rows.py`:

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.rows import IContactInformationsGrids
from imio.smartweb.common.contact.rows import IMailDisplayRow
from imio.smartweb.common.contact.rows import IPhoneDisplayRow
from imio.smartweb.common.contact.rows import IUrlDisplayRow
from plone.autoform.interfaces import FIELDSETS_KEY
from plone.autoform.interfaces import WIDGETS_KEY
from plone.supermodel import model
from plone.supermodel.interfaces import FIELDSETS_KEY as SM_FIELDSETS_KEY  # noqa
from plone.supermodel.utils import mergedTaggedValueDict
from plone.supermodel.utils import mergedTaggedValueList
from zope import schema

import unittest


class IDerived(IContactInformationsGrids):
    """A schema inheriting the shared grids, like the real consumers do."""

    extra = schema.TextLine(title="Extra", required=False)


class TestContactRows(unittest.TestCase):
    """These tests are the guard on the assumption the mixin rests on:
    that plone.autoform collects fieldsets and widget directives from an
    interface's BASES, not only from the interface itself. If they ever fail,
    the fallback is to declare the three grid fields in each product.
    """

    def test_derived_schema_inherits_the_grid_fields(self):
        names = schema.getFieldNamesInOrder(IDerived)
        self.assertIn("phones_display", names)
        self.assertIn("mails_display", names)
        self.assertIn("urls_display", names)
        self.assertIn("extra", names)

    def test_derived_schema_inherits_the_fieldset(self):
        fieldsets = mergedTaggedValueList(IDerived, FIELDSETS_KEY)
        names = [fieldset.__name__ for fieldset in fieldsets]
        self.assertIn("contact_informations", names)
        fieldset = [f for f in fieldsets if f.__name__ == "contact_informations"][0]
        self.assertEqual(
            ["phones_display", "mails_display", "urls_display"],
            list(fieldset.fields),
        )

    def test_derived_schema_inherits_the_widget_directives(self):
        widgets = mergedTaggedValueDict(IDerived, WIDGETS_KEY)
        self.assertIn("phones_display", widgets)
        self.assertIn("mails_display", widgets)
        self.assertIn("urls_display", widgets)

    def test_row_schemas_carry_the_hidden_type_token(self):
        for row_schema in (IPhoneDisplayRow, IMailDisplayRow, IUrlDisplayRow):
            names = schema.getFieldNamesInOrder(row_schema)
            self.assertIn("type_token", names)
            self.assertIn("contact_uid", names)
            self.assertIn("visible_columns", names)

    def test_phone_row_columns(self):
        names = schema.getFieldNamesInOrder(IPhoneDisplayRow)
        for column in ("label", "type", "number"):
            self.assertIn(column, names)

    def test_mail_row_columns(self):
        names = schema.getFieldNamesInOrder(IMailDisplayRow)
        for column in ("label", "type", "mail_address"):
            self.assertIn(column, names)

    def test_url_row_columns(self):
        names = schema.getFieldNamesInOrder(IUrlDisplayRow)
        for column in ("type", "url"):
            self.assertIn(column, names)


class TestModelSchemaMarker(unittest.TestCase):
    def test_grids_mixin_is_a_model_schema(self):
        self.assertTrue(issubclass(IContactInformationsGrids, model.Schema))
```

- [ ] **Step 4: Run it to confirm it fails for the right reason**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_rows`
Expected: collection error — `ModuleNotFoundError: No module named 'imio.smartweb.common.contact'`. That is the correct failure; `rows.py` arrives in Task 3.

- [ ] **Step 5: Checkpoint**

Report: whether `EVENTS/bin/test` now exists, and the outcome of the `get_json` diff. Do not commit.

---

## Task 2: Move `FrozenLabelTextFieldWidget` into `COMMON`

The hard blocker: `imio.events.core` cannot import this widget from
`imio.smartweb.core`. Move it, with its test, unchanged.

**Files:**
- Create: `COMMON/src/imio/smartweb/common/widgets/frozen_label.py`
- Create: `COMMON/src/imio/smartweb/common/tests/test_frozen_label.py`
- Delete: `CORE/src/imio/smartweb/core/widgets/frozen_label.py`
- Delete: `CORE/src/imio/smartweb/core/tests/test_frozen_label.py`
- Modify: `CORE/src/imio/smartweb/core/contents/sections/contact/content.py` (import line only, for now)

**Interfaces:**
- Produces: `imio.smartweb.common.widgets.frozen_label.FrozenLabelTextWidget` (class) and `FrozenLabelTextFieldWidget(field, request) -> IFieldWidget` (factory function). Task 3 imports the factory.

- [ ] **Step 1: Copy the widget module into `COMMON` verbatim**

Create `COMMON/src/imio/smartweb/common/widgets/frozen_label.py` with exactly the content of `CORE/src/imio/smartweb/core/widgets/frozen_label.py`:

```python
# -*- coding: utf-8 -*-

from html import escape
from xml.sax.saxutils import quoteattr
from z3c.form.browser.text import TextWidget
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import NO_VALUE
from z3c.form.widget import FieldWidget
from zope.interface import implementer


class FrozenLabelTextWidget(TextWidget):
    """Render a TextLine column as a read-only label while still submitting it.

    A ``mode="display"`` column looks right but emits no input, so it is not
    submitted and ``DictRow._validate`` rejects every row on save with
    ``AttributeNotFoundError``. ``readonly=True`` is worse: it overwrites the
    row value with the field's single ``default``, so it cannot carry a
    per-row-distinct value. This widget keeps the field in input mode -- so
    extraction is inherited unchanged from TextWidget -- yet renders only a
    span plus a hidden input.
    """

    def render(self):
        value = self.value
        if value is NO_VALUE or value is None:
            value = ""
        elif isinstance(value, (list, tuple)):
            # In a DataGrid the sub-widget value is the raw field value; a
            # list would otherwise render its first character only.
            value = value[0] if value else ""
        value = str(value)
        return (
            '<span class="dgf-frozen-label">{label}</span>'
            '<input type="hidden" name={name} value={value} />'
        ).format(
            label=escape(value),
            name=quoteattr(self.name),
            value=quoteattr(value),
        )


@implementer(IFieldWidget)
def FrozenLabelTextFieldWidget(field, request) -> IFieldWidget:
    return FieldWidget(field, FrozenLabelTextWidget(request))
```

- [ ] **Step 2: Move the test, retargeting its import and base class**

Read `CORE/src/imio/smartweb/core/tests/test_frozen_label.py`, then create
`COMMON/src/imio/smartweb/common/tests/test_frozen_label.py` with the same test
bodies, changing only:
- `from imio.smartweb.core.widgets.frozen_label import …` → `from imio.smartweb.common.widgets.frozen_label import …`
- the base class `ImioSmartwebTestCase` → `unittest.TestCase` if the original base came from `imio.smartweb.core.tests.utils`, since `COMMON` has no such helper. If the original used a `layer`, use `IMIO_SMARTWEB_COMMON_INTEGRATION_TESTING` from `imio.smartweb.common.testing` instead.

Do not invent new assertions here; the point is a like-for-like move.

- [ ] **Step 3: Run the moved test**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_frozen_label`
Expected: PASS, same number of tests as the `CORE` original.

- [ ] **Step 4: Point `CORE` at the moved widget and delete its copies**

In `CORE/src/imio/smartweb/core/contents/sections/contact/content.py` change:
```python
from imio.smartweb.core.widgets.frozen_label import FrozenLabelTextFieldWidget
```
to:
```python
from imio.smartweb.common.widgets.frozen_label import FrozenLabelTextFieldWidget
```
Then delete `CORE/src/imio/smartweb/core/widgets/frozen_label.py` and
`CORE/src/imio/smartweb/core/tests/test_frozen_label.py`.

Then check nothing else referenced them:
```bash
cd /home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core
grep -rn "core.widgets.frozen_label\|core\.widgets import frozen_label" src/
```
Expected: no output.

- [ ] **Step 5: Run the section's tests to prove `CORE` still works**

Run: `cd /home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core && ./bin/test -m imio.smartweb.core.tests.test_section_contact -m imio.smartweb.core.tests.test_section_contact_forms`
Expected: PASS, unchanged.

- [ ] **Step 6: Checkpoint** — report both suites. Do not commit.

---

## Task 3: `COMMON/contact/rows.py` — row schemas and the grids mixin

**Files:**
- Create: `COMMON/src/imio/smartweb/common/contact/__init__.py` (empty)
- Create: `COMMON/src/imio/smartweb/common/contact/rows.py`
- Test: `COMMON/src/imio/smartweb/common/tests/test_contact_rows.py` (already written in Task 1)

**Interfaces:**
- Consumes: `imio.smartweb.common.widgets.frozen_label.FrozenLabelTextFieldWidget` (Task 2).
- Produces: `IPhoneDisplayRow`, `IMailDisplayRow`, `IUrlDisplayRow`, `IContactInformationsGrids`. Each row schema has fields `contact_uid` (hidden), `type_token` (hidden), `contact_title`, its data columns, and `visible_columns`. `IContactInformationsGrids` has `phones_display`, `mails_display`, `urls_display` in fieldset `contact_informations`.

- [ ] **Step 1: Confirm the test from Task 1 still fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_rows`
Expected: `ModuleNotFoundError: No module named 'imio.smartweb.common.contact'`.

- [ ] **Step 2: Create the empty package marker**

Create `COMMON/src/imio/smartweb/common/contact/__init__.py` as an empty file.

- [ ] **Step 3: Write `rows.py`**

Create `COMMON/src/imio/smartweb/common/contact/rows.py`:

```python
# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from imio.smartweb.common.widgets.frozen_label import FrozenLabelTextFieldWidget
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.autoform import directives
from plone.supermodel import model
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import Interface

# Shared by imio.smartweb.core (Section contact) and imio.events.core
# (Secondary contact). The two products disagree on ONE point, deliberately:
# in the section the data columns below are RESIDUE (the page render re-reads
# the live directory payload and only `visible_columns` is authoritative),
# while in imio.events.core they ARE the published data -- an event must show
# the contact as it was for that event. `type_token` exists because of that
# divergence: see its docstring.


class _ContactRowBase(Interface):
    """Columns every contact row carries, whatever its kind.

    Every column but `visible_columns` is remote directory data rendered as a
    frozen label: read-only looking, yet still submitted, because DictRow
    rejects a row whose keys are missing.
    """

    directives.mode(contact_uid="hidden")
    contact_uid = schema.TextLine(title=_("Contact UID"), required=False)

    directives.mode(type_token="hidden")
    type_token = schema.TextLine(title=_("Type token"), required=False)
    # The RAW remote `type` token. The visible `type` column holds the
    # TRANSLATED label, which is what an editor wants to read but freezes the
    # editor's language into storage. Consumers that publish the stored row
    # (imio.events.core) must read this column and let their own consumer
    # translate; the section ignores it, since it re-reads the live payload.

    directives.widget("contact_title", FrozenLabelTextFieldWidget)
    contact_title = schema.TextLine(title=_("Contact"), required=False)


class IPhoneDisplayRow(_ContactRowBase):
    """One phone row of a related contact, plus the columns to display."""

    directives.widget("label", FrozenLabelTextFieldWidget)
    label = schema.TextLine(title=_("Label"), required=False)

    directives.widget("type", FrozenLabelTextFieldWidget)
    type = schema.TextLine(title=_("Type"), required=False)

    directives.widget("number", FrozenLabelTextFieldWidget)
    number = schema.TextLine(title=_("Number"), required=False)

    directives.widget("visible_columns", CheckBoxFieldWidget)
    visible_columns = schema.List(
        title=_("Displayed columns"),
        value_type=schema.Choice(
            vocabulary="imio.smartweb.vocabulary.PhoneDisplayColumns"
        ),
        required=False,
    )


class IMailDisplayRow(_ContactRowBase):
    """One e-mail row of a related contact, plus the columns to display."""

    directives.widget("label", FrozenLabelTextFieldWidget)
    label = schema.TextLine(title=_("Label"), required=False)

    directives.widget("type", FrozenLabelTextFieldWidget)
    type = schema.TextLine(title=_("Type"), required=False)

    directives.widget("mail_address", FrozenLabelTextFieldWidget)
    mail_address = schema.TextLine(title=_("E-mail"), required=False)

    directives.widget("visible_columns", CheckBoxFieldWidget)
    visible_columns = schema.List(
        title=_("Displayed columns"),
        value_type=schema.Choice(
            vocabulary="imio.smartweb.vocabulary.MailDisplayColumns"
        ),
        required=False,
    )


class IUrlDisplayRow(_ContactRowBase):
    """One URL row of a related contact, plus the columns to display."""

    directives.widget("type", FrozenLabelTextFieldWidget)
    type = schema.TextLine(title=_("Type"), required=False)

    directives.widget("url", FrozenLabelTextFieldWidget)
    url = schema.TextLine(title=_("Url"), required=False)

    directives.widget("visible_columns", CheckBoxFieldWidget)
    visible_columns = schema.List(
        title=_("Displayed columns"),
        value_type=schema.Choice(
            vocabulary="imio.smartweb.vocabulary.UrlDisplayColumns"
        ),
        required=False,
    )


class IContactInformationsGrids(model.Schema):
    """The three read-only contact-informations datagrids.

    Inherited by ISectionContact (imio.smartweb.core) and ISecondaryContact
    (imio.events.core) so the declarations exist once. The field descriptions
    keep their original plural wording so the translations already authored in
    imio.smartweb.locales stay valid.
    """

    model.fieldset(
        "contact_informations",
        label=_("Contact informations"),
        fields=["phones_display", "mails_display", "urls_display"],
    )

    directives.widget(
        "phones_display",
        DataGridFieldFactory,
        allow_insert=False,
        allow_delete=False,
        allow_reorder=False,
        auto_append=False,
    )
    phones_display = schema.List(
        title=_("Phones"),
        description=_(
            "Read-only rows loaded from the related contacts with the button "
            "at the bottom of this form. Check the columns you want to "
            "display; uncheck them all to hide the row."
        ),
        value_type=DictRow(title="Value", schema=IPhoneDisplayRow),
        required=False,
    )

    directives.widget(
        "mails_display",
        DataGridFieldFactory,
        allow_insert=False,
        allow_delete=False,
        allow_reorder=False,
        auto_append=False,
    )
    mails_display = schema.List(
        title=_("E-mails"),
        description=_(
            "Read-only rows loaded from the related contacts with the button "
            "at the bottom of this form. Check the columns you want to "
            "display; uncheck them all to hide the row."
        ),
        value_type=DictRow(title="Value", schema=IMailDisplayRow),
        required=False,
    )

    directives.widget(
        "urls_display",
        DataGridFieldFactory,
        allow_insert=False,
        allow_delete=False,
        allow_reorder=False,
        auto_append=False,
    )
    urls_display = schema.List(
        title=_("URLs"),
        description=_(
            "Read-only rows loaded from the related contacts with the button "
            "at the bottom of this form. Check the columns you want to "
            "display; uncheck them all to hide the row."
        ),
        value_type=DictRow(title="Value", schema=IUrlDisplayRow),
        required=False,
    )
```

- [ ] **Step 4: Run the test**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_rows`
Expected: PASS.

**If `test_derived_schema_inherits_the_fieldset` or
`test_derived_schema_inherits_the_widget_directives` fails**, the mixin
assumption is wrong. Do **not** work around it silently. Stop, report, and
apply the documented fallback: delete `IContactInformationsGrids`, declare the
three grid fields directly in `ISectionContact` and `ISecondaryContact`, and
keep sharing only the row schemas. Every later task still works; only the two
`content.py` files grow.

- [ ] **Step 5: Checkpoint** — report the suite. Do not commit.

---

## Task 4: Move the `*DisplayColumns` vocabularies into `COMMON`

**Files:**
- Modify: `COMMON/src/imio/smartweb/common/vocabularies.py`
- Modify: `COMMON/src/imio/smartweb/common/vocabularies.zcml`
- Create: `COMMON/src/imio/smartweb/common/tests/test_contact_vocabularies.py`
- Modify: `CORE/src/imio/smartweb/core/vocabularies.py` (remove)
- Modify: `CORE/src/imio/smartweb/core/vocabularies.zcml` (remove)

**Interfaces:**
- Produces: named vocabulary utilities `imio.smartweb.vocabulary.PhoneDisplayColumns` (terms `label`, `type`, `number`), `…MailDisplayColumns` (`label`, `type`, `mail_address`), `…UrlDisplayColumns` (`type`, `url`). Task 5's `CONTACT_ROW_COLUMNS` must mirror these token-for-token.

- [ ] **Step 1: Write the failing test**

Create `COMMON/src/imio/smartweb/common/tests/test_contact_vocabularies.py`:

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.testing import IMIO_SMARTWEB_COMMON_INTEGRATION_TESTING
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestContactDisplayColumnsVocabularies(unittest.TestCase):
    layer = IMIO_SMARTWEB_COMMON_INTEGRATION_TESTING

    def _tokens(self, name):
        factory = getUtility(IVocabularyFactory, name)
        return [term.token for term in factory()]

    def test_phone_display_columns(self):
        self.assertEqual(
            ["label", "type", "number"],
            self._tokens("imio.smartweb.vocabulary.PhoneDisplayColumns"),
        )

    def test_mail_display_columns(self):
        self.assertEqual(
            ["label", "type", "mail_address"],
            self._tokens("imio.smartweb.vocabulary.MailDisplayColumns"),
        )

    def test_url_display_columns(self):
        self.assertEqual(
            ["type", "url"],
            self._tokens("imio.smartweb.vocabulary.UrlDisplayColumns"),
        )
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_vocabularies`
Expected: FAIL with `ComponentLookupError` for the vocabulary names.

- [ ] **Step 3: Add the factories to `COMMON/vocabularies.py`**

Append to `COMMON/src/imio/smartweb/common/vocabularies.py` (it already imports
`SimpleVocabulary` and `SmartwebMessageFactory as _`; add imports only if
missing):

```python
class ContactDisplayColumnsVocabularyFactory:
    """Columns of a contact-informations row that an editor can show or hide.

    The tokens are the keys of the remote directory row payload, so they can be
    matched against it directly at render time. They MUST mirror
    imio.smartweb.common.contact.directory.CONTACT_ROW_COLUMNS token for token.
    """

    columns = ()

    def __call__(self, context=None):
        terms = [
            SimpleVocabulary.createTerm(name, name, title)
            for name, title in self.columns
        ]
        return SimpleVocabulary(terms)


class PhoneDisplayColumnsVocabularyFactory(ContactDisplayColumnsVocabularyFactory):
    columns = (
        ("label", _("Label")),
        ("type", _("Type")),
        ("number", _("Number")),
    )


PhoneDisplayColumnsVocabulary = PhoneDisplayColumnsVocabularyFactory()


class MailDisplayColumnsVocabularyFactory(ContactDisplayColumnsVocabularyFactory):
    columns = (
        ("label", _("Label")),
        ("type", _("Type")),
        ("mail_address", _("E-mail")),
    )


MailDisplayColumnsVocabulary = MailDisplayColumnsVocabularyFactory()


class UrlDisplayColumnsVocabularyFactory(ContactDisplayColumnsVocabularyFactory):
    columns = (
        ("type", _("Type")),
        ("url", _("Url")),
    )


UrlDisplayColumnsVocabulary = UrlDisplayColumnsVocabularyFactory()
```

- [ ] **Step 4: Register them in `COMMON/vocabularies.zcml`**

Add inside the existing `<configure>` element:

```xml
  <utility
      name="imio.smartweb.vocabulary.PhoneDisplayColumns"
      component=".vocabularies.PhoneDisplayColumnsVocabulary"
      />

  <utility
      name="imio.smartweb.vocabulary.MailDisplayColumns"
      component=".vocabularies.MailDisplayColumnsVocabulary"
      />

  <utility
      name="imio.smartweb.vocabulary.UrlDisplayColumns"
      component=".vocabularies.UrlDisplayColumnsVocabulary"
      />
```

Match the surrounding elements' exact form: open `COMMON/src/imio/smartweb/common/vocabularies.zcml` and copy the shape used by the neighbouring registrations (in particular whether they use `provides="zope.schema.interfaces.IVocabularyFactory"`). Do not guess.

- [ ] **Step 5: Run the test**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_vocabularies`
Expected: PASS.

- [ ] **Step 6: Remove the `CORE` copies**

From `CORE/src/imio/smartweb/core/vocabularies.py` delete
`ContactDisplayColumnsVocabularyFactory`,
`PhoneDisplayColumnsVocabularyFactory`, `PhoneDisplayColumnsVocabulary`,
`MailDisplayColumnsVocabularyFactory`, `MailDisplayColumnsVocabulary`,
`UrlDisplayColumnsVocabularyFactory`, `UrlDisplayColumnsVocabulary` (around
lines 911-957). From `CORE/src/imio/smartweb/core/vocabularies.zcml` delete the
three `*DisplayColumns` registrations (around lines 214-231).

Leaving both registered would make two utilities compete for one name.

- [ ] **Step 7: Prove `CORE` still resolves the vocabularies through `COMMON`**

Run: `cd /home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core && ./bin/test -m imio.smartweb.core.tests.test_section_contact -m imio.smartweb.core.tests.test_section_contact_forms`
Expected: PASS. `CORE` loads `COMMON`'s ZCML, so the names resolve.

- [ ] **Step 8: Checkpoint** — report both suites. Do not commit.

---

## Task 5: `COMMON/contact/directory.py` — constants and pure functions

**Files:**
- Create: `COMMON/src/imio/smartweb/common/contact/directory.py`
- Create: `COMMON/src/imio/smartweb/common/tests/test_contact_directory.py`

**Interfaces:**
- Consumes: `imio.smartweb.common.config.DIRECTORY_URL`, `imio.smartweb.common.utils.get_json`.
- Produces:
  - `CONTACT_TYPE_LABELS: dict[str, dict[str, Message]]`
  - `CONTACT_ROW_KEYS: dict[str, str]` — `{"phones": "number", "mails": "mail_address", "urls": "url"}`
  - `CONTACT_ROW_COLUMNS: dict[str, tuple[str, ...]]`
  - `translated_type_label(kind: str, token: str) -> str`
  - `row_key(kind: str, row: dict) -> str`
  - `build_display_rows(kind: str, contacts: list[dict], preferences: dict | None = None) -> list[dict]`
  - `get_remote_contacts(uids: list[str]) -> list[dict]`
  - `visible_columns_map(context, kind: str) -> dict[tuple[str, str], list[str]]`
  - `displayed_rows(payload: dict, context, kind: str) -> list[dict]` returning `[{"data": <remote row>, "columns": <set[str]>}, …]`

- [ ] **Step 1: Write the failing tests**

Create `COMMON/src/imio/smartweb/common/tests/test_contact_directory.py`:

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.directory import build_display_rows
from imio.smartweb.common.contact.directory import CONTACT_ROW_COLUMNS
from imio.smartweb.common.contact.directory import CONTACT_ROW_KEYS
from imio.smartweb.common.contact.directory import displayed_rows
from imio.smartweb.common.contact.directory import get_remote_contacts
from imio.smartweb.common.contact.directory import row_key
from imio.smartweb.common.contact.directory import translated_type_label
from imio.smartweb.common.contact.directory import visible_columns_map
from imio.smartweb.common.testing import IMIO_SMARTWEB_COMMON_INTEGRATION_TESTING
from unittest import mock

import unittest


CONTACT = {
    "UID": "uid-1",
    "title": "Service culture",
    "phones": [
        {"label": "Accueil", "type": "work", "number": "081 12 34 56"},
        {"label": "", "type": "cell", "number": "0470 00 00 00"},
        {"label": "Sans numero", "type": "work", "number": ""},
    ],
    "mails": [{"label": "", "type": "work", "mail_address": "culture@ville.be"}],
    "urls": [{"type": "website", "url": "https://ville.be"}],
}


class _Stored:
    """Minimal stand-in for a content object carrying the stored grids."""

    def __init__(self, **grids):
        for name, rows in grids.items():
            setattr(self, name, rows)


class TestRowIdentity(unittest.TestCase):
    def test_row_key_uses_the_kind_s_key_column(self):
        self.assertEqual("number", CONTACT_ROW_KEYS["phones"])
        self.assertEqual("mail_address", CONTACT_ROW_KEYS["mails"])
        self.assertEqual("url", CONTACT_ROW_KEYS["urls"])

    def test_row_key_strips(self):
        self.assertEqual("081", row_key("phones", {"number": "  081  "}))

    def test_row_key_of_a_row_without_its_key_column_is_empty(self):
        self.assertEqual("", row_key("phones", {"number": None}))
        self.assertEqual("", row_key("phones", {}))

    def test_columns_mirror_the_vocabularies(self):
        self.assertEqual(("label", "type", "number"), CONTACT_ROW_COLUMNS["phones"])
        self.assertEqual(
            ("label", "type", "mail_address"), CONTACT_ROW_COLUMNS["mails"]
        )
        self.assertEqual(("type", "url"), CONTACT_ROW_COLUMNS["urls"])


class TestTranslatedTypeLabel(unittest.TestCase):
    layer = IMIO_SMARTWEB_COMMON_INTEGRATION_TESTING

    def test_empty_token_gives_empty_string(self):
        self.assertEqual("", translated_type_label("phones", ""))
        self.assertEqual("", translated_type_label("phones", None))

    def test_unknown_token_degrades_to_the_raw_token(self):
        self.assertEqual(
            "carrier-pigeon", translated_type_label("phones", "carrier-pigeon")
        )

    def test_known_token_is_translated_to_something_non_empty(self):
        # The exact wording lives in imio.smartweb.locales; all we assert is
        # that a known token does not come back as the raw token.
        self.assertTrue(translated_type_label("phones", "work"))


class TestBuildDisplayRows(unittest.TestCase):
    layer = IMIO_SMARTWEB_COMMON_INTEGRATION_TESTING

    def test_rows_without_a_key_are_skipped(self):
        rows = build_display_rows("phones", [CONTACT])
        self.assertEqual(2, len(rows))
        self.assertEqual(["081 12 34 56", "0470 00 00 00"], [r["number"] for r in rows])

    def test_absent_preference_yields_every_column(self):
        rows = build_display_rows("phones", [CONTACT])
        self.assertEqual(
            ["label", "type", "number"], list(rows[0]["visible_columns"])
        )

    def test_empty_preference_is_kept_empty(self):
        rows = build_display_rows(
            "phones", [CONTACT], {("uid-1", "081 12 34 56"): []}
        )
        self.assertEqual([], rows[0]["visible_columns"])
        # the other row keeps its default
        self.assertEqual(
            ["label", "type", "number"], list(rows[1]["visible_columns"])
        )

    def test_partial_preference_is_carried_over(self):
        rows = build_display_rows(
            "phones", [CONTACT], {("uid-1", "081 12 34 56"): ["number"]}
        )
        self.assertEqual(["number"], rows[0]["visible_columns"])

    def test_each_row_owns_its_default_list(self):
        rows = build_display_rows("phones", [CONTACT])
        rows[0]["visible_columns"].append("bogus")
        self.assertEqual(
            ["label", "type", "number"], list(rows[1]["visible_columns"])
        )

    def test_row_carries_contact_identity(self):
        rows = build_display_rows("phones", [CONTACT])
        self.assertEqual("uid-1", rows[0]["contact_uid"])
        self.assertEqual("Service culture", rows[0]["contact_title"])

    def test_type_column_is_translated_and_type_token_is_raw(self):
        rows = build_display_rows("phones", [CONTACT])
        self.assertEqual("work", rows[0]["type_token"])
        self.assertEqual(
            translated_type_label("phones", "work"), rows[0]["type"]
        )

    def test_no_contacts_gives_no_rows(self):
        self.assertEqual([], build_display_rows("phones", []))


class TestGetRemoteContacts(unittest.TestCase):
    layer = IMIO_SMARTWEB_COMMON_INTEGRATION_TESTING

    def test_no_uids_short_circuits_without_a_request(self):
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json"
        ) as get_json:
            self.assertEqual([], get_remote_contacts([]))
            get_json.assert_not_called()

    def test_results_follow_the_requested_uid_order(self):
        payload = {"items": [{"UID": "b"}, {"UID": "a"}]}
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=payload,
        ):
            result = get_remote_contacts(["a", "b"])
        self.assertEqual(["a", "b"], [item["UID"] for item in result])

    def test_unrequested_uids_are_dropped(self):
        payload = {"items": [{"UID": "a"}, {"UID": "z"}]}
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=payload,
        ):
            result = get_remote_contacts(["a"])
        self.assertEqual(["a"], [item["UID"] for item in result])

    def test_directory_failure_gives_an_empty_list(self):
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json", return_value=None
        ):
            self.assertEqual([], get_remote_contacts(["a"]))


class TestStoredPreferences(unittest.TestCase):
    def test_visible_columns_map_keys_on_uid_and_row_key(self):
        context = _Stored(
            phones_display=[
                {
                    "contact_uid": "uid-1",
                    "number": "081 12 34 56",
                    "visible_columns": ["number"],
                }
            ]
        )
        self.assertEqual(
            {("uid-1", "081 12 34 56"): ["number"]},
            visible_columns_map(context, "phones"),
        )

    def test_a_none_visible_columns_is_left_out_of_the_map(self):
        context = _Stored(
            phones_display=[
                {"contact_uid": "uid-1", "number": "081", "visible_columns": None}
            ]
        )
        self.assertEqual({}, visible_columns_map(context, "phones"))

    def test_an_empty_visible_columns_is_recorded_as_empty(self):
        context = _Stored(
            phones_display=[
                {"contact_uid": "uid-1", "number": "081", "visible_columns": []}
            ]
        )
        self.assertEqual({("uid-1", "081"): []}, visible_columns_map(context, "phones"))

    def test_a_row_without_a_key_is_skipped(self):
        context = _Stored(
            phones_display=[{"contact_uid": "uid-1", "number": "", "visible_columns": []}]
        )
        self.assertEqual({}, visible_columns_map(context, "phones"))

    def test_missing_grid_attribute_gives_an_empty_map(self):
        self.assertEqual({}, visible_columns_map(_Stored(), "phones"))


class TestDisplayedRows(unittest.TestCase):
    def test_no_preference_shows_every_column(self):
        rows = displayed_rows(CONTACT, _Stored(), "phones")
        self.assertEqual(2, len(rows))
        self.assertEqual({"label", "type", "number"}, rows[0]["columns"])

    def test_an_explicitly_hidden_row_is_dropped(self):
        context = _Stored(
            phones_display=[
                {
                    "contact_uid": "uid-1",
                    "number": "081 12 34 56",
                    "visible_columns": [],
                }
            ]
        )
        rows = displayed_rows(CONTACT, context, "phones")
        self.assertEqual(["0470 00 00 00"], [r["data"]["number"] for r in rows])

    def test_columns_are_intersected_with_the_known_ones(self):
        context = _Stored(
            phones_display=[
                {
                    "contact_uid": "uid-1",
                    "number": "081 12 34 56",
                    "visible_columns": ["number", "bogus"],
                }
            ]
        )
        rows = displayed_rows(CONTACT, context, "phones")
        self.assertEqual({"number"}, rows[0]["columns"])

    def test_the_remote_row_is_returned_as_is(self):
        rows = displayed_rows(CONTACT, _Stored(), "phones")
        self.assertIs(CONTACT["phones"][0], rows[0]["data"])
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_directory`
Expected: collection error, `No module named 'imio.smartweb.common.contact.directory'`.

- [ ] **Step 3: Write `directory.py`**

Create `COMMON/src/imio/smartweb/common/contact/directory.py`. This is the
`CORE` section's `utils.py` module-level code, moved, with two changes: imports
retargeted to `COMMON`, and `build_display_rows` now also writing `type_token`.
`visible_columns_map` and `displayed_rows` become free functions.

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.config import DIRECTORY_URL
from imio.smartweb.common.utils import get_json
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from zope.i18n import translate

# Human labels of the remote `type` tokens. The directory owns these
# vocabularies (imio/directory/core/vocabularies.py); their msgids live in the
# shared `imio.smartweb` domain, so they can be reused here without depending
# on imio.directory.core. If the directory adds a type, its label degrades to
# the raw token -- visible but harmless.
CONTACT_TYPE_LABELS = {
    "phones": {
        "fax": _("Fax"),
        "cell": _("Mobile"),
        "home": _("Personal phone"),
        "work": _("Work phone"),
    },
    "mails": {
        "home": _("Personal email"),
        "work": _("Work email"),
    },
    "urls": {
        "facebook": _("Facebook"),
        "instagram": _("Instagram"),
        "linkedin": _("Linkedin"),
        "pinterest": _("Pinterest"),
        "twitter": _("Twitter"),
        "website": _("Website"),
        "youtube": _("Youtube"),
    },
}

# The remote column that identifies a row. A row without it cannot be keyed,
# so no preference can be recorded for it and it is skipped.
CONTACT_ROW_KEYS = {
    "phones": "number",
    "mails": "mail_address",
    "urls": "url",
}

# Columns of each row, in display order. Must mirror the *DisplayColumns
# vocabularies token for token.
CONTACT_ROW_COLUMNS = {
    "phones": ("label", "type", "number"),
    "mails": ("label", "type", "mail_address"),
    "urls": ("type", "url"),
}


def translated_type_label(kind, token):
    """Human label of a remote `type` token, or the raw token if unknown."""
    if not token:
        return ""
    msgid = CONTACT_TYPE_LABELS.get(kind, {}).get(token)
    if msgid is None:
        return token
    current_lang = api.portal.get_current_language()[:2]
    return translate(msgid, target_language=current_lang)


def row_key(kind, row):
    """Identity of a remote row: its payload value, or "" when it has none."""
    return (row.get(CONTACT_ROW_KEYS[kind]) or "").strip()


def build_display_rows(kind, contacts, preferences=None):
    """Build the DataGridField rows of `kind` from remote contact payloads.

    `contacts` is a list of contact dicts as returned by
    `@search?UID=...&fullobjects=1`. `preferences` maps
    `(contact_uid, row_key)` to a list of column names to carry over.

    A key ABSENT from `preferences` means "no preference recorded" and yields
    every column. A key present with an EMPTY list means "explicitly hidden"
    and is kept as such. The two are not interchangeable.
    """
    preferences = preferences or {}
    all_columns = CONTACT_ROW_COLUMNS[kind]
    rows = []
    for contact in contacts:
        uid = contact.get("UID") or ""
        title = contact.get("title") or ""
        for remote_row in contact.get(kind) or []:
            key = row_key(kind, remote_row)
            if not key:
                continue
            row = {
                "contact_uid": uid,
                "contact_title": title,
                # The raw token, kept alongside the translated `type` label so
                # a consumer that publishes the STORED row is not stuck with
                # the editor's language. See IPhoneDisplayRow.type_token.
                "type_token": remote_row.get("type") or "",
                # list() so each row owns its default.
                "visible_columns": list(preferences.get((uid, key), all_columns)),
            }
            for column in all_columns:
                if column == "type":
                    row["type"] = translated_type_label(kind, remote_row.get("type"))
                else:
                    row[column] = remote_row.get(column) or ""
            rows.append(row)
    return rows


def get_remote_contacts(uids):
    """Live directory payload for `uids`, in that order.

    Deliberately uncached: this is only called from the "load contacts
    informations" button, where the editor is asking for fresh data.
    """
    if not uids:
        return []
    url = "{}/@search?UID={}&fullobjects=1".format(DIRECTORY_URL, "&UID=".join(uids))
    current_lang = api.portal.get_current_language()[:2]
    if current_lang != "fr":
        url = f"{url}&translated_in_{current_lang}=1"
    json_data = get_json(url)
    if not json_data:
        return []
    index_map = {uid: index for index, uid in enumerate(uids)}
    items = [
        item for item in json_data.get("items") or [] if item.get("UID") in index_map
    ]
    return sorted(items, key=lambda item: index_map[item["UID"]])


def visible_columns_map(context, kind):
    """{(contact_uid, row_key): [column, ...]} from the stored preferences.

    A key ABSENT from the returned map means "no preference recorded" and
    yields every column at render time. A key present with an EMPTY list
    means "explicitly hidden" and drops the row. The two are NOT
    interchangeable: never normalise one into the other. A stored row whose
    `visible_columns` is None is treated as "no preference", so its key is
    deliberately left out of the map.
    """
    stored = getattr(context, f"{kind}_display", None) or []
    result = {}
    for row in stored:
        key = row_key(kind, row)
        if not key:
            continue
        columns = row.get("visible_columns")
        if columns is None:
            continue
        result[(row.get("contact_uid") or "", key)] = list(columns)
    return result


def displayed_rows(payload, context, kind):
    """Remote rows of `kind`, each with the set of columns to render.

    Returns [{"data": <remote row dict>, "columns": <set of names>}, ...].
    Rows explicitly hidden are omitted, as are rows with no usable key.

    `payload` is the LIVE directory payload: the stored `*_display` data
    columns are residue for this function and are never read here. The remote
    row dict is returned as-is and must not be mutated -- it belongs to cached
    JSON.
    """
    preferences = visible_columns_map(context, kind)
    uid = payload.get("UID") or ""
    all_columns = set(CONTACT_ROW_COLUMNS[kind])
    rows = []
    for remote_row in payload.get(kind) or []:
        key = row_key(kind, remote_row)
        if not key:
            continue
        columns = preferences.get((uid, key))
        if columns is None:
            columns = set(all_columns)
        else:
            columns = set(columns) & all_columns
            if not columns:
                continue
        rows.append({"data": remote_row, "columns": columns})
    return rows
```

- [ ] **Step 4: Run the tests**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_directory`
Expected: PASS.

- [ ] **Step 5: Checkpoint** — report the suite. Do not commit.

---

## Task 6: `COMMON/contact/forms.py` — the grid-reload mixin

**Files:**
- Create: `COMMON/src/imio/smartweb/common/contact/forms.py`
- Create: `COMMON/src/imio/smartweb/common/tests/test_contact_forms.py`

**Interfaces:**
- Consumes: `build_display_rows`, `CONTACT_ROW_COLUMNS`, `CONTACT_ROW_KEYS`, `get_remote_contacts` (Task 5); `TranslatedAjaxSelectWidget` from `imio.smartweb.common.widgets.select`.
- Produces:
  - `DISPLAY_FIELDS = ("phones_display", "mails_display", "urls_display")`
  - `KIND_BY_FIELD = {"phones_display": "phones", "mails_display": "mails", "urls_display": "urls"}`
  - `CONTACT_UIDS_SEPARATOR`
  - `ContactInformationsGridMixin` with class attribute `contact_uids_field = "related_contacts"` and methods `update()`, `_load_button_name` (property), `_reload_display_grids()`, `_submitted_contact_uids()`, `_extract_preferences(prefix, kind)`, `_write_grid(prefix, kind, rows)`. Tasks 7 and 9 subclass it and override `contact_uids_field`.

- [ ] **Step 1: Write the failing tests**

The four helpers under test only read and write `self.request.form` and
`self.prefix`, so a stub exercises them without a content type. End-to-end form
behaviour stays covered by `CORE`'s existing section-form tests and, in Task 9,
by the `EVENTS` tests.

Create `COMMON/src/imio/smartweb/common/tests/test_contact_forms.py`:

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.forms import CONTACT_UIDS_SEPARATOR
from imio.smartweb.common.contact.forms import ContactInformationsGridMixin
from imio.smartweb.common.contact.forms import DISPLAY_FIELDS
from imio.smartweb.common.contact.forms import KIND_BY_FIELD

import unittest


class _Form(ContactInformationsGridMixin):
    """Just enough of a z3c.form to exercise the request-rewriting helpers."""

    prefix = "form."

    def __init__(self, form):
        self.request = type("Request", (), {"form": form})()


class TestMixinConstants(unittest.TestCase):
    def test_display_fields(self):
        self.assertEqual(
            ("phones_display", "mails_display", "urls_display"), DISPLAY_FIELDS
        )

    def test_kind_by_field(self):
        self.assertEqual(
            {
                "phones_display": "phones",
                "mails_display": "mails",
                "urls_display": "urls",
            },
            KIND_BY_FIELD,
        )

    def test_default_uids_field_is_the_multi_valued_one(self):
        self.assertEqual("related_contacts", ContactInformationsGridMixin.contact_uids_field)


class TestSubmittedContactUids(unittest.TestCase):
    def test_separator_joined_string_is_split(self):
        form = _Form(
            {"form.widgets.related_contacts": CONTACT_UIDS_SEPARATOR.join(["a", "b"])}
        )
        self.assertEqual(["a", "b"], form._submitted_contact_uids())

    def test_a_plain_single_value_is_accepted(self):
        form = _Form({"form.widgets.related_contacts": "a"})
        self.assertEqual(["a"], form._submitted_contact_uids())

    def test_a_list_is_accepted(self):
        form = _Form({"form.widgets.related_contacts": ["a", "b"]})
        self.assertEqual(["a", "b"], form._submitted_contact_uids())

    def test_blanks_are_dropped_and_values_stripped(self):
        form = _Form({"form.widgets.related_contacts": ["  a  ", "", None]})
        self.assertEqual(["a"], form._submitted_contact_uids())

    def test_nothing_submitted_gives_an_empty_list(self):
        self.assertEqual([], _Form({})._submitted_contact_uids())

    def test_the_field_name_is_overridable(self):
        class _Single(_Form):
            contact_uids_field = "related_contact"

        form = _Single({"form.widgets.related_contact": "a"})
        self.assertEqual(["a"], form._submitted_contact_uids())


class TestExtractPreferences(unittest.TestCase):
    prefix = "form.widgets.phones_display"

    def test_checked_columns_are_read_back(self):
        form = _Form(
            {
                f"{self.prefix}.0.widgets.contact_uid": "uid-1",
                f"{self.prefix}.0.widgets.number": "081",
                f"{self.prefix}.0.widgets.visible_columns": ["number"],
            }
        )
        self.assertEqual(
            {("uid-1", "081"): ["number"]},
            form._extract_preferences(self.prefix, "phones"),
        )

    def test_nothing_submitted_for_a_rendered_row_means_all_unchecked(self):
        form = _Form(
            {
                f"{self.prefix}.0.widgets.contact_uid": "uid-1",
                f"{self.prefix}.0.widgets.number": "081",
            }
        )
        self.assertEqual(
            {("uid-1", "081"): []},
            form._extract_preferences(self.prefix, "phones"),
        )

    def test_a_single_checked_column_arrives_as_a_string(self):
        form = _Form(
            {
                f"{self.prefix}.0.widgets.contact_uid": "uid-1",
                f"{self.prefix}.0.widgets.number": "081",
                f"{self.prefix}.0.widgets.visible_columns": "number",
            }
        )
        self.assertEqual(
            {("uid-1", "081"): ["number"]},
            form._extract_preferences(self.prefix, "phones"),
        )

    def test_a_row_without_a_key_is_skipped(self):
        form = _Form(
            {
                f"{self.prefix}.0.widgets.contact_uid": "uid-1",
                f"{self.prefix}.0.widgets.number": "  ",
                f"{self.prefix}.0.widgets.visible_columns": ["number"],
            }
        )
        self.assertEqual({}, form._extract_preferences(self.prefix, "phones"))

    def test_scanning_stops_at_the_first_missing_index(self):
        form = _Form(
            {
                f"{self.prefix}.0.widgets.contact_uid": "uid-1",
                f"{self.prefix}.0.widgets.number": "081",
                # index 1 absent on purpose
                f"{self.prefix}.2.widgets.contact_uid": "uid-1",
                f"{self.prefix}.2.widgets.number": "082",
            }
        )
        self.assertEqual(
            {("uid-1", "081"): []},
            form._extract_preferences(self.prefix, "phones"),
        )


class TestWriteGrid(unittest.TestCase):
    prefix = "form.widgets.phones_display"

    def _rows(self):
        return [
            {
                "contact_uid": "uid-1",
                "contact_title": "Service culture",
                "type_token": "work",
                "label": "Accueil",
                "type": "Telephone de travail",
                "number": "081",
                "visible_columns": ["number"],
            }
        ]

    def test_stale_keys_of_the_grid_are_cleared(self):
        form = _Form({f"{self.prefix}.9.widgets.number": "stale", "other": "kept"})
        form._write_grid(self.prefix, "phones", [])
        self.assertNotIn(f"{self.prefix}.9.widgets.number", form.request.form)
        self.assertEqual("kept", form.request.form["other"])

    def test_every_column_is_written_including_the_hidden_ones(self):
        form = _Form({})
        form._write_grid(self.prefix, "phones", self._rows())
        written = form.request.form
        row = f"{self.prefix}.0.widgets"
        self.assertEqual("uid-1", written[f"{row}.contact_uid"])
        self.assertEqual("Service culture", written[f"{row}.contact_title"])
        self.assertEqual("work", written[f"{row}.type_token"])
        self.assertEqual("Accueil", written[f"{row}.label"])
        self.assertEqual("Telephone de travail", written[f"{row}.type"])
        self.assertEqual("081", written[f"{row}.number"])

    def test_visible_columns_and_its_empty_marker_are_written(self):
        form = _Form({})
        form._write_grid(self.prefix, "phones", self._rows())
        row = f"{self.prefix}.0.widgets"
        self.assertEqual(["number"], form.request.form[f"{row}.visible_columns"])
        self.assertEqual(
            "1", form.request.form[f"{row}.visible_columns-empty-marker"]
        )

    def test_the_count_marker_matches_the_row_number(self):
        form = _Form({})
        form._write_grid(self.prefix, "phones", self._rows())
        self.assertEqual("1", form.request.form[f"{self.prefix}.count"])
        form._write_grid(self.prefix, "phones", [])
        self.assertEqual("0", form.request.form[f"{self.prefix}.count"])

    def test_a_missing_column_is_written_as_an_empty_string(self):
        rows = self._rows()
        del rows[0]["label"]
        form = _Form({})
        form._write_grid(self.prefix, "phones", rows)
        self.assertEqual("", form.request.form[f"{self.prefix}.0.widgets.label"])
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_forms`
Expected: collection error, `No module named 'imio.smartweb.common.contact.forms'`.

- [ ] **Step 3: Write `forms.py`**

Create `COMMON/src/imio/smartweb/common/contact/forms.py`. This is the `CORE`
mixin, moved, with `_hide_hide_title` removed, the UID field name made
overridable, and `type_token` added to the written columns.

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.directory import build_display_rows
from imio.smartweb.common.contact.directory import CONTACT_ROW_COLUMNS
from imio.smartweb.common.contact.directory import CONTACT_ROW_KEYS
from imio.smartweb.common.contact.directory import get_remote_contacts
from imio.smartweb.common.widgets.select import TranslatedAjaxSelectWidget
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api

DISPLAY_FIELDS = ("phones_display", "mails_display", "urls_display")

# A multi-valued AjaxSelectWidget submits ONE text input holding every selected
# UID joined by this separator, not a list. Reading the raw request value
# without splitting would build a single bogus "uid1;uid2" UID.
CONTACT_UIDS_SEPARATOR = TranslatedAjaxSelectWidget.separator

KIND_BY_FIELD = {
    "phones_display": "phones",
    "mails_display": "mails",
    "urls_display": "urls",
}

# Columns written for every row on top of the kind's data columns. They are
# hidden or frozen in the form but must still be submitted: DictRow rejects a
# row whose keys are missing.
EXTRA_ROW_COLUMNS = ("contact_uid", "contact_title", "type_token")


class ContactInformationsGridMixin:
    """Repopulates the read-only contact-informations grids from the directory.

    The grids are never "filled once": they are derived from the contacts
    currently selected in `contact_uids_field`. Rather than rebuilding widgets,
    this rewrites the request BEFORE super().update(), so the normal
    request -> widget path regenerates names, ids, the .count marker and the
    patterns by construction.

    Subclasses set `contact_uids_field` to the name of their own schema field
    holding the contact UID(s): a multi-valued list (imio.smartweb.core's
    Section contact) or a single Choice (imio.events.core's Secondary contact).
    Both submission shapes are handled.
    """

    contact_uids_field = "related_contacts"

    def update(self):
        if self.request.form.get(self._load_button_name):
            self._reload_display_grids()
        super().update()

    @property
    def _load_button_name(self):
        return "{}buttons.load_contact_informations".format(self.prefix)

    def _reload_display_grids(self):
        uids = self._submitted_contact_uids()
        if not uids:
            api.portal.show_message(
                _("Please select a contact before loading its information."),
                request=self.request,
                type="info",
            )
            contacts = []
        else:
            contacts = get_remote_contacts(uids)
            if not contacts:
                # get_remote_contacts returns [] for a timeout, a non-200 and
                # an unreachable host alike (utils.get_json swallows every
                # exception), so "UIDs submitted but nothing came back" can
                # only be a failure. Rewriting the grids here would empty them
                # and destroy every recorded visible_columns preference on the
                # next save, so leave the request untouched.
                api.portal.show_message(
                    _(
                        "The contact directory could not be reached: contact "
                        "information was not loaded and nothing was changed."
                    ),
                    request=self.request,
                    type="error",
                )
                return
            api.portal.show_message(
                _("Contact information has been loaded."),
                request=self.request,
                type="info",
            )
        for field_name in DISPLAY_FIELDS:
            kind = KIND_BY_FIELD[field_name]
            prefix = "{}widgets.{}".format(self.prefix, field_name)
            preferences = self._extract_preferences(prefix, kind)
            rows = build_display_rows(kind, contacts, preferences)
            self._write_grid(prefix, kind, rows)

    def _submitted_contact_uids(self):
        """UIDs currently selected, in order.

        A multi-valued AjaxSelectWidget submits them as a single
        separator-joined string; a single-valued select submits one plain
        value; a plain list is accepted too, so the method does not depend on
        the widget in use.
        """
        uids = self.request.form.get(
            "{}widgets.{}".format(self.prefix, self.contact_uids_field)
        )
        if isinstance(uids, str):
            uids = uids.split(CONTACT_UIDS_SEPARATOR)
        return [uid.strip() for uid in uids or [] if uid and uid.strip()]

    def _extract_preferences(self, prefix, kind):
        """Checkbox state already in the request, keyed (contact_uid, row_key).

        A row whose checkbox group submitted nothing yields an EMPTY list --
        "explicitly hidden" -- not a missing key. The widget was rendered (we
        only look at indices whose contact_uid is present), so "nothing
        submitted" can only mean "everything unchecked".
        """
        form = self.request.form
        key_column = CONTACT_ROW_KEYS[kind]
        preferences = {}
        index = 0
        while "{}.{}.widgets.contact_uid".format(prefix, index) in form:
            row_prefix = "{}.{}.widgets".format(prefix, index)
            key = (form.get("{}.{}".format(row_prefix, key_column)) or "").strip()
            if key:
                columns = form.get("{}.visible_columns".format(row_prefix))
                if columns is None:
                    columns = []
                elif isinstance(columns, str):
                    columns = [columns]
                uid = form.get("{}.contact_uid".format(row_prefix)) or ""
                preferences[(uid, key)] = list(columns)
            index += 1
        return preferences

    def _write_grid(self, prefix, kind, rows):
        form = self.request.form
        for key in [key for key in form if key.startswith("{}.".format(prefix))]:
            del form[key]
        columns = EXTRA_ROW_COLUMNS + CONTACT_ROW_COLUMNS[kind]
        for index, row in enumerate(rows):
            row_prefix = "{}.{}.widgets".format(prefix, index)
            for column in columns:
                form["{}.{}".format(row_prefix, column)] = row.get(column) or ""
            form["{}.visible_columns".format(row_prefix)] = list(row["visible_columns"])
            form["{}.visible_columns-empty-marker".format(row_prefix)] = "1"
        form["{}.count".format(prefix)] = str(len(rows))
```

- [ ] **Step 4: Run the tests**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test -m imio.smartweb.common.tests.test_contact_forms`
Expected: PASS.

- [ ] **Step 5: Run the whole `COMMON` suite**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test`
Expected: PASS. The shared layer is complete and self-contained at this point.

- [ ] **Step 6: Checkpoint** — report the full suite. Do not commit.

---

## Task 7: Point `imio.smartweb.core` at the shared layer

The gate on this task is that `CORE`'s existing section tests pass
**unmodified**. They are the proof the extraction preserved behaviour.

**Files:**
- Modify: `CORE/src/imio/smartweb/core/contents/sections/contact/content.py`
- Modify: `CORE/src/imio/smartweb/core/contents/sections/contact/utils.py`
- Modify: `CORE/src/imio/smartweb/core/contents/sections/contact/forms.py`

**Interfaces:**
- Consumes: everything produced by Tasks 3, 5 and 6.
- Produces: `ISectionContact` unchanged in name and field set; `ContactProperties` unchanged in its public surface (its templates call `displayed_rows(kind)` and `translated_type(kind, token)` as **methods**, so those signatures must not change).

- [ ] **Step 1: Run the section tests to record the green baseline**

Run: `cd /home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core && ./bin/test -m imio.smartweb.core.tests.test_section_contact -m imio.smartweb.core.tests.test_section_contact_forms`
Expected: PASS. Note the test count — it must be identical at the end.

- [ ] **Step 2: Rewrite `content.py` to inherit the shared grids**

In `CORE/src/imio/smartweb/core/contents/sections/contact/content.py`:
delete the classes `IPhoneDisplayRow`, `IMailDisplayRow`, `IUrlDisplayRow`
(lines ~68-159), delete the `model.fieldset("contact_informations", …)` block
and the three `phones_display` / `mails_display` / `urls_display` field
declarations with their `directives.widget` calls (lines ~189-250), and change
the class statement to:

```python
class ISectionContact(ISection, IContactInformationsGrids):
    """Marker interface and Dexterity Python Schema for SectionContact"""
```

Imports: add
```python
from imio.smartweb.common.contact.rows import IContactInformationsGrids
```
and remove the now-unused ones: `DataGridFieldFactory`, `DictRow`,
`FrozenLabelTextFieldWidget`, and `Interface`. Keep `CheckBoxFieldWidget` — it
is still used by `visible_blocks`. Keep `model` — still used by the `layout`
fieldset.

- [ ] **Step 3: Rewrite `utils.py` to import the shared helpers**

In `CORE/src/imio/smartweb/core/contents/sections/contact/utils.py`: delete the
module-level `CONTACT_TYPE_LABELS`, `CONTACT_ROW_KEYS`, `CONTACT_ROW_COLUMNS`,
`translated_type_label`, `row_key`, `build_display_rows` and
`get_remote_contacts`, and replace the `ContactProperties` methods
`translated_type`, `visible_columns_map` and `displayed_rows` with delegations.

Add these imports:
```python
from imio.smartweb.common.contact.directory import build_display_rows  # noqa: F401
from imio.smartweb.common.contact.directory import CONTACT_ROW_COLUMNS  # noqa: F401
from imio.smartweb.common.contact.directory import CONTACT_ROW_KEYS  # noqa: F401
from imio.smartweb.common.contact.directory import displayed_rows as _displayed_rows
from imio.smartweb.common.contact.directory import get_remote_contacts  # noqa: F401
from imio.smartweb.common.contact.directory import row_key  # noqa: F401
from imio.smartweb.common.contact.directory import translated_type_label
from imio.smartweb.common.contact.directory import visible_columns_map as _visible_columns_map
```

The `# noqa: F401` re-exports keep `from …contact.utils import build_display_rows`
working for `forms.py` and for any test that imports them from here — check with
`grep -rn "sections.contact.utils import" src/` and keep whatever is imported.

Replace the three methods with:
```python
    def translated_type(self, kind, token):
        """Human label of a remote `type` token. See translated_type_label."""
        return translated_type_label(kind, token)

    def visible_columns_map(self, kind):
        """See imio.smartweb.common.contact.directory.visible_columns_map."""
        return _visible_columns_map(self.context, kind)

    def displayed_rows(self, kind):
        """See imio.smartweb.common.contact.directory.displayed_rows."""
        return _displayed_rows(self.contact, self.context, kind)
```

Keep every other `ContactProperties` member exactly as it is.

- [ ] **Step 4: Rewrite `forms.py` to subclass the shared mixin**

In `CORE/src/imio/smartweb/core/contents/sections/contact/forms.py`: delete the
whole local `ContactInformationsGridMixin` class, the `DISPLAY_FIELDS`,
`RELATED_CONTACTS_SEPARATOR` and `KIND_BY_FIELD` constants, and the
`build_display_rows` / `CONTACT_ROW_COLUMNS` / `CONTACT_ROW_KEYS` /
`get_remote_contacts` imports. Add:

```python
from imio.smartweb.common.contact.forms import ContactInformationsGridMixin
```

and define the section-specific subclass:

```python
class SectionContactGridMixin(ContactInformationsGridMixin):
    """The section's own bits: `related_contacts` and the hidden hide_title.

    `hide_title` is hidden after the widgets exist, which both concrete forms
    need and neither may forget. It does not exist outside a Section, which is
    why it is not in the shared mixin.
    """

    contact_uids_field = "related_contacts"

    def update(self):
        super().update()
        self._hide_hide_title()

    def _hide_hide_title(self):
        # We hide hide_title field so no one can change the value for contact
        # and set True value (single checkbox)
        for group in self.groups:
            if group.__name__ == "layout":
                group.widgets["hide_title"].mode = HIDDEN_MODE
                group.widgets["hide_title"].value = ["selected"]
```

Then change both concrete forms to use it:
```python
class ContactCustomAddForm(SectionContactGridMixin, CustomAddForm):
```
```python
class ContactCustomEditForm(SectionContactGridMixin, SmartwebCustomEditForm):
```
Leave their `buttons` / `handlers` copies and their button handlers untouched.

- [ ] **Step 5: Run the section tests — the gate**

Run: `cd /home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core && ./bin/test -m imio.smartweb.core.tests.test_section_contact -m imio.smartweb.core.tests.test_section_contact_forms`
Expected: PASS, **same test count as Step 1, with no test file modified**. If a
test needs editing to pass, the extraction changed behaviour: stop and report
rather than adjusting the test.

- [ ] **Step 6: Run the whole `CORE` suite**

Run: `cd /home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core && ./bin/test`
Expected: PASS. This catches anything else that imported the moved names.

- [ ] **Step 7: Checkpoint** — report both runs and the test counts. Do not commit.

---

## Task 8: The `imio.events.SecondaryContact` type

**Files:**
- Rewrite: `EVENTS/src/imio/events/core/contents/secondary_contact/__init__.py` (empty)
- Rewrite: `EVENTS/src/imio/events/core/contents/secondary_contact/content.py`
- Rewrite: `EVENTS/src/imio/events/core/contents/secondary_contact/configure.zcml` (empty `<configure/>` for now; Task 9 fills it)
- Delete: `EVENTS/src/imio/events/core/contents/secondary_contact/utils.py`, `view.py`, `view.pt`, `macros.pt`
- Delete: `EVENTS/src/imio/events/core/contents/contact/` (contains only untracked `__pycache__`)
- Modify: `EVENTS/src/imio/events/core/contents/__init__.py`
- Rewrite: `EVENTS/src/imio/events/core/profiles/default/types/imio.events.SecondaryContact.xml`
- Modify: `EVENTS/src/imio/events/core/profiles/default/types.xml`
- Modify: `EVENTS/src/imio/events/core/profiles/default/workflows.xml`
- Test: `EVENTS/src/imio/events/core/tests/test_secondary_contact.py`

**Interfaces:**
- Consumes: `IContactInformationsGrids` (Task 3).
- Produces: `imio.events.core.contents.ISecondaryContact` and
  `imio.events.core.contents.SecondaryContact`; FTI `imio.events.SecondaryContact`
  with `klass=imio.events.core.contents.SecondaryContact` and
  `schema=imio.events.core.contents.ISecondaryContact`; fields `title`
  (optional `TextLine`), `related_contact` (`Choice` on
  `imio.events.vocabulary.RemoteDirectoryContact`), plus the three inherited grids.

- [ ] **Step 1: Write the failing test**

Create `EVENTS/src/imio/events/core/tests/test_secondary_contact.py`:

```python
# -*- coding: utf-8 -*-

from imio.events.core.contents import ISecondaryContact
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class TestSecondaryContact(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="agenda",
        )
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )

    def test_ct_secondary_contact_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.SecondaryContact")
        self.assertTrue(fti)

    def test_ct_secondary_contact_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.SecondaryContact")
        self.assertEqual(ISecondaryContact, fti.lookupSchema())

    def test_ct_secondary_contact_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.SecondaryContact")
        obj = createObject(fti.factory)
        self.assertTrue(
            ISecondaryContact.providedBy(obj),
            "ISecondaryContact not provided by {0}!".format(obj),
        )

    def test_ct_secondary_contact_globally_not_addable(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.SecondaryContact")
        self.assertFalse(fti.global_allow)

    def test_ct_secondary_contact_addable_in_event(self):
        obj = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        self.assertTrue(ISecondaryContact.providedBy(obj))

    def test_ct_secondary_contact_addable_several_times(self):
        api.content.create(
            container=self.event, type="imio.events.SecondaryContact", id="contact-1"
        )
        api.content.create(
            container=self.event, type="imio.events.SecondaryContact", id="contact-2"
        )
        children = self.event.listFolderContents(
            contentFilter={"portal_type": "imio.events.SecondaryContact"}
        )
        self.assertEqual(2, len(children))

    def test_ct_secondary_contact_not_addable_in_agenda(self):
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.agenda,
                type="imio.events.SecondaryContact",
                id="contact-1",
            )

    def test_ct_secondary_contact_is_a_leaf(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.SecondaryContact")
        self.assertTrue(fti.filter_content_types)
        self.assertEqual((), tuple(fti.allowed_content_types))

    def test_ct_secondary_contact_add_permission(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.SecondaryContact")
        self.assertEqual("imio.events.core.AddEvent", fti.add_permission)

    def test_event_allows_secondary_contact(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        self.assertIn("imio.events.SecondaryContact", fti.allowed_content_types)

    def test_related_contact_is_single_valued_on_the_events_vocabulary(self):
        field = ISecondaryContact["related_contact"]
        self.assertEqual(
            "imio.events.vocabulary.RemoteDirectoryContact", field.vocabularyName
        )
        self.assertTrue(field.required)

    def test_title_is_optional_and_an_untitled_object_is_valid(self):
        self.assertFalse(ISecondaryContact["title"].required)
        obj = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-no-title",
        )
        self.assertFalse(obj.title)

    def test_no_description_field(self):
        self.assertNotIn("description", ISecondaryContact.names(all=True))

    def test_the_three_grids_are_present(self):
        for name in ("phones_display", "mails_display", "urls_display"):
            self.assertIn(name, ISecondaryContact.names(all=True))

    def test_workflow_chain_is_one_state(self):
        chain = api.portal.get_tool("portal_workflow").getChainFor(
            "imio.events.SecondaryContact"
        )
        self.assertEqual(("one_state_workflow",), tuple(chain))
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact`
Expected: collection error — `ImportError: cannot import name 'ISecondaryContact'`.

- [ ] **Step 3: Remove the WIP files that do not belong**

```bash
cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core/src/imio/events/core/contents
rm -f secondary_contact/utils.py secondary_contact/view.py \
      secondary_contact/view.pt secondary_contact/macros.pt
rm -rf secondary_contact/__pycache__ contact
```
`secondary_contact/utils.py` is superseded by `COMMON`; the view modules
contradict the REST-only decision; `contact/` holds nothing but stale bytecode
from the abandoned `imio.events.Contact` attempt. Confirm with
`ls -la secondary_contact/ && ls -d contact 2>&1` — `contact` must be gone.

- [ ] **Step 4: Write `content.py`**

Replace `EVENTS/src/imio/events/core/contents/secondary_contact/content.py`
entirely with:

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.rows import IContactInformationsGrids
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Item
from zope import schema
from zope.interface import implementer


class ISecondaryContact(IContactInformationsGrids):
    """Marker interface and Dexterity Python Schema for SecondaryContact

    One object references ONE directory contact. Several of them can be added
    to an Event: the multiplicity is the number of objects, not a multi-valued
    field. That keeps `title` meaningful (it labels one contact, e.g.
    "Reservations") and the REST payload unambiguous.

    The three inherited datagrids hold a SNAPSHOT of the contact's phones,
    e-mails and urls. Unlike imio.smartweb.core's Section contact, where the
    stored data columns are residue and the render re-reads the directory, here
    they ARE the published data: an event has a temporality and must show the
    contact as it was for that event.
    """

    # Declared here rather than through plone.basic, which would make the title
    # required and also expose a description field. plone.namefromtitle derives
    # the id when a title is given and falls back to the portal type when not.
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
            "You can retrieve information from a contact record that already "
            "exists in your directory"
        ),
        source="imio.events.vocabulary.RemoteDirectoryContact",
        required=True,
    )


@implementer(ISecondaryContact)
class SecondaryContact(Item):
    """SecondaryContact class"""
```

Note: `Item`, not `Container` — a SecondaryContact holds no sub-content.

- [ ] **Step 5: Fix the package exports and the ZCML include**

`EVENTS/src/imio/events/core/contents/__init__.py` — the WIP line re-imports
`IFolder, Folder` from the new module, which is wrong. The file must read:

```python
from .agenda.content import IAgenda, Agenda  # NOQA
from .entity.content import IEntity, Entity  # NOQA
from .event.content import IEvent, Event  # NOQA
from .folder.content import IFolder, Folder  # NOQA
from .secondary_contact.content import ISecondaryContact, SecondaryContact  # NOQA
```

(with a trailing newline — the WIP file has none).

`EVENTS/src/imio/events/core/contents/secondary_contact/configure.zcml` — for
now, an empty configuration; Task 9 fills it:

```xml
<configure xmlns="http://namespaces.zope.org/zope">

</configure>
```

The `<include package=".secondary_contact" />` in
`contents/configure.zcml` is already present from the WIP.

- [ ] **Step 6: Write the FTI**

Replace `EVENTS/src/imio/events/core/profiles/default/types/imio.events.SecondaryContact.xml`
entirely. Open `EVENTS/src/imio/events/core/profiles/default/types/imio.events.Folder.xml`
first and mirror its standard property set (`add_view_expr`, `default_view`,
`view_methods`, `link_target`, etc.) so nothing standard is omitted; then set
the type-specific properties:

```xml
<?xml version="1.0"?>
<object xmlns:i18n="http://xml.zope.org/namespaces/i18n"
    name="imio.events.SecondaryContact"
    meta_type="Dexterity FTI"
    i18n:domain="imio.smartweb">

  <!-- Basic properties -->
  <property
      i18n:translate=""
      name="title">Secondary contact</property>
  <property
      i18n:translate=""
      name="description">Secondary contact for an event</property>

  <property name="icon_expr">string:person-plus</property>

  <!-- Hierarchy control: leaf type, only inside an Event -->
  <property name="global_allow">False</property>
  <property name="filter_content_types">True</property>
  <property name="allowed_content_types"/>

  <!-- Schema, class and security -->
  <!-- if we can add an event, we can add its secondary contacts -->
  <property name="add_permission">imio.events.core.AddEvent</property>
  <property name="klass">imio.events.core.contents.SecondaryContact</property>
  <property name="schema">imio.events.core.contents.ISecondaryContact</property>

  <!-- Enabled behaviors -->
  <property name="behaviors" purge="false">
    <element value="plone.namefromtitle"/>
    <element value="plone.shortname"/>
    <element value="plone.locking"/>
    <element value="plone.excludefromnavigation"/>
  </property>

</object>
```

- [ ] **Step 7: Register the type and bind its workflow**

`EVENTS/src/imio/events/core/profiles/default/types.xml` — add, keeping
alphabetical order:
```xml
  <object meta_type="Dexterity FTI" name="imio.events.SecondaryContact"/>
```

`EVENTS/src/imio/events/core/profiles/default/workflows.xml` — add inside
`<bindings>`:
```xml
    <type type_id="imio.events.SecondaryContact">
      <bound-workflow workflow_id="one_state_workflow" />
    </type>
```

This matters beyond tidiness. Without an explicit binding the type falls on the
site's default chain, is created `private`, and `listFolderContents` would hide
it from the anonymous downstream site — the REST payload would silently come
back empty. `one_state_workflow` is what `imio.events.Agenda` and
`imio.events.Folder` already use.

`imio.events.SecondaryContact` is already in the Event's
`allowed_content_types` from the WIP diff; verify it is still there:
```bash
grep -n "SecondaryContact" src/imio/events/core/profiles/default/types/imio.events.Event.xml
```

- [ ] **Step 8: Run the test**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact`
Expected: PASS.

- [ ] **Step 9: Checkpoint** — report the suite. Do not commit.

---

## Task 9: The add and edit forms with the "Load contact information" button

**Files:**
- Rewrite: `EVENTS/src/imio/events/core/contents/secondary_contact/forms.py`
- Rewrite: `EVENTS/src/imio/events/core/contents/secondary_contact/configure.zcml`
- Test: `EVENTS/src/imio/events/core/tests/test_secondary_contact_forms.py`

**Interfaces:**
- Consumes: `ContactInformationsGridMixin` (Task 6); `ISecondaryContact` (Task 8).
- Produces: `SecondaryContactGridMixin` (`contact_uids_field = "related_contact"`), `SecondaryContactCustomAddForm`, `SecondaryContactCustomAddView`, `SecondaryContactCustomEditForm`, `SecondaryContactCustomEditView`.

- [ ] **Step 1: Write the failing test**

Create `EVENTS/src/imio/events/core/tests/test_secondary_contact_forms.py`:

```python
# -*- coding: utf-8 -*-

from imio.events.core.contents.secondary_contact.forms import (
    SecondaryContactCustomAddForm,
)
from imio.events.core.contents.secondary_contact.forms import (
    SecondaryContactCustomEditForm,
)
from imio.events.core.contents.secondary_contact.forms import SecondaryContactGridMixin
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest import mock
from zope.publisher.browser import TestRequest

import unittest


DIRECTORY_PAYLOAD = {
    "items": [
        {
            "UID": "uid-1",
            "title": "Service culture",
            "phones": [{"label": "Accueil", "type": "work", "number": "081 12 34 56"}],
            "mails": [
                {"label": "", "type": "work", "mail_address": "culture@ville.be"}
            ],
            "urls": [{"type": "website", "url": "https://ville.be"}],
        }
    ]
}


class TestSecondaryContactForms(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event"
        )

    def test_mixin_reads_the_single_valued_field(self):
        self.assertEqual(
            "related_contact", SecondaryContactGridMixin.contact_uids_field
        )

    def test_add_form_portal_type(self):
        self.assertEqual(
            "imio.events.SecondaryContact", SecondaryContactCustomAddForm.portal_type
        )

    def test_add_form_keeps_the_base_save_and_cancel_buttons(self):
        names = list(SecondaryContactCustomAddForm.buttons)
        self.assertIn("load_contact_informations", names)
        self.assertIn("save", names)
        self.assertIn("cancel", names)

    def test_add_form_keeps_the_base_handlers(self):
        # A missing handler is the silent failure mode: Save would re-render
        # the form without saving anything.
        self.assertTrue(len(SecondaryContactCustomAddForm.handlers))

    def test_edit_form_keeps_the_base_save_and_cancel_buttons(self):
        names = list(SecondaryContactCustomEditForm.buttons)
        self.assertIn("load_contact_informations", names)
        self.assertIn("save", names)
        self.assertIn("cancel", names)

    def test_pressing_load_fills_the_grids_from_the_directory(self):
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        request = TestRequest(
            form={
                "form.buttons.load_contact_informations": "Load contact information",
                "form.widgets.related_contact": "uid-1",
            }
        )
        form = SecondaryContactCustomEditForm(contact, request)
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=DIRECTORY_PAYLOAD,
        ):
            form._reload_display_grids()
        written = request.form
        self.assertEqual("1", written["form.widgets.phones_display.count"])
        self.assertEqual(
            "081 12 34 56", written["form.widgets.phones_display.0.widgets.number"]
        )
        self.assertEqual(
            "work", written["form.widgets.phones_display.0.widgets.type_token"]
        )
        self.assertEqual("1", written["form.widgets.mails_display.count"])
        self.assertEqual("1", written["form.widgets.urls_display.count"])

    def test_pressing_load_without_a_contact_empties_the_grids(self):
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        request = TestRequest(
            form={"form.buttons.load_contact_informations": "Load contact information"}
        )
        form = SecondaryContactCustomEditForm(contact, request)
        form._reload_display_grids()
        self.assertEqual("0", request.form["form.widgets.phones_display.count"])

    def test_a_directory_failure_leaves_the_request_untouched(self):
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        request = TestRequest(
            form={
                "form.buttons.load_contact_informations": "Load contact information",
                "form.widgets.related_contact": "uid-1",
            }
        )
        form = SecondaryContactCustomEditForm(contact, request)
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json", return_value=None
        ):
            form._reload_display_grids()
        # Nothing written: rewriting the grids would destroy every recorded
        # visible_columns preference on the next save.
        self.assertNotIn("form.widgets.phones_display.count", request.form)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact_forms`
Expected: collection error — `cannot import name 'SecondaryContactCustomAddForm'`.

- [ ] **Step 3: Write `forms.py`**

Replace `EVENTS/src/imio/events/core/contents/secondary_contact/forms.py`
entirely with:

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.forms import ContactInformationsGridMixin
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.z3cform import layout
from z3c.form import button


class SecondaryContactGridMixin(ContactInformationsGridMixin):
    """A Secondary contact references ONE contact, in `related_contact`.

    No `hide_title` handling here: that field belongs to imio.smartweb.core's
    Section base and does not exist on this type.
    """

    contact_uids_field = "related_contact"


class SecondaryContactCustomAddForm(SecondaryContactGridMixin, DefaultAddForm):
    portal_type = "imio.events.SecondaryContact"

    # Both MUST be copied before the decorator runs: @buttonAndHandler does a
    # setdefault on the `buttons` AND on the `handlers` name of the class body
    # being defined. Without the copies it would create fresh, empty managers
    # that shadow the base ones -- the form would lose the Save / Cancel
    # buttons (buttons) and, more silently, their handlers (handlers), so
    # pressing Save would render the form again without saving anything.
    buttons = DefaultAddForm.buttons.copy()
    handlers = DefaultAddForm.handlers.copy()

    @button.buttonAndHandler(
        _("Load contact information"), name="load_contact_informations"
    )
    def handleLoadContactInformations(self, action):
        """No-op: the grids were already rebuilt in update()."""


class SecondaryContactCustomAddView(DefaultAddView):
    form = SecondaryContactCustomAddForm


class SecondaryContactCustomEditForm(SecondaryContactGridMixin, DefaultEditForm):
    # See SecondaryContactCustomAddForm for why both managers are copied here.
    buttons = DefaultEditForm.buttons.copy()
    handlers = DefaultEditForm.handlers.copy()

    @button.buttonAndHandler(
        _("Load contact information"), name="load_contact_informations"
    )
    def handleLoadContactInformations(self, action):
        """No-op: the grids were already rebuilt in update()."""


SecondaryContactCustomEditView = layout.wrap_form(SecondaryContactCustomEditForm)
```

- [ ] **Step 4: Register the forms in ZCML**

Replace `EVENTS/src/imio/events/core/contents/secondary_contact/configure.zcml`
entirely with:

```xml
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:browser="http://namespaces.zope.org/browser">

  <!-- Custom add view and form - invoked from ++add++ traverser -->
  <adapter
      for="Products.CMFCore.interfaces.IFolderish
           imio.events.core.interfaces.IImioEventsCoreLayer
           plone.dexterity.interfaces.IDexterityFTI"
      provides="zope.publisher.interfaces.browser.IBrowserPage"
      factory=".forms.SecondaryContactCustomAddView"
      name="imio.events.SecondaryContact"
      />
  <class class=".forms.SecondaryContactCustomAddView">
      <require
          permission="cmf.AddPortalContent"
          interface="zope.publisher.interfaces.browser.IBrowserPage"
          />
  </class>

  <browser:page
      for="imio.events.core.contents.ISecondaryContact"
      name="edit"
      class=".forms.SecondaryContactCustomEditView"
      permission="cmf.ModifyPortalContent"
      layer="imio.events.core.interfaces.IImioEventsCoreLayer"
      />

</configure>
```

No `view` page: the default Dexterity view is used, per the REST-only decision.

- [ ] **Step 5: Run the tests**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact_forms`
Expected: PASS.

- [ ] **Step 6: Re-run Task 8's tests to catch ZCML regressions**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact`
Expected: PASS.

- [ ] **Step 7: Checkpoint** — report both suites. Do not commit.

---

## Task 10: Serialize a Secondary contact

**Files:**
- Create: `EVENTS/src/imio/events/core/contents/secondary_contact/serializer.py`
- Test: `EVENTS/src/imio/events/core/tests/test_secondary_contact_serializer.py`

**Interfaces:**
- Consumes: `CONTACT_ROW_COLUMNS` (Task 5); `ISecondaryContact` (Task 8).
- Produces:
  - `kept_rows(obj, kind: str) -> list[dict]`
  - `serialize_secondary_contact(obj) -> dict | None`
  - `get_secondary_contacts(event) -> list[dict]`
  Tasks 11 and 12 call `get_secondary_contacts`.

- [ ] **Step 1: Write the failing test**

Create `EVENTS/src/imio/events/core/tests/test_secondary_contact_serializer.py`:

```python
# -*- coding: utf-8 -*-

from imio.events.core.contents.secondary_contact.serializer import (
    get_secondary_contacts,
)
from imio.events.core.contents.secondary_contact.serializer import kept_rows
from imio.events.core.contents.secondary_contact.serializer import (
    serialize_secondary_contact,
)
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


def phone_row(number, visible_columns, label="Accueil", token="work"):
    return {
        "contact_uid": "uid-1",
        "contact_title": "Service culture",
        "type_token": token,
        "label": label,
        "type": "Telephone de travail",
        "number": number,
        "visible_columns": visible_columns,
    }


class TestKeptRows(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event"
        )

    def _contact(self, contact_id="contact-1", **kwargs):
        return api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id=contact_id,
            **kwargs,
        )

    def test_no_stored_rows_gives_no_rows(self):
        self.assertEqual([], kept_rows(self._contact(), "phones"))

    def test_none_visible_columns_yields_every_column(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", None)]
        self.assertEqual(
            [{"label": "Accueil", "type": "work", "number": "081"}],
            kept_rows(contact, "phones"),
        )

    def test_empty_visible_columns_drops_the_row(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", [])]
        self.assertEqual([], kept_rows(contact, "phones"))

    def test_only_the_retained_columns_are_emitted(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["number"])]
        self.assertEqual([{"number": "081"}], kept_rows(contact, "phones"))

    def test_the_type_column_is_emitted_as_the_raw_token(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["type"], token="cell")]
        self.assertEqual([{"type": "cell"}], kept_rows(contact, "phones"))

    def test_columns_are_emitted_in_the_canonical_order(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["number", "label", "type"])]
        self.assertEqual(
            ["label", "type", "number"], list(kept_rows(contact, "phones")[0])
        )

    def test_unknown_columns_are_ignored(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["number", "bogus"])]
        self.assertEqual([{"number": "081"}], kept_rows(contact, "phones"))

    def test_a_row_without_its_key_column_is_dropped(self):
        contact = self._contact()
        contact.phones_display = [phone_row("", None)]
        self.assertEqual([], kept_rows(contact, "phones"))


class TestSerializeSecondaryContact(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event"
        )

    def _contact(self, contact_id="contact-1"):
        return api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id=contact_id,
        )

    def test_the_full_shape(self):
        contact = self._contact()
        contact.title = "Reservations"
        contact.related_contact = "uid-1"
        contact.phones_display = [phone_row("081", ["number"])]
        contact.mails_display = [
            {
                "contact_uid": "uid-1",
                "contact_title": "Service culture",
                "type_token": "work",
                "label": "",
                "type": "Email de travail",
                "mail_address": "resa@ville.be",
                "visible_columns": ["mail_address"],
            }
        ]
        contact.urls_display = []
        self.assertEqual(
            {
                "uid": "uid-1",
                "title": "Reservations",
                "phones": [{"number": "081"}],
                "mails": [{"mail_address": "resa@ville.be"}],
                "urls": [],
            },
            serialize_secondary_contact(contact),
        )

    def test_a_missing_title_becomes_an_empty_string(self):
        contact = self._contact()
        contact.related_contact = "uid-1"
        self.assertEqual("", serialize_secondary_contact(contact)["title"])

    def test_a_contact_without_a_related_contact_is_not_serialized(self):
        # related_contact is required, so this can only be legacy data; the
        # payload must never carry an entry with a null uid.
        self.assertIsNone(serialize_secondary_contact(self._contact()))


class TestGetSecondaryContacts(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event"
        )

    def test_an_event_without_children_gives_an_empty_list(self):
        self.assertEqual([], get_secondary_contacts(self.event))

    def test_children_are_returned_in_folder_order(self):
        for index, uid in enumerate(["uid-a", "uid-b"], start=1):
            contact = api.content.create(
                container=self.event,
                type="imio.events.SecondaryContact",
                id="contact-{}".format(index),
            )
            contact.related_contact = uid
        self.assertEqual(
            ["uid-a", "uid-b"],
            [item["uid"] for item in get_secondary_contacts(self.event)],
        )

    def test_other_child_types_are_ignored(self):
        api.content.create(container=self.event, type="Image", id="an-image")
        self.assertEqual([], get_secondary_contacts(self.event))

    def test_a_child_without_a_related_contact_is_skipped(self):
        api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        self.assertEqual([], get_secondary_contacts(self.event))
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact_serializer`
Expected: collection error — no module `…secondary_contact.serializer`.

- [ ] **Step 3: Write `serializer.py`**

Create `EVENTS/src/imio/events/core/contents/secondary_contact/serializer.py`:

```python
# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.directory import CONTACT_ROW_COLUMNS
from imio.smartweb.common.contact.directory import row_key

PORTAL_TYPE = "imio.events.SecondaryContact"


def kept_rows(obj, kind):
    """Stored rows of `kind`, reduced to the columns the editor retained.

    Reads the STORED snapshot, not the live directory: an event must publish
    the contact as it was for that event. See ISecondaryContact.

    `visible_columns` semantics, which must not be collapsed:
      * None    -> no preference recorded -> every column
      * []      -> explicitly hidden      -> row dropped
    `type` is emitted as the RAW token (from `type_token`), never as the
    translated label, so a consumer in any language can translate it itself.
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
```

- [ ] **Step 4: Run the tests**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact_serializer`
Expected: PASS.

- [ ] **Step 5: Checkpoint** — report the suite. Do not commit.

---

## Task 11: Publish through `@events` — indexer, metadata column, full serializer

**Files:**
- Modify: `EVENTS/src/imio/events/core/indexers.py`
- Modify: `EVENTS/src/imio/events/core/indexers.zcml`
- Modify: `EVENTS/src/imio/events/core/profiles/default/catalog.xml`
- Modify: `EVENTS/src/imio/events/core/contents/event/serializer.py`
- Modify: `EVENTS/src/imio/events/core/rest/endpoint.py:96-107`
- Test: `EVENTS/src/imio/events/core/tests/test_secondary_contact_rest.py`

**Interfaces:**
- Consumes: `get_secondary_contacts(event)` (Task 10).
- Produces: catalog metadata column `secondary_contacts`; the key
  `result["secondary_contacts"]` in the Event's full JSON.

- [ ] **Step 1: Write the failing test**

Create `EVENTS/src/imio/events/core/tests/test_secondary_contact_rest.py`:

```python
# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter

import unittest


class TestSecondaryContactRest(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event"
        )

    def _add_contact(self, contact_id, uid, title=""):
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id=contact_id,
        )
        contact.related_contact = uid
        contact.title = title
        contact.phones_display = [
            {
                "contact_uid": uid,
                "contact_title": "Service culture",
                "type_token": "work",
                "label": "Accueil",
                "type": "Telephone de travail",
                "number": "081 12 34 56",
                "visible_columns": ["number"],
            }
        ]
        contact.reindexObject()
        self.event.reindexObject()
        return contact

    def test_full_serializer_always_emits_the_key(self):
        result = getMultiAdapter((self.event, self.request), ISerializeToJson)()
        self.assertEqual([], result["secondary_contacts"])

    def test_full_serializer_emits_the_snapshot(self):
        self._add_contact("contact-1", "uid-1", title="Reservations")
        result = getMultiAdapter((self.event, self.request), ISerializeToJson)()
        self.assertEqual(
            [
                {
                    "uid": "uid-1",
                    "title": "Reservations",
                    "phones": [{"number": "081 12 34 56"}],
                    "mails": [],
                    "urls": [],
                }
            ],
            result["secondary_contacts"],
        )

    def test_the_catalog_metadata_column_exists(self):
        catalog = api.portal.get_tool("portal_catalog")
        self.assertIn("secondary_contacts", catalog.schema())

    def test_the_catalog_metadata_carries_the_snapshot(self):
        self._add_contact("contact-1", "uid-1", title="Reservations")
        brain = api.content.find(UID=self.event.UID())[0]
        self.assertEqual(
            [
                {
                    "uid": "uid-1",
                    "title": "Reservations",
                    "phones": [{"number": "081 12 34 56"}],
                    "mails": [],
                    "urls": [],
                }
            ],
            brain.secondary_contacts,
        )

    def test_the_metadata_of_an_event_without_children_is_an_empty_list(self):
        brain = api.content.find(UID=self.event.UID())[0]
        self.assertEqual([], brain.secondary_contacts)

    def test_the_endpoint_requests_the_metadata_field(self):
        from imio.events.core.rest.endpoint import EventsEndpointHandlerGet  # noqa

        # The endpoint appends the field name to metadata_fields; assert on the
        # source of truth rather than on a full search round-trip.
        import inspect

        source = inspect.getsource(EventsEndpointHandlerGet._perform_search)
        self.assertIn('"secondary_contacts"', source)
```

Before running: open `EVENTS/src/imio/events/core/rest/endpoint.py` and check
the real handler class name; if it is not `EventsEndpointHandlerGet`, fix the
import and the test name accordingly. Also confirm
`IMIO_EVENTS_CORE_FUNCTIONAL_TESTING` is the correct name in
`EVENTS/src/imio/events/core/testing.py`.

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact_rest`
Expected: FAIL — `KeyError: 'secondary_contacts'` and the missing column.

- [ ] **Step 3: Add the indexer**

Append to `EVENTS/src/imio/events/core/indexers.py`:

```python
@indexer(IEvent)
def secondary_contacts(obj):
    """The event's Secondary contacts, as a catalog METADATA column.

    @events serializes full objects only when the query carries a UID; the
    ordinary listing path builds summaries from catalog metadata, so the
    snapshot has to travel through the catalog to reach downstream sites.

    Returns [] rather than raising AttributeError: an absent value would be
    stored as Missing.Value, and consumers must always get a list.
    """
    return get_secondary_contacts(obj)
```

and add the import at the top, in alphabetical position among the
`imio.events.core` imports:
```python
from imio.events.core.contents.secondary_contact.serializer import (
    get_secondary_contacts,
)
```

Register it in `EVENTS/src/imio/events/core/indexers.zcml`, inside
`<configure>`:
```xml
  <adapter
      name="secondary_contacts"
      factory=".indexers.secondary_contacts"
      />
```

- [ ] **Step 4: Declare the metadata column**

Add to `EVENTS/src/imio/events/core/profiles/default/catalog.xml`, after the
existing `<column value="event_sponsors"/>`:
```xml
  <column value="secondary_contacts"/>
```

- [ ] **Step 5: Emit the key from the full serializer**

In `EVENTS/src/imio/events/core/contents/event/serializer.py`, inside
`SerializeEventToJson.__call__`, immediately after the two `first_start` /
`first_end` assignments, add:
```python
        result["secondary_contacts"] = get_secondary_contacts(self.context)
```
and add the import:
```python
from imio.events.core.contents.secondary_contact.serializer import (
    get_secondary_contacts,
)
```

- [ ] **Step 6: Ask the endpoint for the metadata field**

In `EVENTS/src/imio/events/core/rest/endpoint.py`, in the
`self.request.form["metadata_fields"] += [...]` list (around lines 96-107), add
`"secondary_contacts"` after `"event_sponsors"`. Do not add any resolution step
to `expand_occurences`: unlike sponsors, the snapshot is already complete.

- [ ] **Step 7: Run the tests**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact_rest`
Expected: PASS.

- [ ] **Step 8: Run the existing REST suites for regressions**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_rest -m imio.events.core.tests.test_search_endpoint -m imio.events.core.tests.test_indexes`
Expected: PASS.

- [ ] **Step 9: Checkpoint** — report all suites. Do not commit.

---

## Task 12: Keep the metadata fresh when a child changes

The metadata lives on the Event; the data lives in its children. Without this,
editing a Secondary contact leaves a stale snapshot in the catalog and
downstream sites keep serving the old rows.

**Files:**
- Modify: `EVENTS/src/imio/events/core/subscribers.py`
- Modify: `EVENTS/src/imio/events/core/subscribers.zcml`
- Test: `EVENTS/src/imio/events/core/tests/test_secondary_contact_rest.py` (extend)

**Interfaces:**
- Consumes: `ISecondaryContact` (Task 8), the `secondary_contacts` column (Task 11).
- Produces: `reindex_event_secondary_contacts(obj, event)`.

- [ ] **Step 1: Write the failing tests**

Append to `EVENTS/src/imio/events/core/tests/test_secondary_contact_rest.py`:

```python
class TestSecondaryContactReindexing(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event"
        )

    def _metadata(self):
        return api.content.find(UID=self.event.UID())[0].secondary_contacts

    def test_adding_a_child_refreshes_the_event_metadata(self):
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        contact.related_contact = "uid-1"
        # No explicit reindex of the Event here: the subscriber must do it.
        api.content.transition  # noqa - keep the import surface obvious
        from zope.lifecycleevent import modified

        modified(contact)
        self.assertEqual(["uid-1"], [item["uid"] for item in self._metadata()])

    def test_removing_a_child_refreshes_the_event_metadata(self):
        contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )
        contact.related_contact = "uid-1"
        from zope.lifecycleevent import modified

        modified(contact)
        self.assertEqual(1, len(self._metadata()))
        api.content.delete(obj=contact)
        self.assertEqual([], self._metadata())
```

- [ ] **Step 2: Run to verify the new tests fail**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -t TestSecondaryContactReindexing`
Expected: FAIL — the metadata is stale (empty after add, still populated after
delete).

- [ ] **Step 3: Write the subscriber**

Append to `EVENTS/src/imio/events/core/subscribers.py`:

```python
def reindex_event_secondary_contacts(obj, event):
    """Refresh the parent Event's `secondary_contacts` metadata.

    The column is computed from the Event's children, so a change to a child is
    invisible to the catalog until the Event itself is reindexed. Without this,
    downstream sites keep serving a stale snapshot.

    On IObjectRemovedEvent the child is already out of the container, so
    recomputing gives the post-removal value, which is what we want. `event`
    carries `newParent`/`oldParent` but `aq_parent` is enough here and works
    for all three lifecycle events.
    """
    parent = aq_parent(obj)
    if parent is None or not IEvent.providedBy(parent):
        return
    parent.reindexObject(idxs=["secondary_contacts"])
```

Add the imports it needs, in the module's existing alphabetical style:
```python
from Acquisition import aq_parent
from imio.events.core.contents import IEvent
```
Check first whether `IEvent` and `aq_parent` are already imported in that module
and do not duplicate them.

Note on `idxs=["secondary_contacts"]`: `reindexObject` with `idxs` also updates
metadata in Plone's `CatalogTool`, which is why this is enough. If the test
proves otherwise, call `parent.reindexObject()` with no arguments and say so in
the checkpoint report rather than leaving a silent difference.

- [ ] **Step 4: Register the subscriber**

Add to `EVENTS/src/imio/events/core/subscribers.zcml`, inside `<configure>`:

```xml
  <subscriber for="imio.events.core.contents.ISecondaryContact
                   zope.lifecycleevent.interfaces.IObjectAddedEvent"
              handler=".subscribers.reindex_event_secondary_contacts" />

  <subscriber for="imio.events.core.contents.ISecondaryContact
                   zope.lifecycleevent.interfaces.IObjectModifiedEvent"
              handler=".subscribers.reindex_event_secondary_contacts" />

  <subscriber for="imio.events.core.contents.ISecondaryContact
                   zope.lifecycleevent.interfaces.IObjectRemovedEvent"
              handler=".subscribers.reindex_event_secondary_contacts" />
```

- [ ] **Step 5: Run the tests**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_secondary_contact_rest`
Expected: PASS, both classes.

- [ ] **Step 6: Run the existing subscriber suite for regressions**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_event -m imio.events.core.tests.test_agenda`
Expected: PASS.

- [ ] **Step 7: Checkpoint** — report all suites, and whether `idxs=` sufficed. Do not commit.

---

## Task 13: The 1026 → 1027 upgrade

**Files:**
- Modify: `EVENTS/src/imio/events/core/profiles/default/metadata.xml`
- Create: `EVENTS/src/imio/events/core/upgrades/profiles/1026_to_1027/types.xml`
- Create: `EVENTS/src/imio/events/core/upgrades/profiles/1026_to_1027/types/imio.events.SecondaryContact.xml`
- Create: `EVENTS/src/imio/events/core/upgrades/profiles/1026_to_1027/types/imio.events.Event.xml`
- Create: `EVENTS/src/imio/events/core/upgrades/profiles/1026_to_1027/catalog.xml`
- Create: `EVENTS/src/imio/events/core/upgrades/profiles/1026_to_1027/workflows.xml`
- Modify: `EVENTS/src/imio/events/core/upgrades/configure.zcml`
- Modify: `EVENTS/src/imio/events/core/upgrades/upgrades.py`
- Test: `EVENTS/src/imio/events/core/tests/test_setup.py` (extend)

**Interfaces:**
- Consumes: the default profile files from Tasks 8 and 11.
- Produces: `add_secondary_contacts_metadata(context)` in `upgrades.py`; profile
  version `1027`.

- [ ] **Step 1: Write the failing test**

Append to `EVENTS/src/imio/events/core/tests/test_setup.py` — read the file
first and match its existing test-class style and imports:

```python
    def test_profile_version(self):
        setup = api.portal.get_tool("portal_setup")
        self.assertEqual(
            "1027", setup.getLastVersionForProfile("imio.events.core:default")[0]
        )

    def test_upgrade_1026_to_1027_is_registered(self):
        setup = api.portal.get_tool("portal_setup")
        steps = setup.listUpgrades("imio.events.core:default", show_old=True)
        sources = [
            step["sdest"]
            for group in steps
            for step in (group if isinstance(group, list) else [group])
        ]
        self.assertIn("1027", sources)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_setup`
Expected: FAIL — version is still `1026`.

- [ ] **Step 3: Bump the profile version**

In `EVENTS/src/imio/events/core/profiles/default/metadata.xml` change
`<version>1026</version>` to `<version>1027</version>`. Leave the
`<dependencies>` block untouched.

- [ ] **Step 4: Create the upgrade profile directory**

`upgrades/profiles/1026_to_1027/types.xml`:
```xml
<?xml version='1.0' encoding='UTF-8'?>
<object name="portal_types" meta_type="Plone Types Tool">
  <object meta_type="Dexterity FTI" name="imio.events.SecondaryContact"/>
  <object meta_type="Dexterity FTI" name="imio.events.Event"/>
</object>
```

`upgrades/profiles/1026_to_1027/types/imio.events.SecondaryContact.xml`: a byte
copy of the file written in Task 8.

`upgrades/profiles/1026_to_1027/types/imio.events.Event.xml`: only the
`allowed_content_types` property, so the reimport does not touch anything else:
```xml
<?xml version="1.0"?>
<object name="imio.events.Event" meta_type="Dexterity FTI">
  <property name="allowed_content_types">
    <element value="File" />
    <element value="Image" />
    <element value="imio.events.SecondaryContact" />
  </property>
</object>
```

`upgrades/profiles/1026_to_1027/catalog.xml`:
```xml
<?xml version="1.0"?>
<object name="portal_catalog">
  <column value="secondary_contacts"/>
</object>
```

`upgrades/profiles/1026_to_1027/workflows.xml`:
```xml
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="Plone Workflow Tool">
  <bindings>
    <type type_id="imio.events.SecondaryContact">
      <bound-workflow workflow_id="one_state_workflow" />
    </type>
  </bindings>
</object>
```

Before writing these, look at `upgrades/profiles/1025_to_1026/` and match its
exact file layout and XML preamble style.

- [ ] **Step 5: Write the upgrade handler**

Append to `EVENTS/src/imio/events/core/upgrades/upgrades.py`, modelled on
`add_event_sponsors_metadata` (lines ~189-196) — read that function and mirror
it:

```python
def add_secondary_contacts_metadata(context):
    catalog = api.portal.get_tool("portal_catalog")
    metadatas = list(catalog.schema())
    if "secondary_contacts" not in metadatas:
        catalog.addColumn("secondary_contacts")
        logger.info("Added secondary_contacts metadata column")
    catalog.manage_reindexIndex(ids=["portal_type"])
    logger.info("Reindexed catalog for secondary_contacts")
```

Match `add_event_sponsors_metadata`'s reindex call exactly rather than inventing
one: open it and copy whatever it does on its last lines.

- [ ] **Step 6: Register the upgrade**

Append to `EVENTS/src/imio/events/core/upgrades/configure.zcml`, before the
closing `</configure>`, mirroring the 1025→1026 block:

```xml
  <genericsetup:registerProfile
      name="upgrade_1026_to_1027"
      title="Upgrade core from 1026 to 1027"
      directory="profiles/1026_to_1027"
      description="Add the imio.events.SecondaryContact type and its catalog metadata column"
      provides="Products.GenericSetup.interfaces.EXTENSION"
      />

  <genericsetup:upgradeSteps
      source="1026"
      destination="1027"
      profile="imio.events.core:default">
    <genericsetup:upgradeDepends
        title="Add the imio.events.SecondaryContact type and its catalog metadata column"
        import_profile="imio.events.core.upgrades:upgrade_1026_to_1027"
        />
    <genericsetup:upgradeStep
        title="Add secondary_contacts metadata column"
        handler=".upgrades.add_secondary_contacts_metadata"
        />
  </genericsetup:upgradeSteps>
```

- [ ] **Step 7: Run the setup tests**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test -m imio.events.core.tests.test_setup`
Expected: PASS.

- [ ] **Step 8: Run the whole `EVENTS` suite**

Run: `cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test`
Expected: PASS.

- [ ] **Step 9: Checkpoint** — report the full suite. Do not commit.

---

## Task 14: Dependency floors and changelogs

**Files:**
- Modify: `COMMON/CHANGES.rst`
- Modify: `CORE/setup.py`, `CORE/CHANGES.rst`
- Modify: `EVENTS/setup.py`, `EVENTS/CHANGES.rst`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Record the change in `COMMON/CHANGES.rst`**

Under the existing `1.2.58 (unreleased)` heading, replace
`- Nothing changed yet.` with:

```rst
- WEBBDC-2835 : Add a shared contact layer (``imio.smartweb.common.contact``):
  the phones/mails/urls row schemas, the ``IContactInformationsGrids`` schema
  mixin, the row-building helpers and the ``ContactInformationsGridMixin``
  form mixin, moved out of ``imio.smartweb.core`` so ``imio.events.core`` can
  reuse them. Also moves ``FrozenLabelTextFieldWidget`` and the
  ``imio.smartweb.vocabulary.*DisplayColumns`` vocabularies (names unchanged).
  [boulch]
```

- [ ] **Step 2: Pin `COMMON` from `CORE`**

In `CORE/setup.py` change the `"imio.smartweb.common"` entry of
`install_requires` (line ~78) to `"imio.smartweb.common>=1.2.58"`.

Add to `CORE/CHANGES.rst`, under its current unreleased heading:
```rst
- WEBBDC-2835 : Move the contact-section row schemas, row helpers, grid form
  mixin, frozen-label widget and ``*DisplayColumns`` vocabularies to
  ``imio.smartweb.common``. No functional change.
  [boulch]
```

- [ ] **Step 3: Pin `COMMON` from `EVENTS` and record the feature**

In `EVENTS/setup.py` change the `"imio.smartweb.common"` entry (line ~67) to
`"imio.smartweb.common>=1.2.58"`.

Add to `EVENTS/CHANGES.rst`, under its current unreleased heading:
```rst
- WEBBDC-2835 : Add the ``imio.events.SecondaryContact`` type ("Secondary
  contact"), addable several times inside an ``imio.events.Event``. Each object
  references one directory contact and keeps a curated snapshot of its phones,
  e-mails and urls, published through ``@events`` as ``secondary_contacts``
  (full serializer + catalog metadata column). Profile 1026 -> 1027.
  [boulch]
```

Check the actual heading of each `CHANGES.rst` before writing — do not create a
new version heading, use the existing unreleased one.

- [ ] **Step 4: Verify the version floor is real**

Run: `grep -n "^version" /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common/setup.py`
Expected: `1.2.58.dev0` or similar. If the version in `setup.py` is **not**
1.2.58, use the actual version in both pins instead and say so in the
checkpoint — a floor pointing at a version that will never exist breaks the
install.

- [ ] **Step 5: Full suites, all three packages**

Run in turn:
```bash
cd /home/cboulanger/iasmartweb/buildout.events/src/imio.smartweb.common && ./bin/test
cd /home/cboulanger/iasmartweb/buildout.smartweb/src/imio.smartweb.core && ./bin/test
cd /home/cboulanger/iasmartweb/buildout.events/src/imio.events.core && ./bin/test
```
Expected: all PASS.

- [ ] **Step 6: Final checkpoint**

Report, per package: the suite result, and `git status --short` so the author
sees exactly what is staged for their own commit. Do **not** commit. Remind the
author that the shared layer must be pushed from the `buildout.events` clone of
`imio.smartweb.common` and pulled into the `buildout.smartweb` one.

---

## Self-review notes

**Spec coverage.** Every numbered decision and component of the spec maps to a
task: decision 1 → Task 8; decision 2 → Task 10; decision 3 → Task 8 Step 3
(view modules deleted) and Task 9 Step 4 (no `view` page); decision 4 →
Tasks 3, 5, 10; decisions 5-6 → Task 8. Spec Part 1 → Tasks 2-6. Spec Part 2
§1-2 → Tasks 8-9; §3 → Task 8; §4 → Tasks 10-11; §5 → Task 12; §6 → Task 13.
Spec Part 3 → Tasks 2, 4, 7, 14. Spec "Tests" → the test steps throughout.
Spec "Assumptions" → Task 1 (both), Task 11 (metadata column holding dicts,
exercised by `test_the_catalog_metadata_carries_the_snapshot`).

**One item the spec did not name**, added here because it would otherwise be a
silent production bug: the **workflow binding** (Task 8 Step 7). Without
`one_state_workflow`, a Secondary contact is created `private` on the default
chain and `listFolderContents` hides it from the anonymous downstream site, so
`secondary_contacts` would come back empty in production while every test that
runs as Manager passed.

**Type consistency.** `contact_uids_field` is spelled identically in Tasks 6, 7
and 9. `get_secondary_contacts` is spelled identically in Tasks 10, 11 and 12.
`kept_rows` / `serialize_secondary_contact` appear only in Task 10 and its
test. `IContactInformationsGrids` is spelled identically in Tasks 1, 3, 7 and 8.
`type_token` appears in Tasks 3, 5, 6, 9, 10 and 11 with the same meaning
throughout: the raw remote token.

**Three places where the plan deliberately says "look before you write"** rather
than guessing, because the surrounding file's exact convention is the
requirement: the `<utility>` element form in `COMMON/vocabularies.zcml`
(Task 4 Step 4), the standard FTI property set copied from
`imio.events.Folder.xml` (Task 8 Step 6), and the reindex call inside
`add_event_sponsors_metadata` (Task 13 Step 5). Also the `@events` handler class
name in Task 11 Step 1. These are not placeholders — the step says exactly which
file to read and what to take from it.
