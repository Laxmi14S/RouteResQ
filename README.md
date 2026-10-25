# RouteResQ — Intelligent Journey Recovery System

**When journeys go wrong, find your way forward.**

RouteResQ is a web-based journey recovery application designed to help travellers identify alternative transportation options when their original journey is disrupted by delays, cancellations, or missed connections.

The application filters available routes according to the traveller's destination and budget, then ranks eligible alternatives using a disruption-aware weighted scoring algorithm. Recommendations include scores and explanations to help users compare their options.

**Project repository:** https://github.com/Laxmi14S/RouteResQ

> **Data notice:** The current implementation uses illustrative sample route data. It does not provide live transport schedules, real-time disruption alerts, verified current fares, or transport bookings.

## Table of Contents

* [Problem Statement](#problem-statement)
* [Key Features](#key-features)
* [Technology Stack](#technology-stack)
* [How It Works](#how-it-works)
* [Route Scoring Algorithm](#route-scoring-algorithm)
* [Project Structure](#project-structure)
* [API Documentation](#api-documentation)
* [Getting Started](#getting-started)
* [Running Tests](#running-tests)
* [Current Limitations](#current-limitations)
* [Future Enhancements](#future-enhancements)
* [Author](#author)

## Problem Statement

Unexpected travel disruptions can leave passengers struggling to find alternative transportation within their budget and time constraints.

When a bus or train is delayed or cancelled, travellers may need to compare alternative routes, fares, journey durations, and transfers manually.

RouteResQ addresses this problem by providing a structured journey recovery workflow. It evaluates the available alternatives and ranks them according to the type of disruption and the traveller's budget.

## Key Features

* **Journey Recovery:** Generates alternative route recommendations for delays, cancellations, and missed connections.
* **Budget-Based Filtering:** Excludes routes that exceed the specified recovery budget.
* **Disruption-Aware Ranking:** Adjusts scoring priorities according to the disruption type.
* **Weighted Route Scoring:** Evaluates alternatives using travel duration, fare, and number of transfers.
* **Alternative Route Comparison:** Returns ranked alternatives with scores and explanatory reasons.
* **Transport-Type Filtering:** Excludes alternatives using the same transport type as the disrupted journey.
* **REST-Style JSON API:** Provides endpoints for retrieving routes and requesting recovery recommendations.
* **Responsive User Interface:** Uses HTML, CSS, and JavaScript to provide a web-based journey planning experience.

## Technology Stack

| Component               | Technology                            |
| ----------------------- | ------------------------------------- |
| Frontend                | HTML5, CSS3, JavaScript               |
| Backend                 | Python, Django                        |
| Database                | SQLite                                |
| API                     | Django views returning JSON responses |
| Cross-Origin Requests   | django-cors-headers                   |
| Testing                 | Django automated test framework       |
| Version Control         | Git and GitHub                        |
| Development Environment | Visual Studio Code                    |

## How It Works

RouteResQ follows a structured journey recovery process:

1. **Collect journey details:** The traveller enters the source, destination, recovery budget, original transport type, and disruption type.
2. **Retrieve available routes:** The backend obtains routes matching the requested journey.
3. **Filter alternatives:** Routes that exceed the budget or fail the recovery requirements are excluded.
4. **Calculate scores:** Each eligible route receives a weighted score based on journey duration, fare, and number of transfers.
5. **Rank alternatives:** Routes are sorted by score, with lower scores representing better matches under the selected priorities.
6. **Explain recommendations:** The API returns recommendation labels, scores, explanatory reasons, and a notice about the sample data.

## Route Scoring Algorithm

RouteResQ uses a **custom, rule-based weighted scoring algorithm** to rank eligible routes.

It is not a machine-learning model. It does not currently use Dijkstra's algorithm, A*, or another graph-search algorithm.

### 1. Normalised Metrics

The algorithm calculates three normalised metrics:

**Time score**

```python
min(duration_minutes / 720, 1)
```

**Fare score**

```python
min(price / 1500, 1)
```

**Transfer score**

```python
min(transfers / 2, 1)
```

These calculations cap each metric at `1`, providing bounded inputs for the weighted scoring formula.

### 2. Default Weights

| Metric              | Weight |
| ------------------- | -----: |
| Travel time         |   0.50 |
| Fare                |   0.30 |
| Number of transfers |   0.20 |

### 3. Disruption-Specific Weights

The algorithm changes the relative importance of each metric depending on the disruption type.

| Disruption Type   | Time Weight | Fare Weight | Transfer Weight |
| ----------------- | ----------: | ----------: | --------------: |
| Delay             |        0.70 |        0.20 |            0.10 |
| Cancellation      |        0.40 |        0.30 |            0.30 |
| Missed connection |        0.30 |        0.20 |            0.50 |

For example, when a delay occurs, travel time receives the highest weight. When a connection is missed, the number of transfers receives greater weight.

### 4. Weighted Score Formula

The algorithm calculates the score as follows:

```text
Score =
    (Time Score × Time Weight)
  + (Fare Score × Fare Weight)
  + (Transfer Score × Transfer Weight)
```

The system sorts eligible routes in ascending order of their scores.

A lower score indicates a better match according to the selected weights. The result is a rule-based ranking, not a guarantee that a route is objectively optimal.

### 5. Explainable Recommendations

Alongside the scores, RouteResQ provides explanatory reasons to help users understand why an alternative may be suitable.

These may include whether a route is within budget and whether it is among the faster or cheaper alternatives.

## Project Structure

```text
RouteResQ/
├── config/
│   ├── settings.py
│   └── urls.py
├── journeys/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
├── index.html
├── style.css
├── script.js
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
```

The project may contain additional Django configuration, migration, and development files.

The `venv/` directory and local SQLite database are intentionally excluded from version control by the project's `.gitignore`.

## API Documentation

RouteResQ exposes endpoints for retrieving route information and requesting journey recovery recommendations.

| Endpoint         | Method | Purpose                                          |
| ---------------- | ------ | ------------------------------------------------ |
| `/api/`          | GET    | API home or status information                   |
| `/api/routes/`   | GET    | Retrieve available routes with supported filters |
| `/api/recovery/` | POST   | Generate ranked journey recovery recommendations |

### Example Recovery Request

A recovery request can use the following JSON structure:

```json
{
  "source": "Bengaluru",
  "destination": "Goa",
  "budget": 1200,
  "original_transport": "Bus",
  "disruption_type": "Delay"
}
```

This example illustrates the request format. The actual response depends on the routes available in the database and the backend's filtering and scoring logic.

### Recovery Response

The recovery endpoint returns information about eligible alternatives, including fields such as:

* Route details
* Recommendation label
* Weighted score
* Explanatory reasons
* Data notice

The API uses the configured Django views to process requests and return JSON responses.

## Getting Started

Follow these instructions to run RouteResQ locally on Windows.

### Prerequisites

Install the following tools:

* Python 3.11 or a compatible Python version
* pip
* Visual Studio Code or another code editor
* The Live Server extension for VS Code, or an equivalent way to serve the frontend

### 1. Clone the Repository

Open PowerShell and run:

```powershell
git clone https://github.com/Laxmi14S/RouteResQ.git
cd RouteResQ
```

### 2. Create a Virtual Environment

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use an appropriate activation method for your Windows environment.

### 3. Install Dependencies

Install the packages listed in `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

The current dependency file includes Django, django-cors-headers, and their supporting packages.

### 4. Prepare the Database

Apply the database migrations:

```powershell
python manage.py migrate
```

**Sample-data note:** The local SQLite database is excluded from GitHub. Applying migrations creates the database schema, but it does not automatically populate the illustrative route records. The current project requires its sample route data to be added through the appropriate database setup process.

### 5. Start the Backend

From the directory containing `manage.py`, run:

```powershell
python manage.py runserver
```

By default, the Django development server runs at:

```text
http://127.0.0.1:8000/
```

### 6. Start the Frontend

Open the project directory in Visual Studio Code.

Launch `index.html` using the Live Server extension.

The frontend will typically be available at:

```text
http://127.0.0.1:5500/
```

Keep the Django backend running while using the frontend.

The frontend's configured API address and the CORS settings must match the environment in which the application is running.

## Running Tests

RouteResQ includes automated tests covering areas such as:

* API endpoint behaviour
* Route retrieval
* Route scoring
* Journey recovery scenarios

Run the Django test suite with:

```powershell
python manage.py test journeys
```

The project test suite has been executed during development. The command above can be used to run it again after setting up the project in a new environment.

## Current Limitations

The current implementation has the following limitations:

* Route information is based on illustrative sample data rather than live transport information.
* Live train and bus schedules are not integrated.
* Real-time delay and cancellation alerts are not available.
* The application does not currently book tickets or integrate with official transport booking services.
* Recommendations depend on the route records available in the database.
* The weighted scoring algorithm uses predefined rules rather than learned predictions.
* Applying database migrations alone does not populate the sample routes.

These limitations define the current implementation and provide opportunities for further development.

## Future Enhancements

Potential improvements include:

### Transport Data Integration

* Integrate suitable transport APIs for verified schedules and fares.
* Introduce real-time disruption information where reliable data sources are available.
* Improve handling of unavailable or outdated route information.

### Journey Recovery

* Add connection-risk estimation based on arrival and departure times.
* Estimate the impact of delays on connecting journeys.
* Support richer multi-leg and multi-modal journey comparisons.

### User Experience

* Add map-based route visualisation.
* Allow users to save and revisit journey plans.
* Improve accessibility and provide clearer explanations for route recommendations.

### Engineering and Deployment

* Add a repeatable sample-data seeding command.
* Expand automated testing for edge cases and invalid requests.
* Deploy the application with production-appropriate settings and hosting.
* Evaluate the use of a production-ready database.

### Recommendation Improvements

* Evaluate the scoring algorithm against realistic travel scenarios.
* Allow users to customise the relative importance of time, cost, and transfers.
* Explore historical journey data if suitable data becomes available.

These are proposed enhancements, not claims about features already implemented.

## Author

**Laxmi Sonnad**

B.E. in Artificial Intelligence and Data Science

GitHub: https://github.com/Laxmi14S/RouteResQ


