from hubspot.scoring import (
    get_recency_multiplier,
    get_activity_weight,
    calculate_activity_points,
    score_activities,
    normalize_activities,
    group_activities_by_company,
    score_companies
)
from datetime import datetime, timezone

def test_recency_multiplier():
    assert get_recency_multiplier(3) == 1.0
    assert get_recency_multiplier(10) == 0.75
    assert get_recency_multiplier(20) == 0.5
    assert get_recency_multiplier(27) == 0.25
    assert get_recency_multiplier(31) == 0

def test_recency_multiplier_boundaries():
    assert get_recency_multiplier(7) == 1.0
    assert get_recency_multiplier(8) == 0.75
    assert get_recency_multiplier(14) == 0.75
    assert get_recency_multiplier(15) == 0.5
    assert get_recency_multiplier(21) == 0.5
    assert get_recency_multiplier(22) == 0.25
    assert get_recency_multiplier(30) == 0.25
    assert get_recency_multiplier(31) == 0

def test_meeting_weights():
    assert get_activity_weight("Meeting", 1) == 20
    assert get_activity_weight("Meeting", 2) == 15
    assert get_activity_weight("Meeting", 3) == 10
    assert get_activity_weight("Meeting", 4) == 5
    assert get_activity_weight("Meeting", 5) == 2
    assert get_activity_weight("Meeting", 10) == 2

def test_call_weights():
    assert get_activity_weight("Call", 1) == 10
    assert get_activity_weight("Call", 2) == 8
    assert get_activity_weight("Call", 3) == 6
    assert get_activity_weight("Call", 4) == 4
    assert get_activity_weight("Call", 5) == 2
    assert get_activity_weight("Call", 10) == 2

def test_email_weight():
    assert get_activity_weight("Email", 1) == 1
    assert get_activity_weight("Email", 10) == 1

def test_invalid_activity_weight():
    assert get_activity_weight("Slack", 1) == 0
    assert get_activity_weight("Meeting", 0) == 0
    assert get_activity_weight("Call", -1) == 0

def test_calculate_activity_points():
    points = calculate_activity_points(
        activity_type="Meeting",
        occurrence_number=1,
        age_in_days=10,
    )

    assert points == 15.0

def test_score_activities():
    activities = [
        {
            "activity_type": "Meeting",
            "hs_timestamp": "2026-11-22T12:00:00Z",
        },
        {
            "activity_type": "Call",
            "hs_timestamp": "2026-11-20T12:00:00Z",
        },
    ]
    now = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    score = score_activities(activities, now=now)
    assert score == 30.0

def test_score_point_cap():
    activities = [
        {
            "activity_type": "Meeting",
            "hs_timestamp": "2026-11-22T10:00:00Z"
        }
        for _ in range(30)
    ]
    now = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    score = score_activities(activities, now=now)
    assert score == 100.0

def test_connected_call_normalized():
    activities = [
        {
            "properties": {
                "hs_call_disposition": "f240bbac-87c9-4f6e-bf70-924b57d47db7",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": [
                        {"id": "123"}
                    ]
                }
            }
        }
    ]

    normalized = [
        {
            "activity_type": "Call",
            "hs_timestamp": "2026-11-22T10:00:00Z",
            "company_ids": ["123"]
        }
    ]
    assert normalized == normalize_activities(activities=activities, activity_type="Call")

def test_non_connected_call_normalized():
    activities = [
        {
            "properties": {
                "hs_call_disposition": "9d9162e7-6cf3-4944-bf63-4dff82258764",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": [
                        {"id": "123"}
                    ]
                }
            }
        }
    ]

    normalized = []
    assert normalized == normalize_activities(activities=activities, activity_type="Call")

def test_completed_meeting_normalized():
    activities = [
        {
            "properties": {
                "hs_meeting_outcome": "COMPLETED",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": [
                        {"id": "123"}
                    ]
                }
            }
        }
    ]

    normalized = [
        {
            'activity_type': 'Meeting',
            'hs_timestamp': '2026-11-22T10:00:00Z',
            'company_ids': ["123"]

        }
    ]
    assert normalized == normalize_activities(activities=activities, activity_type="Meeting")

def test_no_show_meeting_normalized():
    activities = [
        {
            "properties": {
                "hs_meeting_outcome": "NO_SHOW",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": [
                        {"id": "123"}
                    ]
                }
            }
        }
    ]

    normalized = []
    assert normalized == normalize_activities(activities=activities, activity_type="Meeting")

def test_incoming_email_normalized():
    activities = [
        {
            "properties": {
                "hs_email_direction": "INCOMING_EMAIL",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": [
                        {"id": "123"}
                    ]
                }
            }
        }
    ]

    normalized = [
        {
            'activity_type': 'Email',
            'hs_timestamp': '2026-11-22T10:00:00Z',
            'company_ids': ["123"]

        }
    ]
    assert normalized == normalize_activities(activities=activities, activity_type="Email")

def test_outgoing_email_normalized():
    activities = [
        {
            "properties": {
                "hs_email_direction": "EMAIL",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": [
                        {"id": "123"}
                    ]
                }
            }
        }
    ]

    normalized = []
    assert normalized == normalize_activities(activities=activities, activity_type="Email")

def test_no_company_associations_normalized():
    activities = [
        {
            "properties": {
                "hs_email_direction": "EMAIL",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": []
                }
            }
        }
    ]

    normalized = []
    assert normalized == normalize_activities(activities=activities, activity_type="Email")

def test_multiple_company_associations_normalized():
    activities = [
        {
            "properties": {
                "hs_email_direction": "INCOMING_EMAIL",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            "associations": {
                "companies": {
                    "results": [
                        {"id": "123"},
                        {"id": "456"}
                    ]
                }
            }
        }
    ]

    normalized = [
        {
            'activity_type': 'Email',
            'hs_timestamp': '2026-11-22T10:00:00Z',
            'company_ids': ["123", "456"]
   }
    ]
    assert normalized == normalize_activities(activities=activities, activity_type="Email")

def test_group_actvities_singular_company_assocation():
    activities = [
        {
            "activity_type": "Call",
            "hs_timestamp": "2026-11-22T10:00:00Z",
            "company_ids": ["123"]
        },
        {
            "activity_type": "Email",
            "hs_timestamp": "2026-11-21T10:00:00Z",
            "company_ids": ["123"]
        },
        {
            "activity_type": "Meeting",
            "hs_timestamp": "2026-11-20T10:00:00Z",
            "company_ids": ["456"]
        }
    ]
    grouped_activities = group_activities_by_company(activities=activities)
    exp_grouped_activites = {
        "123" : [
            {
                "activity_type": "Call",
                "hs_timestamp": "2026-11-22T10:00:00Z",
            },
            {
                "activity_type": "Email",
                "hs_timestamp": "2026-11-21T10:00:00Z",
            }
        ],
        "456" : [
            {
                "activity_type": "Meeting",
                "hs_timestamp": "2026-11-20T10:00:00Z",
            }
        ]
    }
    assert grouped_activities == exp_grouped_activites

def test_group_activities_multiple_compansy_association():
        activities = [
        {
            "activity_type": "Call",
            "hs_timestamp": "2026-11-22T10:00:00Z",
            "company_ids": ["123", "456"]
        },
        {
            "activity_type": "Email",
            "hs_timestamp": "2026-11-21T10:00:00Z",
            "company_ids": ["123", "456"]
        },
        {
            "activity_type": "Meeting",
            "hs_timestamp": "2026-11-20T10:00:00Z",
            "company_ids": ["456"]
        }
    ]
        grouped_activities = group_activities_by_company(activities)
        exp_grouped_activities = {
            "123" : [
                {
                    "activity_type": "Call",
                    "hs_timestamp": "2026-11-22T10:00:00Z",
                },
                {
                    "activity_type": "Email",
                    "hs_timestamp": "2026-11-21T10:00:00Z",
                }
            ],
            "456" : [
                {
                    "activity_type": "Call",
                    "hs_timestamp": "2026-11-22T10:00:00Z",
                },
                {
                    "activity_type": "Email",
                    "hs_timestamp": "2026-11-21T10:00:00Z",
                },
                {
                    "activity_type": "Meeting",
                    "hs_timestamp": "2026-11-20T10:00:00Z",
                }
            ]
        }
        assert grouped_activities == exp_grouped_activities

def test_score_companies_singular_association():
    company_activities = {
        "123": [
            {
                "activity_type": "Call",
                "hs_timestamp": "2026-11-22T10:00:00Z"
            },
            {
                "activity_type": "Email",
                "hs_timestamp": "2026-11-21T10:00:00Z"
            }
        ],
        "456": [
            {
                "activity_type": "Meeting",
                "hs_timestamp": "2026-11-20T10:00:00Z"
            }
        ]
    }
    now = datetime.fromisoformat("2026-11-23T10:00:00+00:00")
    actual_score = score_companies(company_activities=company_activities, now=now)
    exp_score = {
        "123": 11,
        "456": 20,
    }
    assert actual_score == exp_score


def test_score_companies_singular_association_multiple_occurrences():
    company_activities = {
        "123": [
            {
                "activity_type": "Call",
                "hs_timestamp": "2026-11-22T10:00:00Z"
            },
            {
                "activity_type": "Email",
                "hs_timestamp": "2026-11-21T10:00:00Z"
            },
            {
                "activity_type": "Call",
                "hs_timestamp": "2026-11-21T10:00:00Z"
            }
        ],
        "456": [
            {
                "activity_type": "Meeting",
                "hs_timestamp": "2026-11-20T10:00:00Z"
            }
        ]
    }
    now = datetime.fromisoformat("2026-11-23T10:00:00+00:00")
    actual_score = score_companies(company_activities=company_activities, now=now)
    exp_score = {
        "123": 19,
        "456": 20,
    }
    assert actual_score == exp_score

def test_score_companies_multiple_associations():
    company_activities = {
        "123": [
            {
                "activity_type": "Call",
                "hs_timestamp": "2026-11-22T10:00:00Z"
            },
            {
                "activity_type": "Email",
                "hs_timestamp": "2026-11-21T10:00:00Z"
            },
        ],
        "456": [
            {
                "activity_type": "Meeting",
                "hs_timestamp": "2026-11-20T10:00:00Z"
            },
            {
                "activity_type": "Email",
                "hs_timestamp": "2026-11-21T10:00:00Z"
            },
            {
                "activity_type": "Call",
                "hs_timestamp": "2026-11-21T10:00:00Z"
            }
        ]
    }
    now = datetime.fromisoformat("2026-11-23T10:00:00+00:00")
    actual_score = score_companies(company_activities=company_activities, now=now)
    exp_score = {
        "123": 11,
        "456": 31,
    }
    assert actual_score == exp_score
    