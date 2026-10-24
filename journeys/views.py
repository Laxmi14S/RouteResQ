from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Route


# ============================================
# 1. Retrieve available routes
# ============================================

@require_GET
def route_list(request):
    source = request.GET.get("source", "").strip()
    destination = request.GET.get("destination", "").strip()
    budget = request.GET.get("budget", "").strip()
    transport = request.GET.get("transport", "").strip()

    routes = Route.objects.all()

    if source:
        routes = routes.filter(source__iexact=source)

    if destination:
        routes = routes.filter(destination__iexact=destination)

    if budget:
        try:
            budget_value = int(budget)

            if budget_value < 0:
                return JsonResponse(
                    {"error": "Budget cannot be negative."},
                    status=400
                )

            routes = routes.filter(price__lte=budget_value)

        except ValueError:
            return JsonResponse(
                {"error": "Budget must be a valid number."},
                status=400
            )

    if transport:
        routes = routes.filter(transport__iexact=transport)

    data = [
        {
            "id": route.id,
            "source": route.source,
            "destination": route.destination,
            "transport": route.transport,
            "duration_minutes": route.duration_minutes,
            "price": route.price,
            "transfers": route.transfers,
            "description": route.description,
        }
        for route in routes.order_by("price")
    ]

    return JsonResponse({
        "count": len(data),
        "routes": data
    })


# ============================================
# 2. API home endpoint
# ============================================

@require_GET
def api_home(request):
    return JsonResponse({
        "message": "Welcome to the RouteResQ API!",
        "description": "Find alternative routes for disrupted journeys.",
        "routes_endpoint": "/api/routes/",
        "recovery_endpoint": "/api/recovery/"
    })


# ============================================
# 3. Calculate a recovery route score
# ============================================

def calculate_route_score(route, disruption_type):
    """
    Calculate a normalized weighted score.
    A lower score indicates a better-ranked route.
    """

    # Reference values for normalization.
    reference_duration = 720
    reference_fare = 1500
    reference_transfers = 2

    # Normalize the route factors.
    time_score = min(
        route.duration_minutes / reference_duration, 1
    )

    fare_score = min(
        route.price / reference_fare, 1
    )

    transfer_score = min(
        route.transfers / reference_transfers, 1
    )

    # Default weights.
    time_weight = 0.50
    fare_weight = 0.30
    transfer_weight = 0.20

    # Prioritize travel time for delays.
    if disruption_type == "Delay":
        time_weight = 0.70
        fare_weight = 0.20
        transfer_weight = 0.10

    # Balance time, fare and transfers for cancellations.
    elif disruption_type == "Cancellation":
        time_weight = 0.40
        fare_weight = 0.30
        transfer_weight = 0.30

    # Prioritize fewer transfers after a missed connection.
    elif disruption_type == "Missed connection":
        time_weight = 0.30
        fare_weight = 0.20
        transfer_weight = 0.50

    # Calculate the final score.
    score = (
        time_weight * time_score
        + fare_weight * fare_score
        + transfer_weight * transfer_score
    )

    return score


# ============================================
# 4. Generate recommendation explanations
# ============================================

def generate_route_reasons(route, alternatives, budget):
    """
    Generate explanations based on the available route data.
    """

    reasons = []

    # All returned alternatives have passed the budget filter.
    if route.price <= budget:
        reasons.append("Within your recovery budget.")

    # Compare journey duration with other available alternatives.
    fastest_duration = min(
        item.duration_minutes for item in alternatives
    )

    if route.duration_minutes == fastest_duration:
        reasons.append("One of the fastest available alternatives.")

    # Compare fare with other available alternatives.
    cheapest_fare = min(
        item.price for item in alternatives
    )

    if route.price == cheapest_fare:
        reasons.append("One of the cheapest available alternatives.")

    # Explain the number of transfers.
    if route.transfers == 0:
        reasons.append("Direct journey with no transfers.")
    elif route.transfers == 1:
        reasons.append("Requires only one transfer.")
    else:
        reasons.append(
            f"Requires {route.transfers} transfers."
        )

    return reasons


# ============================================
# 5. Recommend recovery journeys
# ============================================

@csrf_exempt
@require_POST
def recover_journey(request):
    try:
        # Read the JSON request from the frontend.
        payload = json.loads(request.body)

        source = payload.get("source", "").strip()
        destination = payload.get("destination", "").strip()

        original_transport = payload.get(
            "original_transport", ""
        ).strip()

        disruption_type = payload.get(
            "disruption_type", ""
        ).strip()

        budget = int(payload.get("budget", 0))

        # Validate source and destination.
        if not source or not destination:
            return JsonResponse(
                {"error": "Source and destination are required."},
                status=400
            )

        if source.casefold() == destination.casefold():
            return JsonResponse(
                {
                    "error": (
                        "Source and destination must be different."
                    )
                },
                status=400
            )

        # Validate budget.
        if budget <= 0:
            return JsonResponse(
                {"error": "Budget must be greater than zero."},
                status=400
            )

        # Validate affected transport.
        if original_transport not in ["Bus", "Train"]:
            return JsonResponse(
                {
                    "error": (
                        "Select Bus or Train as the affected transport."
                    )
                },
                status=400
            )

        # Validate disruption type.
        valid_disruptions = [
            "Delay",
            "Cancellation",
            "Missed connection"
        ]

        if disruption_type not in valid_disruptions:
            return JsonResponse(
                {"error": "Select a valid disruption type."},
                status=400
            )

        # Find routes for the requested journey within budget.
        routes = Route.objects.filter(
            source__iexact=source,
            destination__iexact=destination,
            price__lte=budget
        )

        # Exclude routes using the affected transport alone.
        alternatives = []

        for route in routes:
            if route.transport == original_transport:
                continue

            alternatives.append(route)

        # Rank alternatives using the weighted scoring algorithm.
        alternatives.sort(
            key=lambda route: calculate_route_score(
                route,
                disruption_type
            )
        )

        # Build the response.
        results = []

        for index, route in enumerate(alternatives):

            # Explain why this route may be a good option.
            reasons = generate_route_reasons(
                route,
                alternatives,
                budget
            )

            # Set the recommendation label.
            if index == 0:
                recommendation = (
                    "Top match based on the weighted scoring formula."
                )
            else:
                recommendation = (
                    "Alternative within your recovery budget."
                )

            results.append({
                "id": route.id,
                "source": route.source,
                "destination": route.destination,
                "transport": route.transport,
                "duration_minutes": route.duration_minutes,
                "price": route.price,
                "transfers": route.transfers,
                "description": route.description,
                "recommendation": recommendation,
                "reasons": reasons,
                "score": round(
                    calculate_route_score(
                        route,
                        disruption_type
                    ),
                    3
                )
            })

        # Return the results to the frontend.
        return JsonResponse({
            "success": True,
            "disruption_type": disruption_type,
            "original_transport": original_transport,
            "budget": budget,
            "count": len(results),
            "message": (
                "Recovery alternatives found."
                if results
                else "No alternative routes match your budget."
            ),
            "routes": results,
            "data_notice": (
                "Recommendations use illustrative sample data, "
                "not live transport schedules or availability."
            )
        })

    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse(
            {
                "error": (
                    "Invalid recovery request. "
                    "Check the submitted values."
                )
            },
            status=400
        )
