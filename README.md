# RouteResQ — Intelligent Journey Recovery System

**RouteResQ** is a web-based journey recovery application designed to help travellers find alternative transportation options when their original journey is disrupted by delays, cancellations, or missed connections.

The application uses a rule-based, weighted scoring algorithm to rank alternative routes according to travel time, fare, and number of transfers. It also considers the disruption type when prioritising alternatives.

> **Data notice:** The current version uses illustrative sample route data. It does not provide live transport schedules, real-time disruption alerts, or verified current fares.

## Problem Statement

Travel disruptions can leave passengers struggling to find suitable alternatives within their budget and time constraints. Comparing multiple transportation options manually can be time-consuming.

RouteResQ addresses this problem by filtering and ranking available alternative routes based on a traveller's preferences and the type of disruption.

## Key Features

* **Journey Recovery:** Recommends alternatives for delays, cancellations, and missed connections.
* **Budget-Based Filtering:** Excludes routes that exceed the specified budget.
* **Weighted Route Ranking:** Evaluates alternatives using travel time, fare, and number of transfers.
* **Disruption-Aware Recommendations:** Adjusts scoring priorities according to the disruption type.
* **Alternative Route Comparison:** Returns ranked alternatives with scores and explanations.
* **REST API:** Uses Django REST Framework-style JSON responses through Django API views.
* **Responsive Interface:** Provides a web interface designed to work across desktop and mobile screen sizes.

## Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Django
* Django REST Framework

### Database

* SQLite

### Development Tools

* Visual Studio Code
* Git and GitHub

## How It Works

1. The traveller provides journey details and recovery preferences.
2. RouteResQ retrieves routes matching the source, destination, and budget constraints.
3. The application excludes routes that do not meet the recovery requirements, including alternatives using the same transport type as the disrupted journey.
4. Each remaining route receives a weighted score based on travel time, fare, and transfers.
5. The system sorts the alternatives by score and returns recommendations with explanatory reasons.

## Route Scoring Algorithm

RouteResQ uses a **custom rule-based weighted scoring algorithm**. A lower score indicates a better match under the selected scoring priorities.

### Normalised Metrics

The algorithm calculates three metrics:

* **Time score:** `min(duration_minutes / 720, 1)`
* **Fare score:** `min(price / 1500, 1)`
* **Transfer score:** `min(transfers / 2, 1)`

### Default Weights

| Metric      | Weight |
| ----------- | -----: |
| Travel time |   0.50 |
| Fare        |   0.30 |
| Transfers   |   0.20 |

### Disruption-Specific Weights

| Disruption type   | Time | Fare | Transfers |
| ----------------- | ---: | ---: | --------: |
| Delay             | 0.70 | 0.20 |      0.10 |
| Cancellation      | 0.40 | 0.30 |      0.30 |
| Missed connection | 0.30 | 0.20 |      0.50 |

The weighted score is calculated as:

`Score = (Time score × Time weight) + (Fare score × Fare weight) + (Transfer score × Transfer weight)`

The system sorts routes in ascending score order. It also generates reasons to explain why a route may be suitable, such as fitting within the budget or being among the faster or cheaper alternatives.

**Algorithm note:** This is a rule-based scoring approach, not a machine-learning prediction model or a graph-search algorithm such as Dijkstra's or A*.

## Project Structure

```text
RouteResQ/
├── config/
│   ├── settings.py
│   └── urls.py
├── journeys/
│   ├── migrations/
│   ├── tests.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── venv/
├── index.html
├── style.css
├── script.js
├── manage.py
├── db.sqlite3
└── README.md
```

*Note: The structure above highlights the main project files. Your local project may contain additional files.*

## API Endpoints

| Endpoint         | Method | Purpose                                           |
| ---------------- | ------ | ------------------------------------------------- |
| `/api/`          | GET    | API home or status information                    |
| `/api/routes/`   | GET    | Retrieve available routes, with supported filters |
| `/api/recovery/` | POST   | Generate ranked journey recovery recommendations  |

### Example Recovery Request

```json
{
  "source": "Bengaluru",
  "destination": "Goa",
  "budget": 1200,
  "original_transport": "Bus",
  "disruption_type": "Delay"
}
```

The recovery endpoint returns matching alternatives, scores, recommendation labels, explanatory reasons, and a data notice.

*The example illustrates the request format; the actual response depends on the current database and API implementation.*

## Getting Started

### Prerequisites

* Python 3.11 or a compatible Python version
* pip
* Visual Studio Code or another code editor

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd RouteResQ
```

Replace the placeholder with your actual GitHub repository URL.

### 2. Create and Activate a Virtual Environment

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

If a `requirements.txt` file is available:

```bash
pip install -r requirements.txt
```

Otherwise, install the packages required by your project, including Django, Django REST Framework, and django-cors-headers, as applicable to your configuration.

### 4. Apply Database Migrations

```bash
python manage.py migrate
```

### 5. Start the Backend

```bash
python manage.py runserver
```

The backend will normally be available at:

`http://127.0.0.1:8000/`

### 6. Start the Frontend

Open the project folder in Visual Studio Code and launch `index.html` using the Live Server extension.

The frontend will typically be available at:

`http://127.0.0.1:5500/`

Keep the backend running while using the frontend.

## Testing

The project includes automated tests covering areas such as:

* API endpoints
* Route retrieval
* Route scoring
* Journey recovery behaviour

The test suite has been run during development.

To execute the tests in a fresh environment:

```bash
python manage.py test journeys
```

## Current Limitations

* Route information is illustrative sample data rather than live transport information.
* The application does not currently integrate with official transport booking services.
* Recommendations are based on a configurable weighted scoring algorithm.
* The quality of recommendations depends on the routes available in the database.

## Future Enhancements

* Integrate verified transport APIs for live schedules and fares.
* Add real-time delay and cancellation notifications.
* Incorporate connection-risk estimation and estimated arrival times.
* Add map-based route visualisation.
* Improve route recommendations using historical journey data.
* Add user accounts and saved journeys.
* Deploy the application with a production-ready database and hosting configuration.

## Author

**Laxmi Sonnad**


