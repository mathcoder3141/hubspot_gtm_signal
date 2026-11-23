from src.hubspot.client import HubSpotClient
from src.hubspot.scoring import (
    normalize_activities,
    group_activities_by_company,
    score_companies,
)
from src.hubspot.pipeline import write_company_scores
from itertools import chain
from pprint import pprint

def main():
    client = HubSpotClient()
    companies = client.get_companies(limit=100)
    calls = client.get_engagements(
        endpoint="calls",
        limit=100,
        properties=["hs_call_disposition", "hs_timestamp"],
        associations=["companies"]
    )
    meetings = client.get_engagements(
        endpoint="meetings",
        limit=100,
        properties=["hs_meeting_outcome", "hs_timestamp"],
        associations=["companies"]
    )
    emails = client.get_engagements(
        endpoint="emails",
        limit=100,
        properties=["hs_email_direction", "hs_timestamp"],
        associations=["companies"]
    )
    normalized_calls = normalize_activities(calls, "Call")
    normalized_meetings = normalize_activities(meetings, "Meeting")
    normalized_emails = normalize_activities(emails, "Email")
    normalized_activities = list(
        chain(
            normalized_calls,
            normalized_meetings,
            normalized_emails
        )
    )
    grouped_activities = group_activities_by_company(normalized_activities)
    company_scores = {
        company["id"]: 0
        for company in companies
    }

    company_scores.update(score_companies(grouped_activities))

    write_company_scores(client, company_scores, dry_run=True)

if __name__ == "__main__":
    main()