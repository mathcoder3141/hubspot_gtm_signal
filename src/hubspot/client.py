import time
import os

import requests
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Optional

load_dotenv()

class HubSpotClient:
    BASE_URL = "https://api.hubapi.com/crm/objects/2026-09"

    def __init__(self) -> None:
        token = os.getenv("HUBSPOT_SERVICE_API_KEY")

        if not token:
            raise ValueError(
                "HUBSPOT_SERVICE_API_KEY is not set."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-type": "application/json",
            }
        )

    def request(self,
                method: str,
                endpoint: str,
                timeout: int = 30, 
                **kwargs
    ) -> dict:
        """
        Send an HTTP request to the HubSpot API.

        Retries requests that receive rate-limit or transient server
        errors using the configured retry delay.

        Returns the decoded JSON response.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        for i in range(0,3):
            response = self.session.request(
                method,
                url,
                timeout=timeout,
                **kwargs
            )   
            
            if response.ok:
                break
            
            if response.status_code not in (429, 500, 502, 503, 504):
                response.raise_for_status()
            
            if i < 2:
                time.sleep(self.get_retry_delay(response, i))

        response.raise_for_status() 
        return response.json()

    def get_retry_delay(
        self,
        response: requests.Response,
        attempt: int
    ) -> float:
        """
        Calculate the number of seconds to wait before retrying a request.

        Uses the Retry-After header for rate-limit responses when available.
        Falls back to exponential backoff when no usable retry delay is provided.
        """
        fallback_delay = 2 ** attempt
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                return int(retry_after)
            elif retry_after:
                try:
                    utc_dt = parsedate_to_datetime(retry_after)
                    now_dt = datetime.now(timezone.utc)
                    return max(0, (utc_dt - now_dt).total_seconds())
                except ValueError:
                    return fallback_delay
            else:
                return fallback_delay
        else:
            return fallback_delay

    def get_company(
            self,
            company_id: str,
            properties: Optional[list] = None
    ):
        """
        Retrieve all companies from HubSpot using pagination.

        `limit` controls the number of companies requested per API page.
        """
        params = {}

        if properties:
            params["properties"] = ",".join(properties)

        return self.request(
            "GET",
            f"companies/{company_id}",
            params=params
        )

    def get_companies(self, limit: int = 2) -> list[dict]:
        """
        Retrieve all companies from HubSpot using pagination.

        `limit` controls the number of companies requested per API page.
        """
        companies = []
        after = None
        has_more = True
        
        params = {
            "limit": limit,
            "properties": "name,domain,industry,numberofemployees"
        }

        while has_more:
            companies_pagination = self.request(
            "GET",
            "companies",
            params=params
        )
            companies.extend(companies_pagination['results'])
            next_page = companies_pagination.get("paging", {}).get("next")
            
            if next_page:
                after = next_page.get("after")
            else:
                after = None

            has_more = after is not None
            if has_more:
                params["after"] = after

        return companies

    def find_company_by_domain(self, domain: str) -> Optional[dict]:
        """
        Find a company in HubSpot by its domain.

        Returns the matching company, or None if no company is found.

        Raises ValueError if multiple companies match the domain.
        """
        filterGroups = [
            {
                "filters": [
                    {
                        "propertyName": "domain",
                        "operator": "EQ",
                        "value": domain
                    }
                ]
            }
        ]

        payload = {
            "filterGroups": filterGroups,
            "properties": ["name","domain","industry","numberofemployees"],
            "limit": 2
        }

        companies = self.request(
            "POST",
            "companies/search",
            json = payload
        )

        company_results = companies.get("results", [])

        if len(company_results) > 1:
            raise ValueError(
                f"Multiple companies found with domain '{domain}'. "
                "Cannot accurately determine where to write engagement score."
            )
        elif len(company_results) == 0:
            return None
        else:
            return company_results[0]

    def update_company(
        self,
        company_id: str,
        properties: dict
    ) -> dict:
        """
        Update properties on a HubSpot company.

        Returns the API response for the updated company.
        """
        payload = {
            "properties": properties
        }

        return self.request(
            "PATCH",
            f"companies/{company_id}",
            json=payload
        )

    def get_engagements(
        self,
        endpoint: str,
        limit: int = 100,
        properties: Optional[list] = None,
        associations: Optional[list] = None
    ) -> list[dict]:
        """
        Retrieve all engagements from a HubSpot endpoint using pagination.

        Optionally accepts properties and associations to include
        in the API response.

        `limit` controls the number of engagements requested per page.
        """
        engagements = []
        after = None
        has_more = True
        
        params = {
            "limit": limit,
        }

        if properties:
            params["properties"] = ",".join(properties)

        if associations:
            params["associations"] = ",".join(associations)
        
        while has_more:
            engagement_pagination = self.request(
            "GET",
            endpoint,
            params=params
        )
            engagements.extend(engagement_pagination['results'])
            next_page = engagement_pagination.get("paging", {}).get("next")
            
            if next_page:
                after = next_page.get("after")
            else:
                after = None

            has_more = after is not None
            if has_more:
                params["after"] = after

        return engagements
