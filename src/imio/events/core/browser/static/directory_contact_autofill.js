/**
 * Edit-form helpers for ``imio.events.Event``:
 *
 *  - **Contact autofill**: when the user picks an entry in the
 *    ``directory_linked_contact`` select, GET ``@@directory_contact_info``
 *    on the current Plone site (a server-side proxy to the remote directory
 *    that avoids CORS and keeps the directory URL out of the client) and
 *    populate the IEventContact (name / email / phone) and IAddress
 *    (street, number, complement, zipcode, city, country) inputs. Picking a
 *    (new) contact first wipes those fields, then fills them from the chosen
 *    entry; deselecting simply clears them. A "Open in directory" link is
 *    shown next to the select, pointing at the contact's own directory URL
 *    (its ``@id``) plus ``/edit`` so editors can jump straight to the contact
 *    in the remote directory (within its entity).
 *
 *  - **Address-based geocoding**: a "Géolocaliser depuis l'adresse" button
 *    inserted at the top of the geolocation widget. On click, we build a
 *    query from the IAddress fields, hit OpenStreetMap's Nominatim public
 *    endpoint, and write the first hit's lat/lon into the geolocation
 *    inputs (dispatching ``change`` so pat-leaflet recenters the marker).
 *    The action is intentionally manual (one click = one request) to stay
 *    within Nominatim's usage policy.
 *
 * Shipped via the ``imio-events-core-edit`` bundle, which is registered in
 * ``profiles/default/registry.xml`` and restricted to logged-in members
 * through the bundle's ``expression`` condition. Loaded site-wide for
 * editors and silently no-ops on pages without the expected form fields.
 */
(function () {
    "use strict";

    // IDs produced by z3c.form for the IEvent schema and the IEventContact
    // behavior. They are stable across add and edit forms because both use
    // the same widget prefix. The address inputs come from IAddress (no
    // behavior prefix) and match the Contact schema field names one-to-one.
    var SELECT_ID = "form-widgets-directory_linked_contact";
    var CONTACT_FIELD_IDS = {
        name: "form-widgets-IEventContact-contact_name",
        email: "form-widgets-IEventContact-contact_email",
        phone: "form-widgets-IEventContact-contact_phone",
    };
    var ADDRESS_FIELD_IDS = {
        street: "form-widgets-street",
        number: "form-widgets-number",
        complement: "form-widgets-complement",
        zipcode: "form-widgets-zipcode",
        city: "form-widgets-city",
        country: "form-widgets-country",
    };
    var GEO_LAT_ID = "form-widgets-IGeolocatable-geolocation_latitude";
    var GEO_LNG_ID = "form-widgets-IGeolocatable-geolocation_longitude";
    // OpenStreetMap's Nominatim public endpoint. Free for low-volume,
    // user-triggered queries. Per their usage policy we only fire one request
    // per click (no autofill on field change) and rely on the browser-sent
    // ``Referer`` header to identify the application.
    var NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";

    function getPortalUrl() {
        // Plone exposes the portal URL on <body data-portal-url="..."> so we
        // can build absolute URLs without hard-coding the site path.
        var body = document.body;
        return (body && body.dataset && body.dataset.portalUrl) || "";
    }

    function markAutofilled(field) {
        if (!field) return;
        field.classList.add("autofilled-contact");
        function removeOnUserInput(evt) {
            if (evt.isTrusted) {
                field.classList.remove("autofilled-contact");
                field.removeEventListener("input", removeOnUserInput);
                field.removeEventListener("change", removeOnUserInput);
            }
        }
        // "input"  → text inputs (not fired by .value = x assignments)
        // "change" → selects (isTrusted distinguishes user interaction from dispatchEvent)
        field.addEventListener("input", removeOnUserInput);
        field.addEventListener("change", removeOnUserInput);
    }

    function fillIfEmpty(field, value) {
        if (!field) return;
        // Preserve any existing user input. The "Clear" button is the only
        // path that wipes contact fields. ``--NOVALUE--`` is the placeholder
        // value z3c.form puts on Choice selects when no option is picked, so
        // we treat it as empty.
        var current = (field.value || "").trim();
        if (current && current !== "--NOVALUE--") return;
        var newValue = value || "";
        field.value = newValue;
        if (newValue) {
            markAutofilled(field);
        }
        // Notify any widget enhancer (pat-select2, geolocation map, …) so the
        // visible state stays in sync with the underlying input/select value.
        try {
            field.dispatchEvent(new Event("change", { bubbles: true }));
        } catch (e) {
            /* old browsers without Event constructor — best-effort */
        }
    }

    function resolveFields(idMap) {
        var out = {};
        var found = false;
        Object.keys(idMap).forEach(function (key) {
            var el = document.getElementById(idMap[key]);
            out[key] = el;
            if (el) found = true;
        });
        out.__any = found;
        return out;
    }

    function buildAddressQuery(addressFields) {
        // Build a free-form query string for Nominatim from the IAddress
        // inputs. Order matters less than presence; we keep it natural for
        // humans (street/number, complement, zip city, country). For the
        // ``country`` select we use the visible label (e.g. "Belgique")
        // because Nominatim resolves country names better than ISO codes.
        var bits = [];
        function pushTextField(key) {
            var el = addressFields[key];
            if (!el) return;
            var v = (el.value || "").trim();
            if (v && v !== "--NOVALUE--") bits.push(v);
        }
        // Combine street + number into one comma-less chunk so Nominatim
        // treats them as a single address line.
        var street = addressFields.street && addressFields.street.value
            ? addressFields.street.value.trim()
            : "";
        var number = addressFields.number && addressFields.number.value
            ? addressFields.number.value.trim()
            : "";
        var streetLine = [street, number].filter(Boolean).join(" ").trim();
        if (streetLine) bits.push(streetLine);
        pushTextField("complement");
        // Strip all whitespace (including the NBSP that IntegerDataConverter
        // inserts as a thousand separator, e.g. "5 300") so the zipcode lands
        // in Nominatim's query as a clean numeric token.
        var zip = addressFields.zipcode && addressFields.zipcode.value
            ? addressFields.zipcode.value.replace(/\s+/g, "")
            : "";
        var city = addressFields.city && addressFields.city.value
            ? addressFields.city.value.trim()
            : "";
        var zipCity = [zip, city].filter(Boolean).join(" ").trim();
        if (zipCity) bits.push(zipCity);
        var countryEl = addressFields.country;
        if (countryEl && countryEl.value && countryEl.value !== "--NOVALUE--") {
            if (countryEl.tagName === "SELECT") {
                var opt = countryEl.options[countryEl.selectedIndex];
                bits.push((opt && opt.text) ? opt.text.trim() : countryEl.value);
            } else {
                bits.push(countryEl.value.trim());
            }
        }
        return bits.join(", ");
    }

    function stripZipcodeWhitespace(zipField) {
        // IntegerDataConverter inserts an NBSP thousand-separator on render,
        // turning "5300" into "5 300". Strip whitespace in place so the value
        // displayed in the form matches what gets submitted (and what we
        // send to Nominatim).
        if (!zipField || !zipField.value) return;
        var cleaned = zipField.value.replace(/\s+/g, "");
        if (cleaned !== zipField.value) {
            zipField.value = cleaned;
        }
    }

    function initGeocodeButton(addressFields) {
        var latField = document.getElementById(GEO_LAT_ID);
        var lngField = document.getElementById(GEO_LNG_ID);
        if (!latField || !lngField) return;
        // Auto-clean the zipcode field whenever the user leaves it, so they
        // don't have to delete the NBSP separator by hand before saving or
        // geocoding.
        if (addressFields.zipcode) {
            addressFields.zipcode.addEventListener("blur", function () {
                stripZipcodeWhitespace(addressFields.zipcode);
            });
        }
        // Insert the button at the top of the geolocation wrapper so it sits
        // right above the leaflet map; fall back to the field wrapper if the
        // expected DOM structure is missing.
        var wrapper =
            latField.closest(".geolocation_wrapper") ||
            latField.closest(".field") ||
            latField.parentNode;
        if (!wrapper) return;

        var container = document.createElement("div");
        container.style.marginBottom = "0.5em";

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-secondary btn-sm";
        btn.textContent = "Géolocaliser depuis l'adresse";

        var status = document.createElement("span");
        status.style.marginLeft = "0.5em";

        btn.addEventListener("click", function () {
            stripZipcodeWhitespace(addressFields.zipcode);
            var query = buildAddressQuery(addressFields);
            if (!query) {
                status.textContent = "Adresse vide.";
                return;
            }
            status.textContent = "Recherche…";
            btn.disabled = true;
            var url =
                NOMINATIM_URL +
                "?format=json&limit=1&addressdetails=0&q=" +
                encodeURIComponent(query);
            fetch(url, { headers: { Accept: "application/json" } })
                .then(function (r) {
                    return r.ok ? r.json() : [];
                })
                .then(function (results) {
                    if (!results || !results.length) {
                        status.textContent = "Aucun résultat.";
                        return;
                    }
                    var hit = results[0];
                    latField.value = hit.lat;
                    lngField.value = hit.lon;
                    // pat-leaflet listens for change on the lat/lng inputs to
                    // move the marker; dispatching the event keeps the map
                    // and the form state in sync.
                    try {
                        latField.dispatchEvent(new Event("change", { bubbles: true }));
                        lngField.dispatchEvent(new Event("change", { bubbles: true }));
                    } catch (e) { /* no-op */ }
                    status.textContent = "OK (" + hit.display_name + ")";
                })
                .catch(function () {
                    status.textContent = "Erreur réseau.";
                })
                .then(function () {
                    btn.disabled = false;
                });
        });

        container.appendChild(btn);
        container.appendChild(status);
        wrapper.insertBefore(container, wrapper.firstChild);
    }

    function init() {
        var addressFields = resolveFields(ADDRESS_FIELD_IDS);
        // The geocode button is independent from the directory contact
        // autofill: it is useful on any Event form that exposes IAddress and
        // the geolocation behavior, even if the contact select is missing.
        if (addressFields.__any) {
            initGeocodeButton(addressFields);
        }

        var select = document.getElementById(SELECT_ID);
        if (!select) return;
        var contactFields = resolveFields(CONTACT_FIELD_IDS);
        // If none of the target fields are present we have nothing to fill —
        // bail out cleanly so the script stays harmless on unrelated forms.
        if (!contactFields.__any && !addressFields.__any) return;

        // "Open in directory" link shown next to the select once a contact is
        // picked. It targets the contact's real directory URL (its @id, from
        // @@directory_contact_info) so it lands on the contact in its own
        // entity, plus "/edit" to open the edit form there. Editors sign in to
        // the directory site separately (SSO).
        var contactLink = document.createElement("a");
        contactLink.className = "directory-contact-edit-link";
        contactLink.target = "_blank";
        contactLink.rel = "noopener noreferrer";
        contactLink.style.display = "none";
        contactLink.style.marginTop = "0.5em";
        contactLink.textContent = "Ouvrir le contact dans l'annuaire";
        (select.closest(".field") || select.parentNode).appendChild(contactLink);

        function setContactLink(baseUrl) {
            // baseUrl is the contact's @id (canonical directory URL). Strip any
            // trailing slash before appending "/edit". Hide the link when there
            // is no URL (nothing selected, or the lookup failed).
            if (baseUrl) {
                contactLink.href = baseUrl.replace(/\/+$/, "") + "/edit";
                contactLink.style.display = "";
            } else {
                contactLink.removeAttribute("href");
                contactLink.style.display = "none";
            }
        }

        function clearFields() {
            // Wipe every contact and address field we know about, ignoring
            // missing ones (e.g. on a future form variant that drops some).
            [contactFields, addressFields].forEach(function (fields) {
                Object.keys(fields).forEach(function (key) {
                    if (key === "__any") return;
                    var f = fields[key];
                    if (!f) return;
                    f.value = "";
                    f.classList.remove("autofilled-contact");
                    try {
                        f.dispatchEvent(new Event("change", { bubbles: true }));
                    } catch (e) { /* no-op */ }
                });
            });
        }

        function expandAddressFieldset() {
            // Once a contact is picked we prefill the IAddress inputs, so make
            // sure the "address" fieldset is visible. imio's edit.js renders
            // secondary fieldsets as toggles: the <legend> gets a
            // "dropdown-toggle collapsed" class and its content is hidden until
            // the legend is clicked (which slides it open and swaps the class
            // to "expanded"). We trigger that native click rather than flipping
            // classes ourselves so the real toggle runs — including the Leaflet
            // resize fix bound to the same legend in fixLeafletSize(). No-op if
            // the fieldset is already open.
            var legend = document.getElementById("fieldsetlegend-address");
            if (legend && !legend.classList.contains("expanded")) {
                legend.click();
            }
        }

        function fetchAndFill() {
            // Reset first so switching (or clearing) the selected contact
            // always reflects the new choice rather than keeping stale values
            // from the previous one. fillIfEmpty then populates the now-blank
            // fields from the fetched data.
            clearFields();
            var uid = select.value;
            // "--NOVALUE--" is z3c.form's placeholder for "nothing selected".
            if (!uid || uid === "--NOVALUE--") {
                // Deselection: nothing to fill and no contact to link to.
                setContactLink(null);
                return;
            }
            // A contact is chosen: reveal the address fieldset we're about to
            // fill. Skipped on deselection (empty uid) via the early return.
            expandAddressFieldset();
            var url =
                getPortalUrl() +
                "/@@directory_contact_info?uid=" +
                encodeURIComponent(uid);
            fetch(url, { credentials: "same-origin" })
                .then(function (r) {
                    return r.ok ? r.json() : {};
                })
                .then(function (data) {
                    fillIfEmpty(contactFields.name, data.name);
                    fillIfEmpty(contactFields.email, data.email);
                    fillIfEmpty(contactFields.phone, data.phone);
                    fillIfEmpty(addressFields.street, data.street);
                    fillIfEmpty(addressFields.number, data.number);
                    fillIfEmpty(addressFields.complement, data.complement);
                    // ``zipcode`` is rendered by z3c.form's IntegerDataConverter
                    // which inserts a locale thousand separator (NBSP in fr_BE),
                    // turning "5300" into "5 300". Inject a whitespace-free
                    // value so the field stays clean until the next save.
                    fillIfEmpty(
                        addressFields.zipcode,
                        (data.zipcode || "").replace(/\s+/g, "")
                    );
                    fillIfEmpty(addressFields.city, data.city);
                    fillIfEmpty(addressFields.country, data.country);
                    setContactLink(data.url);
                })
                .catch(function () {
                    // Network/parse errors are non-fatal: the user can still
                    // type the contact details manually. Drop any stale link.
                    setContactLink(null);
                });
        }

        // Bind the change handler twice on purpose. The select is enhanced by
        // pat-select2 (Select2 v3) which dispatches change events through
        // jQuery; depending on jQuery's version those events do not always
        // surface to a vanilla ``addEventListener``. The jQuery binding is
        // what actually fires when the user picks an option via the select2
        // popup, while the native binding covers programmatic changes and
        // future-proofs us if the widget is ever swapped out.
        select.addEventListener("change", fetchAndFill);
        if (window.jQuery) {
            window.jQuery(select).on("change", fetchAndFill);
        }

        // On an edit form a contact may already be linked. Show the directory
        // link on load WITHOUT running fetchAndFill (which would clear/refill
        // the fields and wipe existing values): just look up the contact URL.
        if (select.value && select.value !== "--NOVALUE--") {
            fetch(
                getPortalUrl() +
                    "/@@directory_contact_info?uid=" +
                    encodeURIComponent(select.value),
                { credentials: "same-origin" }
            )
                .then(function (r) {
                    return r.ok ? r.json() : {};
                })
                .then(function (data) {
                    setContactLink(data.url);
                })
                .catch(function () {
                    /* no-op: link just stays hidden */
                });
        }
    }

    function fixLeafletSize() {
        // Root cause: pat-leaflet (RequireJS async) and Plone's fieldset toggle
        // JS race each other. Whichever runs first loses:
        //   - If Leaflet wins: it measures a hidden container (height 0) and
        //     only loads a 2×2 tile stub. When the toggle later shows the
        //     fieldset the gray areas are already there.
        //   - If the toggle wins: no issue — Leaflet measures the visible
        //     container and loads the correct tile set.
        //
        // Fix: wait until BOTH events have fired, then dispatch a resize event
        // so Leaflet re-measures the now-visible container and fills the gaps.
        // A 150 ms grace period after the second event absorbs any CSS
        // transition on the fieldset row.

        var leafletReady = false;
        var fieldsetReady = false;

        function tryFix() {
            if (!leafletReady || !fieldsetReady) return;
            setTimeout(function () {
                window.dispatchEvent(new Event("resize"));
            }, 150);
        }

        // 1. Watch for Leaflet adding "leaflet-container" to the map div.
        var leafletObserver = new MutationObserver(function (mutations) {
            for (var i = 0; i < mutations.length; i++) {
                var el = mutations[i].target;
                if (el.classList && el.classList.contains("leaflet-container")) {
                    leafletReady = true;
                    leafletObserver.disconnect();
                    tryFix();
                    return;
                }
            }
        });
        leafletObserver.observe(document.body, {
            attributes: true,
            subtree: true,
            attributeFilter: ["class"],
        });

        // 2. Watch for Plone's toggle adding "expanded" to the fieldset legend.
        var legend = document.querySelector("#fieldsetlegend-address");
        if (!legend) {
            // No legend found — fieldset always visible, mark as ready now.
            fieldsetReady = true;
        } else if (legend.classList.contains("expanded")) {
            // Already expanded before our script ran.
            fieldsetReady = true;
        } else {
            var legendObserver = new MutationObserver(function (mutations) {
                for (var i = 0; i < mutations.length; i++) {
                    if (mutations[i].target.classList.contains("expanded")) {
                        fieldsetReady = true;
                        legendObserver.disconnect();
                        tryFix();
                        return;
                    }
                }
            });
            legendObserver.observe(legend, {
                attributes: true,
                attributeFilter: ["class"],
            });
        }

        // Fallback: if either observer never fires (e.g. different Plone
        // version, fieldset already visible), force a resize after 2 s.
        setTimeout(function () {
            window.dispatchEvent(new Event("resize"));
        }, 2000);

        // Re-measure on manual toggle click (fieldset collapsed then re-opened).
        if (legend) {
            legend.addEventListener("click", function () {
                setTimeout(function () {
                    window.dispatchEvent(new Event("resize"));
                }, 350);
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            init();
            fixLeafletSize();
        });
    } else {
        init();
        fixLeafletSize();
    }
})();
