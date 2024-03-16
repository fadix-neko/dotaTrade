from steampy_fix.client import SteamClient, Asset
from steampy_fix.models import GameOptions
from cfg import STEAM_API_KEY, STEAM_USERNAME, STEAM_PASSWORD, STEAM_GUARD_NAME


class SteamBot:
    def __init__(self):
        self.client = SteamClient(api_key=STEAM_API_KEY)
        self.client.login(username=STEAM_USERNAME, password=STEAM_PASSWORD, steam_guard=fr"database/{STEAM_GUARD_NAME}")
        self.game_ = GameOptions.DOTA2
        self.client.steam_guard['steamid'] = self.client.steam_guard['Session']['SteamID']

    def create_trade(self, offer_url: str, item_id: str):
        asset = Asset(item_id, self.game_)
        return self.client.make_offer_with_url([asset], [], offer_url, '', True)

    def parse_inventory(self):
        my_items = self.client.get_my_inventory(self.game_)
        items = [
            {
                "name": x[1]['name'],
                "item_id": x[0],
                "icon": f'https://community.cloudflare.steamstatic.com/economy/image/{x[1]["icon_url_large"]}/330x192?allow_animated=1'
            }
            for x in my_items.items() if bool(x[1]['tradable'])
        ]

        for item in items:
            item['item_id'] = [x['item_id'] for x in items if x['name'] == item['name'] and not isinstance(x['item_id'], list)]

        names = []
        for item in items[:]:
            if item['name'] in names: items.remove(item)
            names.append(item['name'])

        return items


steambot = SteamBot()

