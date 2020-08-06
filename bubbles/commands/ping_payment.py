import requests

from bubbles.config import PluginManager, PAYMENT_KEY, PAYMENT_VALUE


def ping_payment(rtmclient, client, user_list, data):
    result = requests.post('https://payments.grafeas.org/ping', json={PAYMENT_KEY: PAYMENT_VALUE})
    try:
        result.raise_for_status()
    except:
        client.chat_postMessage(
            channel=data.get("channel"),
            text="I... I don't see anything out there...",
            as_user=True
        )


PluginManager.register_plugin(ping_payment, r"ping payment")
