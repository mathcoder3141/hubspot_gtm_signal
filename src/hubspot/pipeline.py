import logging
from src.hubspot.client import HubSpotClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def write_company_scores(
        client: HubSpotClient,
        company_scores: dict[str, float],
        dry_run=True
) -> None:
    for company_id, score in company_scores.items():
        if dry_run:
            logger.info(f"[DRY RUN] Would update company {company_id} with score {score}")
        else:
            try:
                client.update_company(
                    company_id=company_id,
                    properties={"gtm_engagement_score": score}
                )
                logger.info("Updated company %s with score %s", company_id, score)
            except Exception:
                logger.error(
                    "Failed to update company %s",
                    company_id,
                    exc_info=True
                )