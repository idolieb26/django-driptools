# from channels.routing import route
# from driptools.consumers import ws_connect, ws_receive


# channel_routing = [
#     route('websocket.connect', ws_connect),
#     route("websocket.receive", ws_receive),
# ]

# project/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter
import gmail_app.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': URLRouter(
        gmail_app.routing.websocket_urlpatterns
        ),
})