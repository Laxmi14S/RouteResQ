import json

from django.test import TestCase
from django.urls import reverse

from .models import Route
from .views import calculate_route_score, generate_route_reasons


class RouteResQTestDataMixin:
    """Create reusable sample routes for automated tests."""

    def create_routes(self):
        self.bus_route = Route.objects.create(
            source="Bengaluru",
            destination="Goa",
            transport="Bus",
            duration_minutes=600,
            price=900,
            transfers=0,
            description="Direct overnight bus."
        )

        self.train_route = Route.objects.create(
            source="Bengaluru",
            destination="Goa",
            transport="Train",
            duration_minutes=720,
            price=550,
            transfers=0,
            description="Budget-friendly train."
        )

        self.combined_route = Route.objects.create(
            source="Bengaluru",
            destination="Goa",
            transport="Train + Bus",
            duration_minutes=540,
            price=1100,
            transfers=1,
            description="Faster combined journey."
        )

        self.alternative_bus_route = Route.objects.create(
            source="Bengaluru",
            destination="Goa",
            transport="Bus",
            duration_minutes=660,
            price=750,
            transfers=1,
            description="Alternative bus connection."
        )


class RouteListAPITests(RouteResQTestDataMixin, TestCase):
    """Test the available-routes endpoint."""

    def setUp(self):
        self.create_routes()
        self.url = reverse("route_list")

    def test_returns_routes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["count"], 4)
        self.assertEqual(len(data["routes"]), 4)

    def test_routes_are_ordered_by_price(self):
        response = self.client.get(self.url)

        prices = [
            route["price"]
            for route in response.json()["routes"]
        ]

        self.assertEqual(prices, sorted(prices))

    def test_filters_by_source_and_destination(self):
        response = self.client.get(
            self.url,
            {
                "source": "bengaluru",
                "destination": "goa",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 4)

    def test_filters_by_budget(self):
        response = self.client.get(
            self.url,
            {"budget": "900"}
        )

        self.assertEqual(response.status_code, 200)

        for route in response.json()["routes"]:
            self.assertLessEqual(route["price"], 900)

        self.assertEqual(response.json()["count"], 3)

    def test_filters_by_transport(self):
        response = self.client.get(
            self.url,
            {"transport": "Train"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(
            response.json()["routes"][0]["transport"],
            "Train"
        )

    def test_rejects_negative_budget(self):
        response = self.client.get(
            self.url,
            {"budget": "-100"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_rejects_non_numeric_budget(self):
        response = self.client.get(
            self.url,
            {"budget": "abc"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_rejects_post_request(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 405)


class APIHomeTests(TestCase):
    """Test the API home endpoint."""

    def test_api_home_returns_welcome_message(self):
        response = self.client.get(reverse("api_home"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("RouteResQ API", response.json()["message"])

    def test_api_home_rejects_post(self):
        response = self.client.post(reverse("api_home"))

        self.assertEqual(response.status_code, 405)


class RouteScoringTests(RouteResQTestDataMixin, TestCase):
    """Test the weighted route-scoring algorithm."""

    def setUp(self):
        self.create_routes()

    def test_score_is_between_zero_and_one_for_sample_route(self):
        score = calculate_route_score(
            self.bus_route,
            "Delay"
        )

        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)

    def test_delay_prioritizes_travel_time(self):
        faster_route = Route(
            source="Bengaluru",
            destination="Goa",
            transport="Train + Bus",
            duration_minutes=300,
            price=1400,
            transfers=2,
        )

        slower_route = Route(
            source="Bengaluru",
            destination="Goa",
            transport="Bus",
            duration_minutes=700,
            price=500,
            transfers=0,
        )

        faster_score = calculate_route_score(
            faster_route,
            "Delay"
        )

        slower_score = calculate_route_score(
            slower_route,
            "Delay"
        )

        self.assertLess(faster_score, slower_score)

    def test_missed_connection_prioritizes_fewer_transfers(self):
        direct_route = Route(
            source="Bengaluru",
            destination="Goa",
            transport="Bus",
            duration_minutes=700,
            price=1000,
            transfers=0,
        )

        connecting_route = Route(
            source="Bengaluru",
            destination="Goa",
            transport="Train + Bus",
            duration_minutes=500,
            price=500,
            transfers=2,
        )

        direct_score = calculate_route_score(
            direct_route,
            "Missed connection"
        )

        connecting_score = calculate_route_score(
            connecting_route,
            "Missed connection"
        )

        self.assertLess(direct_score, connecting_score)

    def test_score_is_a_float(self):
        score = calculate_route_score(
            self.bus_route,
            "Cancellation"
        )

        self.assertIsInstance(score, float)

    def test_reasons_include_budget_and_direct_journey(self):
        reasons = generate_route_reasons(
            self.bus_route,
            [self.bus_route, self.train_route],
            1000
        )

        self.assertIn(
            "Within your recovery budget.",
            reasons
        )

        self.assertIn(
            "Direct journey with no transfers.",
            reasons
        )


class JourneyRecoveryAPITests(RouteResQTestDataMixin, TestCase):
    """Test recovery requests and their recommendations."""

    def setUp(self):
        self.create_routes()
        self.url = reverse("recover_journey")

    def post_recovery(
        self,
        source="Bengaluru",
        destination="Goa",
        original_transport="Bus",
        disruption_type="Delay",
        budget=1500,
    ):
        payload = {
            "source": source,
            "destination": destination,
            "original_transport": original_transport,
            "disruption_type": disruption_type,
            "budget": budget,
        }

        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_bus_delay_returns_recovery_alternatives(self):
        response = self.post_recovery(
            original_transport="Bus",
            disruption_type="Delay",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["success"])
        self.assertGreater(data["count"], 0)

        self.assertEqual(
            data["routes"][0]["recommendation"],
            "Top match based on the weighted scoring formula."
        )

    def test_train_cancellation_excludes_train_only_routes(self):
        response = self.post_recovery(
            original_transport="Train",
            disruption_type="Cancellation",
        )

        self.assertEqual(response.status_code, 200)

        for route in response.json()["routes"]:
            self.assertNotEqual(route["transport"], "Train")

    def test_missed_connection_returns_ranked_results(self):
        response = self.post_recovery(
            original_transport="Bus",
            disruption_type="Missed connection",
        )

        self.assertEqual(response.status_code, 200)

        routes = response.json()["routes"]
        scores = [route["score"] for route in routes]

        self.assertEqual(scores, sorted(scores))

    def test_all_results_stay_within_budget(self):
        response = self.post_recovery(budget=800)

        self.assertEqual(response.status_code, 200)

        for route in response.json()["routes"]:
            self.assertLessEqual(route["price"], 800)

    def test_low_budget_returns_no_alternatives(self):
        response = self.post_recovery(budget=100)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["count"], 0)
        self.assertEqual(data["routes"], [])
        self.assertIn("No alternative routes", data["message"])

    def test_missing_source_returns_bad_request(self):
        response = self.post_recovery(source="")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_same_source_and_destination_returns_bad_request(self):
        response = self.post_recovery(
            source="Bengaluru",
            destination="BENGALURU",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("different", response.json()["error"])

    def test_zero_budget_returns_bad_request(self):
        response = self.post_recovery(budget=0)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Budget", response.json()["error"])

    def test_negative_budget_returns_bad_request(self):
        response = self.post_recovery(budget=-100)

        self.assertEqual(response.status_code, 400)

    def test_invalid_transport_returns_bad_request(self):
        response = self.post_recovery(
            original_transport="Flight"
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_disruption_returns_bad_request(self):
        response = self.post_recovery(
            disruption_type="Earthquake"
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_json_returns_bad_request(self):
        response = self.client.post(
            self.url,
            data="{invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_recovery_rejects_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_response_includes_sample_data_notice(self):
        response = self.post_recovery()

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "illustrative sample data",
            response.json()["data_notice"]
        )
