from datetime import datetime, timezone
from typing import Optional

def sort_activities(activities: list[dict]) -> list[dict]:
    """
    Sorts activities based on `hs_timestamp` from most recent to least recent.

    This ensures the assign occurence number function starts from the most recent activity type
    so that more recent events can be weighted properly.
    """
    activities = sorted(
        activities,
        key=lambda activity: activity["hs_timestamp"],
        reverse=True
    )
    return activities

def assign_occurrence_numbers(activities: list[dict]) -> list[dict]:
    """
    Assign occurrence numbers to activities based on activity type.
    """
    counts = {}
    for activity in activities:
        activity_type = activity["activity_type"]

        if activity_type not in counts:
            counts[activity_type] = 0
        counts[activity_type] += 1
        activity["occurrence_number"] = counts[activity_type]
    return activities

def prepare_activities(activities: list[dict]) -> list[dict]:
    """
    This function utilizes the `sort_activities()` and `assgin_(occurrence_numbers()`
    functions.
    """
    activities = sort_activities(activities)
    activities = assign_occurrence_numbers(activities)
    return activities

def get_age_in_days(
        hs_timestamp: str,
        now: Optional[datetime] = None
) -> int:
    """
    Return the number of days since an activity occurred.

    hs_timestamp should be an ISO 8601 timestamp, such as:
    2026-11-22T10:00:00Z.

    `now` can be provided to make the calculation deterministic
    during testing.
    """
    utc_dt = hs_timestamp.replace('Z', "+00:00")
    utc_dt = datetime.fromisoformat(utc_dt)
    if now is None:
        now = datetime.now(timezone.utc)
    else:
        now = now

    difference_days = (now - utc_dt).days
    return difference_days

def get_recency_multiplier(age_in_days: int) -> float:
    """
    Return the recency multiplier based on the age of an activity.
    """
    if age_in_days < 0 or age_in_days > 30:
        multiplier = 0
    elif age_in_days <= 7:
        multiplier = 1.0
    elif age_in_days <= 14:
        multiplier = 0.75
    elif age_in_days <= 21:
        multiplier = 0.5
    else:
        multiplier = 0.25
    return multiplier

def get_activity_weight(
        activity_type: str,
        occurrence_number: int
) -> int:
    """
    Return the base points for an activity based on its type
    and occurrence number.
    """

    weights = {
        "Meeting": [20, 15, 10, 5, 2],
        "Call": [10, 8, 6, 4, 2],
        "Email": [1]
    }
    
    if activity_type not in weights or occurrence_number <= 0: 
        return 0
    
    activity_weights = weights[activity_type]

    if occurrence_number > len(activity_weights):
        return activity_weights[-1]

    return activity_weights[occurrence_number - 1]

def calculate_activity_points(
        activity_type:str, 
        occurrence_number:int,
        age_in_days:int
) -> float:
    """
    Calculate the adjusted points for a single activity.
    """
    adj_points = get_activity_weight(activity_type, occurrence_number) * get_recency_multiplier(age_in_days)
    return adj_points

def score_activities(
        activities: list[dict],
        now: Optional[datetime] = None
) -> float:
    """
    Calculate the engagement score for a set of activities.

    The final score is capped at 100.
    """
    prepared_activities = prepare_activities(activities)
    score = 0
    for activity in prepared_activities:
        activity_type = activity["activity_type"]
        occurrence_number = activity["occurrence_number"]
        hs_timestamp = activity["hs_timestamp"]
        age = get_age_in_days(hs_timestamp, now=now)
        activity_points = calculate_activity_points(
            activity_type=activity_type,
            occurrence_number=occurrence_number,
            age_in_days=age
        )
        score += activity_points
    score = min(score, 100)
    return score

def normalize_activities(
        activities: list[dict],
        activity_type: str
) -> list[dict]:
    """
    Filter activities to qualifying events and return them
    in a consistent format.
    """
    normalized_activities = []
    if activity_type == 'Call':
        qualifying_property = 'hs_call_disposition'
        qualifying_value = 'f240bbac-87c9-4f6e-bf70-924b57d47db7'
    elif activity_type == 'Meeting':
        qualifying_property = 'hs_meeting_outcome'
        qualifying_value = 'COMPLETED'
    elif activity_type == 'Email':
        qualifying_property = 'hs_email_direction'
        qualifying_value = 'INCOMING_EMAIL'
    else:
        raise ValueError(f"{activity_type} is not a valid activity type.")
    
    for activity in activities:
        activity_outcome = activity['properties'][qualifying_property]
        hs_timestamp = activity['properties']['hs_timestamp']
        companies = activity['associations']['companies']['results']
        company_ids = [company["id"] for company in companies]
        
        if not companies or activity_outcome != qualifying_value:
            continue
        
        normalized_activity = {
            'activity_type': activity_type,
            'hs_timestamp': hs_timestamp,
            "company_ids": company_ids
        }

        normalized_activities.append(normalized_activity)
    return normalized_activities

def group_activities_by_company(
        activities: list[dict]
) -> dict[str, list[dict]]:
    """
    Groups activities by company ID.
    """
    company_level_activities = {}
    for activity in activities:
        activity_type = activity['activity_type']
        hs_timestamp = activity['hs_timestamp']
        company_ids = activity['company_ids']
        for company_id in company_ids:
            company_activity = {
                "activity_type": activity_type,
                "hs_timestamp": hs_timestamp
            }
            company_level_activities.setdefault(company_id, []).append(company_activity)
    return company_level_activities

def score_companies(
        company_activities: dict[str, list[dict]],
        now: Optional[datetime] = None
) -> dict[str, float]:
    """
    Calculates the engagement score for each company.
    """
    company_scores = {}
    for company, activities in company_activities.items():
        score = score_activities(activities, now=now)
        company_scores[company] = score
    return company_scores
