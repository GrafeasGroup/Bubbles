import os
import urllib.parse as urlparse
from datetime import datetime, timedelta
from urllib.parse import parse_qs

from etsy2.oauth import EtsyOAuthHelper

from bubbles.config import app, etsy, rooms_list

KEY = os.environ.get('etsy_key')
SECRET = os.environ.get('etsy_secret')
SHOP_ID = os.environ.get('etsy_shop_id')
OAUTH_TOKEN = os.environ.get('etsy_oauth_token')
OAUTH_TOKEN_SECRET = os.environ.get('etsy_oauth_token_secret')

permission_scopes = ['transactions_r']


def get_oauth_keys() -> None:
    """A function that should be run from the command line to generate new keys."""
    login_url, temp_oauth_token_secret = EtsyOAuthHelper.get_request_url_and_token_secret(
        KEY, SECRET, permission_scopes
    )

    query = urlparse.urlparse(login_url).query
    temp_oauth_token = parse_qs(query)['oauth_token'][0]
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
        min_last_modified=int((datetime.now() - timedelta(seconds=16)).timestamp())
    )

    for receipt in receipts:
        msg = (
            f":moneybag: Just sold a whopping {receipt.get('grandtotal')}"
            f" {receipt.get('currency_code')} to somebody in {receipt.get('city')}!"
        )
        if buyer_msg := receipt.get('message_from_buyer'):
            msg += f" They included a message for us:\n\n```\n{buyer_msg}\n```"
        app.client.chat_postMessage(
            text=msg,
            channel=rooms_list["merch"],
            as_user=True
        )
