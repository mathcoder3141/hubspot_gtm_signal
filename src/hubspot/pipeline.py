def write_company_scores(client, company_scores, dry_run=True):
    for company_id, score in company_scores.items():
        if dry_run:
            print(f"[DRY RUN] Would update company {company_id} with score {score}")
        else:
            client.update_company(
                company_id=company_id,
                properties={"gtm_engagement_score": score}
            )
            print(f"Updated company {company_id} with score {score}")

