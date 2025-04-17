import os
from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime
import openai

# Set up OpenAI (via ChatGPT or Hugging Face)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Authenticate with Google Ads
googleads_client = GoogleAdsClient.load_from_storage("google-ads.yaml")

def analyze_and_exclude_search_terms():
    ga_service = googleads_client.get_service("GoogleAdsService")

    query = """
        SELECT
          campaign.id,
          ad_group.id,
          search_term_view.search_term,
          search_term_view.impressions
        FROM search_term_view
        WHERE segments.date DURING LAST_7_DAYS
    """

    response = ga_service.search_stream(customer_id="INSERT_CUSTOMER_ID", query=query)

    for batch in response:
        for row in batch.results:
            term = row.search_term_view.search_term
            prompt = f"Is this search term '{term}' relevant to my Google Ads for restaurant reservations?"
            answer = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            result = answer.choices[0].message.content.lower()
            if "not relevant" in result or "exclude" in result:
                print(f"Exclude keyword: {term}")

if __name__ == "__main__":
    print(f"[{datetime.now()}] Running AI Agent...")
    analyze_and_exclude_search_terms()
