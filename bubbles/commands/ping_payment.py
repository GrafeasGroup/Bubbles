import requests

from bubbles.config import PluginManager, PAYMENT_KEY, PAYMENT_VALUE


def ping_payment(payload):
    result = requests.post(
        "https://payments.grafeas.org/ping", json={PAYMENT_KEY: PAYMENT_VALUE}
    )
    try:
        result.raise_for_status()
    except:
        payload["extras"]["say"]("I... I don't see anything out there...")


PluginManager.register_plugin(
    ping_payment,
    r"ping payment",
    help="!ping payment - make sure that Gringotts is still accepting coin.",
)
