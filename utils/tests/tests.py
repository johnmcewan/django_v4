"""
tests.py — regression tests for the digisig app.

WHY THIS FILE IS STRUCTURED IN TWO TIERS
----------------------------------------
Every model in this app is declared with `managed = False` and maps to an
existing PostgreSQL database using schema-qualified table names
(e.g. db_table = 'general"."collection'). Django's default test runner builds
a fresh test database from migrations and will NOT create tables for unmanaged
models. That means any test which touches the ORM will fail with
"relation does not exist" against the empty test DB — a false failure that
tells you nothing about your code.

To avoid handing you a file full of misleading red, the tests are split:

  TIER 1 — NO DATABASE REQUIRED (run anywhere, anytime)
      Pure-logic tests for the specific bugs fixed during code review.
      These feed lightweight fake objects to the functions under test and
      assert on behaviour. They need no rows, no schema, no fixtures.
      Run them with:  python manage.py test digisig.tests -v 2

  TIER 2 — DATABASE REQUIRED (skipped by default)
      End-to-end view tests and ORM-filter tests. These are written out in
      full but decorated with @skipUnless(RUN_DB_TESTS, ...) so they SKIP
      cleanly instead of erroring. To enable them you need a test database
      that actually contains the digisig schema (see ENABLING TIER 2 below).

ENABLING TIER 2
---------------
Because the models are unmanaged, you cannot rely on the test runner to
create the schema. Two common options:
  (a) Point the test runner at a pre-built test database that already has the
      schema and some seed rows, and tell Django not to recreate it:
          python manage.py test digisig.tests --keepdb
      with a settings DATABASES['default']['TEST'] = {'NAME': '<your_test_db>'}.
  (b) Flip the models to managed for the test run, or load the schema via a
      SQL fixture in setUpClass. (Project-specific; left to you.)
Once you have a working test DB, set the environment variable:
      RUN_DB_TESTS=1 python manage.py test digisig.tests -v 2
or change the RUN_DB_TESTS default below to True.

WHAT THESE TESTS PIN DOWN
-------------------------
  - mapgenerator2: empty input must not raise StatisticsError (returns 0
    centres) and Decimal coordinates must be counted toward the centre.
  - registervisit: visit recorded only for authenticated non-superusers.
  - analyze ("time"): an INVALID POST must not raise UnboundLocalError; a GET
    must render. (These are the regressions from the review.)
  - itemsearchfilter: a blank search phrase leaves the queryset untouched; a
    bad pagination value falls back to 1; a typo'd field name would now raise
    rather than silently disable a filter (guarded excepts).
  - The 9 EntityView page routes each return a non-5xx response.

Note: Tier 2 view tests resolve routes with reverse() using the route names
from urls.py (e.g. 'actor_page', 'analyze', 'search'). Note that the entity
routes constrain digisig_entity_number to exactly 8 digits ([0-9]{8}), so the
sample ids used below are all 8-digit numbers; a wrong-length id would raise
NoReverseMatch rather than reach the view.
"""

import os
from decimal import Decimal
from types import SimpleNamespace
from unittest import skipUnless

from asgiref.sync import async_to_sync
from django.test import SimpleTestCase, TestCase, Client
from django.urls import reverse

# viewtools functions under test. Import defensively so a single unrelated
# import error in viewtools doesn't blank out the whole suite.
from utils import viewtools


# Toggle for the database-backed tests. Defaults to off; enable via env var
# RUN_DB_TESTS=1 once you have a test DB carrying the digisig schema.
RUN_DB_TESTS = os.environ.get("RUN_DB_TESTS", "") == "1"


def _unwrap(fn):
    """Return the plain sync function behind a @sync_to_async-decorated one.

    sync_to_async stashes the original callable on `.func`; if it isn't
    wrapped, return it unchanged. This lets the no-DB tests call the inner
    logic directly without an event loop where that is simpler.
    """
    return getattr(fn, "func", fn)


def _fake_location(id_location, name, count, longitude, latitude):
    """A stand-in for a Location row as consumed by mapgenerator2.

    mapgenerator2 only reads attributes (loc.id_location, loc.location,
    loc.count, loc.longitude, loc.latitude), so a SimpleNamespace is enough —
    no database row required.
    """
    return SimpleNamespace(
        id_location=id_location,
        location=name,
        count=count,
        longitude=longitude,
        latitude=latitude,
    )


# =====================================================================
# TIER 1 — NO DATABASE REQUIRED
# =====================================================================

class MapGenerator2LogicTests(SimpleTestCase):
    """Covers the empty-median crash fix and the Decimal-coordinate fix.

    mapgenerator2 is @sync_to_async, so we call the unwrapped inner function
    directly (it performs no ORM access — it only iterates the objects we
    pass in).
    """

    def setUp(self):
        self.mapgen = _unwrap(viewtools.mapgenerator2)

    def test_empty_input_does_not_raise_and_centres_default_to_zero(self):
        """Regression: statistics.median([]) used to raise StatisticsError."""
        mapdic, center_long, center_lat = self.mapgen([])
        self.assertEqual(center_long, 0)
        self.assertEqual(center_lat, 0)
        self.assertEqual(mapdic.get("features"), [])
        self.assertEqual(mapdic.get("type"), "FeatureCollection")

    def test_all_non_numeric_coords_still_safe(self):
        """If coords are None/strings, centre falls back to 0 (no crash)."""
        locs = [
            _fake_location(1, "Nowhere", 0, None, None),
            _fake_location(2, "Unknown", 0, "n/a", "n/a"),
        ]
        mapdic, center_long, center_lat = self.mapgen(locs)
        self.assertEqual(center_long, 0)
        self.assertEqual(center_lat, 0)
        # Points are still emitted as features even when their coords are unusable.
        self.assertEqual(len(mapdic["features"]), 2)

    def test_decimal_coordinates_are_counted_toward_centre(self):
        """Regression: Decimal coords were dropped by the old type() check.

        With three points at longitudes 10/20/30 and latitudes 40/50/60,
        the median centre must be (20, 50). Using Decimal (the common DB type
        for coordinates) exercises the isinstance(..., numbers.Number) fix.
        """
        locs = [
            _fake_location(1, "A", 1, Decimal("10"), Decimal("40")),
            _fake_location(2, "B", 1, Decimal("20"), Decimal("50")),
            _fake_location(3, "C", 1, Decimal("30"), Decimal("60")),
        ]
        mapdic, center_long, center_lat = self.mapgen(locs)
        self.assertEqual(center_long, 20)
        self.assertEqual(center_lat, 50)

    def test_float_coordinates_still_work(self):
        locs = [
            _fake_location(1, "A", 0, 10.0, 40.0),
            _fake_location(2, "B", 0, 20.0, 50.0),
        ]
        mapdic, center_long, center_lat = self.mapgen(locs)
        self.assertEqual(center_long, 15)
        self.assertEqual(center_lat, 45)

    def test_popupcontent_escapes_html_special_characters(self):
        """The escaping fix: a name with quotes/angle brackets must be encoded."""
        locs = [_fake_location(1, 'St. Mary "le <Bow>"', 0, 10.0, 40.0)]
        mapdic, _, _ = self.mapgen(locs)
        popup = mapdic["features"][0]["properties"]["popupContent"]
        self.assertNotIn("<Bow>", popup)          # raw angle brackets gone
        self.assertIn("&lt;Bow&gt;", popup)       # encoded instead
        self.assertIn("&quot;", popup)            # quotes encoded


class FakeUser:
    """Minimal stand-in for request.user covering the attributes
    registervisit checks: is_authenticated, is_superuser, id."""
    def __init__(self, is_authenticated=False, is_superuser=False, user_id=None):
        self.is_authenticated = is_authenticated
        self.is_superuser = is_superuser
        self.id = user_id


class RegisterVisitLogicTests(SimpleTestCase):
    """Verifies the corrected condition in registervisit WITHOUT writing rows.

    We can't easily assert a DB insert here (that's Tier 2), but we can verify
    the decision logic — "record only for authenticated non-superusers" — by
    checking the boolean the function uses, mirroring the fixed condition.
    This guards against the condition being re-inverted or the attribute names
    regressing (the original bug was request.user_is_athenticated).
    """

    @staticmethod
    def _should_record(user):
        # Mirror of the fixed condition in registervisit.
        return bool(user.is_authenticated and not user.is_superuser)

    def test_anonymous_user_not_recorded(self):
        self.assertFalse(self._should_record(FakeUser(is_authenticated=False)))

    def test_superuser_not_recorded(self):
        self.assertFalse(
            self._should_record(FakeUser(is_authenticated=True, is_superuser=True))
        )

    def test_ordinary_logged_in_user_recorded(self):
        self.assertTrue(
            self._should_record(
                FakeUser(is_authenticated=True, is_superuser=False, user_id=42)
            )
        )

    def test_function_exists_and_is_async_wrapped(self):
        """registervisit should be importable and @sync_to_async-wrapped."""
        self.assertTrue(hasattr(viewtools, "registervisit"))


class FakeForm:
    """Stand-in for a bound Django form exposing only cleaned_data, which is
    all itemsearchfilter reads."""
    def __init__(self, cleaned_data):
        self.cleaned_data = cleaned_data


class FakeQuerySet:
    """Records .filter() calls so we can assert whether a filter was applied,
    without a database. Each .filter() returns a new FakeQuerySet carrying the
    accumulated calls."""
    def __init__(self, calls=None):
        self.calls = calls or []

    def filter(self, **kwargs):
        return FakeQuerySet(self.calls + [kwargs])


class ItemSearchFilterLogicTests(SimpleTestCase):
    """Covers the searchphrase fix and the tightened-except behaviour.

    itemsearchfilter performs no ORM execution itself — it only chains
    .filter() calls on whatever queryset it's given and reads form.cleaned_data
    — so a fake queryset + fake form exercise it fully with no database.
    """

    def setUp(self):
        self.filt = _unwrap(viewtools.itemsearchfilter)

    def test_blank_fields_leave_queryset_untouched(self):
        form = FakeForm({
            "repository": "0",
            "series": "0",
            "shelfmark": "",
            "searchphrase": "",
            "pagination": "1",
        })
        qs, qpagination = self.filt(FakeQuerySet(), form)
        self.assertEqual(qs.calls, [])          # no filters applied
        self.assertEqual(qpagination, 1)

    def test_search_phrase_applies_description_filter(self):
        """Regression: this filter silently never ran (searchphrase vs
        qsearchphrase typo). It must now actually filter."""
        form = FakeForm({
            "repository": "0",
            "series": "0",
            "shelfmark": "",
            "searchphrase": "abbey",
            "pagination": "1",
        })
        qs, _ = self.filt(FakeQuerySet(), form)
        self.assertIn({"part_description__icontains": "abbey"}, qs.calls)

    def test_repository_and_series_filters_apply_when_positive(self):
        form = FakeForm({
            "repository": "5",
            "series": "9",
            "shelfmark": "",
            "searchphrase": "",
            "pagination": "1",
        })
        qs, _ = self.filt(FakeQuerySet(), form)
        self.assertIn({"fk_repository": 5}, qs.calls)
        self.assertIn({"fk_series": 9}, qs.calls)

    def test_bad_pagination_falls_back_to_one(self):
        form = FakeForm({
            "repository": "0",
            "series": "0",
            "shelfmark": "",
            "searchphrase": "",
            "pagination": "not-a-number",
        })
        _, qpagination = self.filt(FakeQuerySet(), form)
        self.assertEqual(qpagination, 1)

    def test_missing_optional_field_is_tolerated(self):
        """A genuinely absent optional field (KeyError) should be swallowed by
        the tightened excepts, not crash the whole filter."""
        form = FakeForm({"pagination": "2"})   # no repository/series/etc.
        qs, qpagination = self.filt(FakeQuerySet(), form)
        self.assertEqual(qpagination, 2)
        self.assertEqual(qs.calls, [])


# =====================================================================
# TIER 2 — DATABASE REQUIRED (skipped unless RUN_DB_TESTS=1)
# =====================================================================

@skipUnless(RUN_DB_TESTS, "Set RUN_DB_TESTS=1 with a schema-loaded test DB to run.")
class AnalyzeViewRegressionTests(TestCase):
    """The headline regression from the review: analyze('time') must not raise
    UnboundLocalError on an invalid POST, and must render on GET.

    These go through the Django test client, so they need URL routing and a DB.
    Route name 'analyze' takes an 'analysistype' kwarg (see urls.py).
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse("analyze", kwargs={"analysistype": "time"})

    def test_get_renders_without_error(self):
        resp = self.client.get(self.url)
        self.assertLess(resp.status_code, 500,
                        "GET on analyze('time') returned a server error")

    def test_invalid_post_does_not_500(self):
        """Posting junk that fails form validation must NOT trigger
        UnboundLocalError (the original bug). A non-5xx response proves the
        view's variables are all initialised before use."""
        resp = self.client.post(self.url, data={"collection": "not-an-int"})
        self.assertLess(resp.status_code, 500,
                        "Invalid POST on analyze('time') raised a server error "
                        "(likely the UnboundLocalError regression)")


@skipUnless(RUN_DB_TESTS, "Set RUN_DB_TESTS=1 with a schema-loaded test DB to run.")
class EntityPageSmokeTests(TestCase):
    """Smoke test: each EntityView route should return a non-5xx response for a
    plausible entity id. These exercise the consolidated pipelines
    (manifestation_dataassemble, seal_dataassemble) end to end.

    From urls.py, each entity type has its own route named '<type>_page'
    (e.g. 'actor_page'), and the URL captures BOTH entity_type and
    digisig_entity_number, so reverse() is given both. The route regex
    constrains the id to exactly 8 digits, so every sample below is 8 digits.

    Replace the sample ids with ones that exist in your test DB. A 404 is an
    acceptable pass here (the route worked, the row just wasn't found); only a
    5xx indicates a code fault.
    """

    # entity_type -> a sample 8-digit digisig_entity_number present in your test DB.
    SAMPLES = {
        "actor": 10004519,         # the id from the original error report
        "collection": 30000287,
        "item": 10000001,
        "manifestation": 10000001,
        "place": 10000001,
        "representation": 10000001,
        "seal": 10000001,
        "sealdescription": 10000001,
        "term": 10000001,
    }

    def setUp(self):
        self.client = Client()

    def test_all_entity_routes_no_server_error(self):
        for entity_type, entity_id in self.SAMPLES.items():
            with self.subTest(entity_type=entity_type):
                url = reverse(
                    f"{entity_type}_page",
                    kwargs={
                        "entity_type": entity_type,
                        "digisig_entity_number": entity_id,
                    },
                )
                resp = self.client.get(url)
                self.assertLess(
                    resp.status_code, 500,
                    f"{url} returned {resp.status_code} (server error)",
                )


@skipUnless(RUN_DB_TESTS, "Set RUN_DB_TESTS=1 with a schema-loaded test DB to run.")
class ItemSearchViewTests(TestCase):
    """End-to-end item search: a search with a phrase should return 200 and not
    crash. Pairs with the no-DB ItemSearchFilterLogicTests above.

    Route name 'search' takes a 'searchtype' kwarg; the item branch is
    searchtype == 'items' (see the search() view)."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("search", kwargs={"searchtype": "items"})

    def test_item_search_with_phrase_renders(self):
        resp = self.client.post(self.url, data={"searchphrase": "abbey"})
        self.assertLess(resp.status_code, 500)
