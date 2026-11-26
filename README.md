# HubSpot GTM Engagement Signal

A Python-based integration that retrieves sales engagement activity from HubSpot, transforms it into account-level engagement signals, and writes an engagement score back to HubSpot.

The project explores practical GTM engineering concepts, including API integration, CRM data modeling, pagination, activity classification, and reliable data synchronization.

## Project Overview

Sales and customer-facing teams generate activity across calls, emails, and meetings. However, individual activity records don't necessarily represent meaningful customer engagement.

This project aims to distinguish genuine customer interaction from outbound sales activity and consolidate those signals into a single account-level engagement score.

The current workflow is:

1. Retrieve engagement records from HubSpot.
2. Associate activities with their respective companies.
3. Classify activities based on their type, direction, and outcome.
4. Calculate engagement using activity volume, recency, and frequency.
5. Generate a normalized engagement score between 0 and 100.
6. Write the resulting score back to the associated HubSpot company.

## Technology Stack

- **Python** — API integration and business logic
- **Requests** — HTTP communication with HubSpot
- **python-dotenv** — Environment variable management
- **HubSpot CRM API** — Company and engagement data retrieval and writeback

## Current Implementation

### HubSpot API Client

A reusable `HubSpotClient` handles authentication, HTTP requests, and communication with HubSpot's CRM API.

Implemented functionality includes:

- Session-based authentication using a HubSpot service key stored in an environment variable.
- Reusable HTTP request handling.
- Company retrieval and property updates.
- Company lookup by domain.
- Paginated company retrieval.
- Generic paginated engagement retrieval.

### Engagement Retrieval

A shared `get_engagements()` method retrieves paginated records from different HubSpot engagement endpoints.

Supported engagement types:

- Calls
- Emails
- Meetings

The method supports configurable properties and associations, allowing the same retrieval logic to be reused across different CRM objects.

### Activity Classification

The project distinguishes customer engagement from sales outreach.

| Activity | Classification | Treatment |
|---|---|---|
| Connected call | Meaningful interaction | Positive signal |
| Other call dispositions | Outreach or unsuccessful attempt | No meaningful-interaction credit |
| Incoming email | Customer engagement | Secondary positive signal |
| Outgoing email | Sales outreach | No engagement credit |
| Forwarded email | Not a new interaction | Excluded |
| Completed meeting | Meaningful interaction | Positive signal |
| Scheduled meeting | Not yet completed | No credit |
| Rescheduled meeting | Not completed | No credit |
| No-show meeting | No completed interaction | No credit |
| Canceled meeting | No completed interaction | No credit |

Activities without an associated company are excluded from company-level scoring rather than being attributed through assumptions.

## Engagement Scoring

The scoring model will account for:

- **Recency:** How recently meaningful customer interactions occurred.
- **Activity frequency:** The frequency of meaningful interactions over a defined time window.
- **Activity type:** Different weights for calls, meetings, and incoming emails.
- **Diminishing returns:** Preventing unusually high activity volumes from disproportionately inflating an account's score.

The intended output is a normalized engagement score from 0 to 100, stored in a custom HubSpot company property.

## Reliability and Engineering Practices

The project is being developed incrementally with an emphasis on reusable code and reliable API interactions.

Implemented:

- Reusable HTTP session.
- Cursor-based pagination.
- HTTP error handling.
- Retry logic for rate limits and transient server errors.
- Exponential backoff.
- Respect HubSpot `Retry-After` headers.
- Automated tests.
- Application logging.

Planned improvements:

- Safe retry behavior for write operations.
- Idempotent synchronization.
- Architecture Documentation

## Local Setup

### Prerequisites

- Python 3.10+
- A HubSpot developer or test account.
- A HubSpot service key with the required CRM scopes.

### Installation

Clone the repository:

```bash
git clone https://github.com/mathcoder3141/hubspot_gtm_signal.git
cd hubspot_gtm_signal
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
HUBSPOT_SERVICE_API_KEY=your_service_key
```

Ensure `.env` is included in `.gitignore`. Never commit API credentials.

## Project Structure

```text
hubspot_gtm_signal/
├── README.md
├── main.py
├── pytest.ini
├── requirements.txt
├── src
│   └── hubspot
│       ├── __init__.py
│       ├── client.py
│       ├── pipeline.py
│       └── scoring.py
└── tests
    └── test_scoring.py
    └── test_client.py
```

## Roadmap

- [x] HubSpot API authentication
- [x] Reusable API client
- [x] Company retrieval and property updates
- [x] Company pagination
- [x] Company lookup by domain
- [x] Generic paginated engagement retrieval
- [x] Call, email, and meeting activity inspection
- [x] Initial activity classification rules
- [x] Basic retry logic with exponential backoff
- [x] Engagement scoring model
- [x] Account-level activity aggregation
- [x] HubSpot score writeback workflow
- [x] Retry-After header support
- [ ] Safe write retries and idempotency
- [x] Application logging
- [x] Automated tests
- [ ] End-to-end demonstration
- [ ] Architecture documentation

## Project Goals

Beyond producing an engagement score, this project is an opportunity to explore the engineering considerations involved in building a practical GTM data integration:

- Working with third-party APIs and authentication.
- Handling pagination and API failures.
- Modeling relationships between CRM objects.
- Translating business definitions into data transformations.
- Designing reusable and maintainable Python components.
- Synchronizing derived data back into operational systems.
