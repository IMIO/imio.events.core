# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Overview

**imio.events.core** is a Plone 6.1 addon that is the core events management system for the Walloon event aggregation platform. It provides content types, REST API endpoints, Solr indexing, and multilingual support for events consumed by downstream Smartweb sites.

## Commands

```bash
make buildout    # Create venv (python3.12), install requirements, run buildout
make test        # Run all tests (builds first if needed)
./bin/test       # Run tests directly (after make buildout)
./bin/test -t TestClassName        # Run a single test class
./bin/test -t test_method_name     # Run a single test method
./bin/test-coverage               # Run tests with coverage report (90% minimum)
```

## Architecture

### Content Types (`src/imio/events/core/contents/`)

Four Dexterity content types:

- **Entity** – Represents a local authority/organization. Contains Agendas. Has `local_categories` (datagrid with FR/NL/DE/EN translations), `zip_codes`, and `authorize_to_bring_event_anywhere`. Auto-creates two sub-agendas on creation.
- **Agenda** – Container for Events within an Entity. Has `populating_agendas` relation field for hierarchical composition (one Agenda can pull events from others). Triggers faceted navigation reconfiguration.
- **Event** – The core content type. Extends `IAddress` and translation behaviors. Fields include `selected_agendas` (multi-select linking event to other Agendas for distribution), `category` (global vocabulary), `local_category` (Entity-specific), social links, and multilingual title/description/body (FR/DE/NL/EN).
- **Folder** – Standard container, minimal customization.

### REST API (`src/imio/events/core/rest/`)

- **`@events`** – Primary search endpoint for downstream sites. Extends Plone's SearchHandler. Key behaviors:
  - Cascading agenda filtering via `get_cascading_agendas()` (recursive hierarchy resolution)
  - Recurring event occurrence expansion via iCal recurrence rules
  - Date range filtering: `"min"` (next 365 days), `"max"` (past 365 days), `"min:max"` (custom range)
  - RAM cache with 240s TTL, keyed by MD5-hashed query parameters
- **`@search-filters`** – Returns faceted search metadata (category, local_category, topics)
- **`@odwb`** / **`@odwb_entities`** – Push events/entities to external ODWB open data platform

### Key Modules

- **`utils.py`** – `expand_occurences()` and `filter_and_sort_occurrences()` are the core functions for handling recurring events. These build expanded occurrence objects with image scale URLs, geolocation data, and computed end dates.
- **`indexers.py`** – Custom catalog indexers for translation flags (`translated_in_nl/de/en`) and category title translations. Registered in `indexers.zcml`.
- **`subscribers.py`** – Event lifecycle handlers: Entity/Agenda creation sets up faceted config; Event creation ensures `selected_agendas` always includes the direct parent Agenda; Agenda deletion removes references from Events.
- **`vocabularies.py`** – `EventsCategoriesVocabulary` (10 hardcoded global categories), `EventsLocalCategoriesVocabulary` (context-aware, pulled from Entity's `local_categories` field).
- **`ia/`** – AI-powered content categorization: suggests global category, local category, and target audience from event title/body text. Extends `BaseProcessCategorizeContentView` from imio.smartweb.common.
- **`setuphandlers.py`** – Post-install configuration steps.
- **`upgrades/`** – Version migration handlers.

### Installation Profile (`src/imio/events/core/profiles/default/`)

Standard Plone GenericSetup profile. Key files: `catalog.xml` (custom indexes/metadata), `rolemap.xml` (AddEntity, BringEventIntoPersonnalAgenda permissions), `taxonomies/` (collective.taxonomy event_public config).

### Testing (`src/imio/events/core/tests/`)

Tests use a Plone testing layer defined in `testing.py`. Test files mirror modules: `test_event.py`, `test_agenda.py`, `test_entity.py`, `test_rest.py`, `test_odwb.py`, `test_utils.py`, `test_vocabularies.py`, `test_indexes.py`, `test_multilingual.py`, `test_local_roles.py`, `test_cropping.py`, `test_bring_event_into_agendas.py`. Robot (acceptance) tests in `tests/robot/`.

### Dependencies

- **Plone ecosystem**: plone.restapi, plone.app.dexterity, plone.app.imagecropping, plone.event (recurrence)
- **Smartweb**: imio.smartweb.common (REST utilities, cropping, geolocation), imio.smartweb.locales (FR/DE/NL translations)
- **Third-party**: collective.geolocationbehavior, collective.taxonomy, collective.z3cform.datagridfield, eea.facetednavigation, embeddify
