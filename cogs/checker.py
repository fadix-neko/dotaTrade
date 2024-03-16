import datetime
import random

import discord.ui
from discord.ext import commands, tasks
from cfg import *
from utils.models import current_items, safe_name, users
from utils.steamAPI import steambot


class Checker(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.guild = None
        self.timer = {}
        if not self.update_amount.is_running():
            self.update_amount.start()

    @tasks.loop(minutes=30)
    async def update_amount(self):
        inventory = steambot.parse_inventory()
        for x in inventory:
            doc = current_items.find_one_document({"name_id": safe_name(x['name'])})
            if bool(doc): current_items.find_one_and_update_document(doc, {"item_id": x['item_id'], "amount": len(x['item_id'])})

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.is_component():
            command = interaction.custom_id.split("@")
            if command[0] == 'shop':
                doc = current_items.find_one_document({"name_id": command[1]})
                if bool(doc):
                    if doc['amount'] >= 1:
                        user = users.find_one_document({"user_id": interaction.user.id})
                        if not bool(user):
                            user = {"user_id": interaction.user.id, "balance": 0}
                            users.insert_document(user)

                        if user['balance'] >= doc['price']:
                            modal = discord.ui.Modal(title="Вывод предмета в инвентарь Steam")
                            input_trade = discord.ui.InputText(label="Ссылка на трейд")

                            async def modal_callback(modal_interaction):
                                trade_link = modal_interaction.data["components"][0]["components"][0]["value"]
                                picked_item = random.choice(doc['item_id'])
                                trade = steambot.create_trade(trade_link, picked_item)

                                if trade.get("strError", None) is None:
                                    doc['item_id'].remove(picked_item)
                                    doc['amount']-=1
                                    current_items.find_one_and_update_document({"name_id": command[1]}, doc)
                                    users.find_one_and_update_document({"user_id": interaction.user.id},
                                                                       {"balance": user['balance']-doc['price']})
                                    await modal_interaction.response.send_message("Трейд был успешно отправлен по вашей ссылке!",
                                                                                  ephemeral=True)
                                else:
                                    await modal_interaction.response.send_message("Бот не смог отправить вам трейд. "
                                                                                  "Убедитесь, что ссылка указана верно, "
                                                                                  "а так же ваш инвентарь открыт для просмотра",
                                                                                  ephemeral=True)

                            modal.callback = modal_callback
                            modal.add_item(input_trade)
                            await interaction.response.send_modal(modal)
                        else:
                            await interaction.response.send_message("У вас недостаточно скрапа!", ephemeral=True)
                    else:
                        await interaction.response.send_message("Извините, данный предмет закончился :C", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        try:
            time_now = datetime.datetime.today()
            if before.channel == None or before.channel == member.guild.afk_channel:
                self.timer[member.id] = time_now
            elif after.channel == None or after.channel == member.guild.afk_channel:
                time_left = time_now - self.timer.get(member.id)
                seconds = int(time_left.total_seconds())
                balance = float(f"{seconds / (60 / COINS_PER_MINUTE):.2f}")

                user = users.find_one_document({"user_id": member.id})
                if bool(user): users.find_one_and_update_document(user, {"balance": user['balance']+balance})
                else: users.insert_document({"user_id": member.id, "balance": balance})
        except TypeError:
            # Бот был перезапущен, пока пользователь находился в голосовом канале
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        user = users.find_one_document({"user_id": member.id})
        if bool(user): pass
        else: users.insert_document({"user_id": member.id, "balance": 0})

    @commands.Cog.listener()
    async def on_message(self, message):
        member = message.author
        user = users.find_one_document({"user_id": member.id})
        if bool(user): users.find_one_and_update_document(user, {"balance": user['balance']+COINS_PER_MESSAGE})
        else: users.insert_document({"user_id": member.id, "balance": COINS_PER_MESSAGE})

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = users.find_one_document({"user_id": payload.user_id})
        if bool(user): users.find_one_and_update_document(user, {"balance": user['balance']+COINS_PER_REACTION})
        else: users.insert_document({"user_id": payload.user_id, "balance": COINS_PER_REACTION})

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user = users.find_one_document({"user_id": payload.user_id})
        if bool(user): users.find_one_and_update_document(user, {"balance": user['balance']-COINS_PER_REACTION})
        else: users.insert_document({"user_id": payload.user_id, "balance": 0})

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"cog > {self.__class__.__name__} < is loaded")
        self.guild = self.client.get_guild(GUILD_ID)


def setup(client):
    client.add_cog(Checker(client))
