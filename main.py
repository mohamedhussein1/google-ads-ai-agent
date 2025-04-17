import os
import base64
import datetime
import gspread
from google.oauth2 import service_account
from google.ads.googleads.client import GoogleAdsClient
from huggingface_hub import InferenceClient

# === Load environment variables ===
google_ads_yaml = os.environ.get("GOOGLE_ADS_YAML")
decoded_yaml = base64.b64decode(google_ads_yaml).decode("utf-8")
with open("google-ads.yaml", "w") as f:
    f.write(decoded_yaml)

hf_token = os.environ.get("OPENAI_API_KEY")
inference = InferenceClient(token=hf_token)

# === Authenticate Google Sheets ===
sheet_url = "https://docs.google.com/spreadsheets/d/1brxg6YXWQrDG8gUNHqsgkizibb7blwsV-vwDCNEApL4"
service_account_info = {
    # NOTE: Replace this block with your actual service account JSON if needed
}
credentials = service_account.Credentials.from_service_account_info(service_account_info)
gc = gspread.authorize(credentials)

# === Connect to Google Ads ===
client = GoogleAdsClient.load_from_storage("google-ads.yaml")
customer_service = client.get_service("CustomerService")
accessible_customers = customer_service.list_accessible_customers()

today = datetime.datetime.now().strftime("%Y-%m-%d")

for customer in accessible_customers.resource_names:
    customer_id = customer.split("/")[-1]
    sheet = gc.open_by_url(sheet_url).worksheet(customer_id) if customer_id in [ws.title for ws in gc.open_by_url(sheet_url).worksheets()] else gc.open_by_url(sheet_url).add_worksheet(title=customer_id, rows="1000", cols="5")
    sheet.append_row(["Search Term", "Excluded", "Campaign Name", "Ad Group Name", "Date/Time"])

    ga_service = client.get_service("GoogleAdsService")
    query = '''
    SELECT campaign.name, ad_group.name, search_term_view.search_term
    FROM search_term_view
    WHERE segments.date DURING LAST_7_DAYS
    LIMIT 50
    '''

    response = ga_service.search(customer_id=customer_id, query=query)

    for row in response:
        search_term = row.search_term_view.search_term
        campaign_name = row.campaign.name
        ad_group_name = row.ad_group.name

        prompt = f"Is '{search_term}' relevant for a Google Ads campaign targeting '{campaign_name}' and '{ad_group_name}'? Reply 'Yes' or 'No'."
        result = inference.text_generation(prompt, max_new_tokens=5).lower()

        exclude = "Done" if "no" in result else "Not Done"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sheet.append_row([search_term, exclude, campaign_name, ad_group_name, timestamp])