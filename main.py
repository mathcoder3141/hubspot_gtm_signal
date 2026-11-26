import logging
from itertools import chain

from src.hubspot.client import HubSpotClient
from src.hubspot.scoring import (
    normalize_activities,
    group_activities_by_company,
    score_companies,
)
from src.hubspot.pipeline import write_company_scores

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting HubSpot engagement scoring pipeline.")

    client = HubSpotClient()

    logger.info("Fetching companies")
    companies = client.get_companies(limit=100)
    logger.info("Fetched %d companies", len(companies))
    
    logger.info("Fetching calls")
    calls = client.get_engagements(
        endpoint="calls",
        limit=100,
        properties=["hs_call_disposition", "hs_timestamp"],
        associations=["companies"]
    )
    logger.info("Fetched %d calls", len(calls))

    logger.info("Fetching meetings")
    meetings = client.get_engagements(
        endpoint="meetings",
        limit=100,
        properties=["hs_meeting_outcome", "hs_timestamp"],
        associations=["companies"]
    )
    logger.info("Fetched %d meetings", len(meetings))

    logger.info("Fetching emails")
    emails = client.get_engagements(
        endpoint="emails",
        limit=100,
        properties=["hs_email_direction", "hs_timestamp"],
        associations=["companies"]
    )
    logger.info("Fetched %d emails", len(emails))

    normalized_calls = normalize_activities(calls, "Call")
    normalized_meetings = normalize_activities(meetings, "Meeting")
    normalized_emails = normalize_activities(emails, "Email")

    logger.info(
        "Normalized activities: %d calls, %d meetings, %d emails.", len(normalized_calls), len(normalized_meetings), len(normalized_emails)
    )

    normalized_activities = list(
        chain(
            normalized_calls,
            normalized_meetings,
            normalized_emails
        )
    )
    grouped_activities = group_activities_by_company(normalized_activities)
    logger.info(
        "Grouped activities across %d companies.", len(grouped_activities)
    )

    company_scores = {
        company["id"]: 0
        for company in companies
    }

    company_scores.update(score_companies(grouped_activities))

    logger.info(
        "Calculated scores for %d companies.", len(company_scores)
    )
    write_company_scores(client, company_scores, dry_run=True)
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()