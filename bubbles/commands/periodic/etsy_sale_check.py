import os
import urllib.parse as urlparse
from datetime import datetime, timedelta
from urllib.parse import parse_qs

from etsy2.oauth import EtsyOAuthHelper

from bubbles.config import app, etsy, rooms_list

KEY = os.environ.get("etsy_key")
SECRET = os.environ.get("etsy_secret")
SHOP_ID = os.environ.get("etsy_shop_id")
OAUTH_TOKEN = os.environ.get("etsy_oauth_token")
OAUTH_TOKEN_SECRET = os.environ.get("etsy_oauth_token_secret")

permission_scopes = ["transactions_r"]

# Etsy has their own internal map of country codes that doesn't map to anything.
# Here are some of the ones that we know we have volunteers in so we can save
# an API call.
KNOWN_COUNTRY_CODES = {
    10: "Antarctica",
    79: "Canada",
    91: "Germany",
    93: "Denmark",
    97: "Egypt",
    99: "Spain",
    103: "France",
    105: "United Kingdom",
    112: "Greece",
    122: "India",
    123: "Ireland",
    128: "Italy",
    150: "Mexico",
    164: "The Netherlands",
    167: "New Zealand",
    172: "Philippines",
    181: "Russia",
    193: "Sweden",
    203: "Turkey",
    209: "United States",
    211: "Venezuela",
    219: "Hong Kong",
}


def get_oauth_keys() -> None:
    """A function that should be run from the command line to generate new keys."""
    (
        login_url,
        temp_oauth_token_secret,
    ) = EtsyOAuthHelper.get_request_url_and_token_secret(KEY, SECRET, permission_scopes)

    query = urlparse.urlparse(login_url).query
    temp_oauth_token = parse_qs(query)["oauth_token"][0]
    print("URL for verification: ", login_url)
    verifier = input("Please visit the URL above and paste the verification key here: ")

    oauth_token, oauth_token_secret = EtsyOAuthHelper.get_oauth_token_via_verifier(
        KEY, SECRET, temp_oauth_token, temp_oauth_token_secret, verifier
    )

    print(f"OAuth token: {oauth_token}")
    print(f"OAuth token secret: {oauth_token_secret}")


def etsy_recent_sale_callback() -> None:
    receipts = etsy.findAllShopReceipts(
        shop_id=SHOP_ID,
        min_created=int((datetime.now() - timedelta(seconds=15)).timestamp()),
    )

    for receipt in receipts:
        try:
            country_name = KNOWN_COUNTRY_CODES.get(int(receipt.get("currency_code")))
            if not country_name:
                country_name = etsy.getCountry(country_id=receipt.get("currency_code"))[0].get(
                    "name"
                )
            msg = (
                f":moneybag: Just sold a whopping {receipt.get('grandtotal')}"
                f" {receipt.get('currency_code')} to somebody in {country_name}!"
            )
            if buyer_msg := receipt.get("message_from_buyer"):
                msg += f" They included a message for us:\n\n```\n{buyer_msg}\n```"
        except Exception as e:
            msg = f"Somebody just bought something, but there was an error on my" \
                  f" side:\n\n```\n{e}\n```"
        app.client.chat_postMessage(text=msg, channel=rooms_list["merch"], as_user=True)
