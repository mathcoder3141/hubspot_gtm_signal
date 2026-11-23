from pprint import pprint
from datetime import datetime, timezone

def sort_activities(activities):
    activities = sorted(
        activities,
        key=lambda activity: activity["hs_timestamp"],
        reverse=True
    )
    return activities

def assign_occurrence_numbers(activities):
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

def prepare_activities(activities):
    activities = sort_activities(activities)
    activities = assign_occurrence_numbers(activities)
    return activities

def get_age_in_days(timestamp, now=None):
    utc_dt = timestamp.replace('Z', "+00:00")
    utc_dt = datetime.fromisoformat(utc_dt)
    if now is None:
        now = datetime.now(timezone.utc)
    else:
        now = now

    difference_days = (now - utc_dt).days
    return difference_days

def get_recency_multiplier(age_in_days):
    """
    Returns a multiplier / weight that looks on how long
    it's been since the engagement happened
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

def get_activity_weight(activity_type, occurrence_number):
    """
    Return the points for an activity based on its type
    and occurrence number.
    """
    if activity_type not in ('Meeting', 'Call', 'Email') or occurrence_number <= 0:
        return 0
    elif activity_type == 'Meeting' and occurrence_number == 1:
        weight = 20
    elif activity_type == 'Meeting' and occurrence_number == 2:
        weight = 15
    elif activity_type == 'Meeting' and occurrence_number == 3:
        weight = 10
    elif activity_type == 'Meeting' and occurrence_number == 4:
        weight = 5
    elif activity_type == 'Meeting' and occurrence_number >= 5:
        weight = 2
    elif activity_type == 'Call' and occurrence_number == 1:
        weight = 10
    elif activity_type == 'Call' and occurrence_number == 2:
        weight = 8
    elif activity_type == 'Call' and occurrence_number == 3:
        weight = 6
    elif activity_type == 'Call' and occurrence_number == 4:
        weight = 4
    elif activity_type == 'Call' and occurrence_number >= 5:
        weight = 2
    elif activity_type == 'Email':
        weight = 1
    return weight

def calculate_activity_points(activity_type, occurrence_number, age_in_days):
    """
    Calculate the adjusted points for a single activity.
    """
    adj_points = get_activity_weight(activity_type, occurrence_number) * get_recency_multiplier(age_in_days)
    return adj_points

def score_activities(activities, now=None):
    prepared_activites = prepare_activities(activities)
    score = 0
    for activity in prepared_activites:
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

def normalize_activities(activities, activity_type):
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

def group_activities_by_company(activities):
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

def score_companies(company_activities, now=None):
    company_scores = {}
    for company, activity in company_activities.items():
        score = score_activities(activity, now=now)
        company_scores[company] = score
    return company_scores
