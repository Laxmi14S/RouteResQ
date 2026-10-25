// ============================================
// RouteResQ - Frontend JavaScript
// Connected to the Django REST-style API
// ============================================

const API_BASE_URL = "http://127.0.0.1:8000/api";

// HTML elements
const form = document.getElementById("searchForm");
const sourceInput = document.getElementById("source");
const destinationInput = document.getElementById("destination");
const dateInput = document.getElementById("travelDate");
const budgetInput = document.getElementById("budget");
const sortSelect = document.getElementById("sortBy");
const routeGrid = document.getElementById("routeGrid");
const summary = document.getElementById("resultsSummary");

let displayedRoutes = [];
let recoveryRankedRoutes = [];
let currentResultsMode = "search";
let currentJourney = null;
let isLoading = false;

// ============================================
// 1. Set today's date as the default travel date
// ============================================

const today = new Date();

const localToday = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0")
].join("-");

dateInput.min = localToday;
dateInput.value = localToday;


// ============================================
// 2. Swap source and destination
// ============================================

document.getElementById("swapBtn").addEventListener("click", () => {
    const previousSource = sourceInput.value;

    sourceInput.value = destinationInput.value;
    destinationInput.value = previousSource;
});


// ============================================
// 3. Format journey duration
// ============================================

function formatDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;

    if (remainingMinutes === 0) {
        return `${hours}h`;
    }

    if (hours === 0) {
        return `${remainingMinutes}m`;
    }

    return `${hours}h ${remainingMinutes}m`;
}


// ============================================
// 4. Convert API data into frontend format
// ============================================

function normalizeRoute(route) {
    return {
        id: route.id,
        source: route.source,
        destination: route.destination,
        transport: route.transport,
        duration: route.duration_minutes,
        fare: route.price,
        transfers: route.transfers,
        label: route.description || route.transport,
        description: route.description || "",
        recommendation: route.recommendation || "",
        reasons: Array.isArray(route.reasons) ? route.reasons : [],
        score: route.score
    };
}


// ============================================
// 5. Calculate recommendation score
// Used for normal route search only
// Lower score means a better balance of time and fare
// ============================================

function getRecommendationScore(route) {
    return route.duration / 60 + route.fare / 200;
}


// ============================================
// 6. Sort available routes
// ============================================

function sortRoutes() {

    // For recovery results, preserve Django's ranking
    // when the user selects Recommended.
    if (
        sortSelect.value === "recommended" &&
        currentResultsMode === "recovery"
    ) {
        displayedRoutes = [...recoveryRankedRoutes];
        return;
    }

    if (sortSelect.value === "price") {

        displayedRoutes.sort((a, b) => a.fare - b.fare);

    } else if (sortSelect.value === "duration") {

        displayedRoutes.sort((a, b) => a.duration - b.duration);

    } else {

        displayedRoutes.sort(
            (a, b) =>
                getRecommendationScore(a) -
                getRecommendationScore(b)
        );
    }
}


// ============================================
// 7. Display routes on the webpage
// ============================================

function renderRoutes() {

    routeGrid.innerHTML = "";

    // Show an empty state if no routes are available.
    if (displayedRoutes.length === 0) {

        routeGrid.innerHTML = `
            <div class="empty-state">
                No sample routes match your search and budget.
                Try another journey or increase your budget.
            </div>
        `;

        return;
    }

    displayedRoutes.forEach((route, index) => {

        const card = document.createElement("article");

        card.className = "route-card";

        // Highlight the first result when using recommended sorting.
        if (
            index === 0 &&
            sortSelect.value === "recommended"
        ) {
            card.classList.add("recommended");
        }

        // Set the card badge.
        const badge =
            index === 0 && sortSelect.value === "recommended"
                ? "TOP MATCH"
                : currentResultsMode === "recovery"
                    ? "ALTERNATIVE"
                    : "ROUTE OPTION";

        // Display the number of transfers.
        const transferText = route.transfers === 0
            ? "Direct journey"
            : `${route.transfers} transfer(s)`;

        // Recommendation message returned by Django.
        const recommendationText = route.recommendation || "";

        // Display reasons returned by Django.
        const reasonsHtml = route.reasons.length
            ? `
                <div class="route-reasons">
                    <strong>Why this route?</strong>

                    <ul>
                        ${route.reasons.map(reason => `
                            <li>${reason}</li>
                        `).join("")}
                    </ul>
                </div>
            `
            : "";

        // Display the sample route description during normal search.
        const descriptionHtml =
            route.description && currentResultsMode !== "recovery"
                ? `
                    <p class="route-description">
                        ${route.description}
                    </p>
                `
                : "";

        // Build the route card.
        card.innerHTML = `
            <span class="route-label">${badge}</span>

            <h3>${route.transport}</h3>

            <p class="route-type">
                ${currentJourney.source}
                →
                ${currentJourney.destination}
            </p>

            <div class="route-metrics">

                <div>
                    <span class="metric-label">
                        ESTIMATED TIME
                    </span>

                    <span class="metric-value">
                        ${formatDuration(route.duration)}
                    </span>
                </div>

                <div>
                    <span class="metric-label">
                        SAMPLE FARE
                    </span>

                    <span class="metric-value">
                        ₹${route.fare.toLocaleString("en-IN")}
                    </span>
                </div>

            </div>

            <p class="route-transfers">
                ${transferText}
            </p>

            ${descriptionHtml}

            ${reasonsHtml}

            ${
                recommendationText
                    ? `
                        <p class="route-recommendation">
                            ${recommendationText}
                        </p>
                    `
                    : ""
            }

            <button
                class="route-action"
                type="button"
                data-route-id="${route.id}"
            >
                View journey details →
            </button>
        `;

        routeGrid.appendChild(card);
    });
}


// ============================================
// 8. Fetch matching routes from Django
// ============================================

async function fetchRoutes({
    source,
    destination,
    budget,
    transport = ""
}) {

    const params = new URLSearchParams({
        source: source,
        destination: destination,
        budget: String(budget)
    });

    if (transport) {
        params.set("transport", transport);
    }

    const response = await fetch(
        `${API_BASE_URL}/routes/?${params.toString()}`
    );

    if (!response.ok) {
        throw new Error(
            `Route API returned HTTP ${response.status}`
        );
    }

    const data = await response.json();

    if (!Array.isArray(data.routes)) {
        throw new Error(
            "The route API returned an unexpected response."
        );
    }

    return data.routes.map(normalizeRoute);
}


// ============================================
// 9. Validate journey search inputs
// ============================================

function validateJourney(source, destination, budget) {

    if (
        !source ||
        !destination ||
        source.toLowerCase() === destination.toLowerCase()
    ) {
        alert(
            "Please enter two different starting and destination cities."
        );

        return false;
    }

    if (!Number.isFinite(budget) || budget <= 0) {
        alert(
            "Please enter a valid budget greater than zero."
        );

        return false;
    }

    return true;
}


// ============================================
// 10. Search for alternative journeys
// ============================================

form.addEventListener("submit", async (event) => {

    event.preventDefault();

    if (isLoading) {
        return;
    }

    const source = sourceInput.value.trim();
    const destination = destinationInput.value.trim();
    const budget = Number(budgetInput.value);

    if (!validateJourney(source, destination, budget)) {
        return;
    }

    currentJourney = {
        source,
        destination,
        budget
    };

    sortSelect.value = "recommended";

    isLoading = true;

    summary.textContent =
        "Searching the RouteResQ database...";

    routeGrid.innerHTML = `
        <div class="empty-state">
            Finding matching sample routes...
        </div>
    `;

    try {

        currentResultsMode = "search";

        recoveryRankedRoutes = [];

        displayedRoutes = await fetchRoutes({
            source,
            destination,
            budget
        });

        sortRoutes();

        summary.textContent =
            `${displayedRoutes.length} sample option(s) for ` +
            `${source} to ${destination}, within ₹${budget}.`;

        renderRoutes();

        document.getElementById("alternatives").scrollIntoView({
            behavior: "smooth"
        });

    } catch (error) {

        console.error("Route search failed:", error);

        displayedRoutes = [];

        recoveryRankedRoutes = [];

        currentResultsMode = "search";

        renderRoutes();

        summary.textContent =
            "Unable to retrieve routes from the backend.";

        routeGrid.innerHTML = `
            <div class="empty-state">
                Could not connect to the RouteResQ backend.
                Make sure Django is running at 127.0.0.1:8000
                and try again.
            </div>
        `;

    } finally {

        isLoading = false;
    }
});


// ============================================
// 11. Change the route sorting order
// ============================================

sortSelect.addEventListener("change", () => {

    if (!currentJourney) {
        return;
    }

    sortRoutes();

    renderRoutes();
});


// ============================================
// 12. View journey details
// ============================================

routeGrid.addEventListener("click", (event) => {

    const button = event.target.closest("[data-route-id]");

    if (!button || !currentJourney) {
        return;
    }

    const route = displayedRoutes.find(
        item => item.id === Number(button.dataset.routeId)
    );

    if (!route) {
        return;
    }

    alert(
        `Journey details\n\n` +
        `${currentJourney.source} → ${currentJourney.destination}\n` +
        `Transport: ${route.transport}\n` +
        `Estimated duration: ${formatDuration(route.duration)}\n` +
        `Illustrative fare: ₹${route.fare}\n` +
        `Transfers: ${route.transfers}\n\n` +
        `Demo data only. Verify real schedules and fares.`
    );
});


// ============================================
// 13. Journey disruption recovery
// Calls the Django recovery API
// ============================================

const disruptionForm = document.getElementById("disruptionForm");

disruptionForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const disruptionInput =
        document.getElementById("disruptionType").value;

    const transportInput =
        document.getElementById("originalTransport").value;

    const delay = Number(
        document.getElementById("delayDuration").value
    );

    const budget = Number(
        document.getElementById("recoveryBudget").value
    );

    const message =
        document.getElementById("recoveryMessage");


    // Validate the recovery budget.
    if (!Number.isFinite(budget) || budget <= 0) {

        message.textContent =
            "Please enter a valid recovery budget.";

        return;
    }


    // Get the journey details from the planner.
    const source = sourceInput.value.trim();

    const destination = destinationInput.value.trim();

    if (
        !source ||
        !destination ||
        source.toLowerCase() === destination.toLowerCase()
    ) {

        message.textContent =
            "Please enter two different cities in the journey planner first.";

        return;
    }


    // Normalize the selected disruption type.
    const normalizedDisruption = disruptionInput
        .trim()
        .toLowerCase()
        .replace(/[_-]+/g, " ");

    const disruptionMap = {
        "delay": "Delay",
        "delayed": "Delay",
        "cancellation": "Cancellation",
        "cancelled": "Cancellation",
        "canceled": "Cancellation",
        "missed connection": "Missed connection"
    };

    const disruptionType =
        disruptionMap[normalizedDisruption];

    if (!disruptionType) {

        message.textContent =
            "Please select a valid disruption type.";

        return;
    }


    // Normalize the affected transport.
    const normalizedTransport = transportInput
        .trim()
        .toLowerCase();

    let originalTransport;

    if (normalizedTransport.includes("bus")) {

        originalTransport = "Bus";

    } else if (normalizedTransport.includes("train")) {

        originalTransport = "Train";

    } else {

        message.textContent =
            "Please select Bus or Train as the affected transport.";

        return;
    }


    // Save the journey being recovered.
    currentJourney = {
        source,
        destination,
        budget
    };

    sortSelect.value = "recommended";

    message.textContent =
        "Analysing the disruption and finding alternatives...";


    try {

        // Send the recovery request to Django.
        const response = await fetch(
            `${API_BASE_URL}/recovery/`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    source,
                    destination,
                    original_transport: originalTransport,
                    disruption_type: disruptionType,
                    delay_minutes: delay,
                    budget
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error || "The recovery request failed."
            );
        }


        // Django has already ranked recovery routes using
        // the selected disruption type.
        // Preserve that order instead of applying the
        // frontend's general-purpose search score.
        currentResultsMode = "recovery";

        displayedRoutes = data.routes.map(normalizeRoute);

        recoveryRankedRoutes = [...displayedRoutes];


        // Update the results summary.
        summary.textContent =
            `${data.count} recovery option(s) for ` +
            `${source} to ${destination}, within ₹${budget}.`;


        // Display recovery results.
        renderRoutes();


        // Explain the outcome to the traveller.
        if (displayedRoutes.length > 0) {

            message.textContent =
                `Recovery analysis complete. ` +
                `${data.count} alternative(s) found. ` +
                `${data.data_notice || "Routes use illustrative sample data."}`;

        } else {

            message.textContent =
                "No alternative routes match your budget and " +
                "transport preference. Try increasing your budget.";
        }


        document.getElementById("alternatives").scrollIntoView({
            behavior: "smooth"
        });

    } catch (error) {

        console.error("Recovery request failed:", error);

        displayedRoutes = [];

        recoveryRankedRoutes = [];

        currentResultsMode = "recovery";

        renderRoutes();

        summary.textContent =
            "Recovery search failed.";

        message.textContent =
            `Unable to retrieve recovery options: ${error.message}`;
    }
});


// ============================================
// 14. Initial status
// ============================================

console.log(
    "RouteResQ frontend JavaScript loaded successfully."
);