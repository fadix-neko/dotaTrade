import re

import discord
from discord.ui import View
from faginator import Faginator

from utils.models import check_admin, generate_inventory, current_items
from utils.steamAPI import steambot
from cfg import *

from discord.ext import commands
from discord import Option, SlashCommandGroup


class ItemsPanel(commands.Cog):

    def __init__(self, client):
        self.client = client

    panel = SlashCommandGroup(name="panel", checks=[check_admin])
    items = panel.create_subgroup("items")
    guide = panel.create_subgroup("guide")

    @items.command(description="Открыть панель управления скинами в магазине")
    async def manage(self, ctx):
        embeds, buttons = generate_inventory(ctx.author, steambot.parse_inventory())
        if buttons == []: shop_buttons = None
        menu = Faginator(ctx, embeds=embeds, extra_buttons=buttons, timeout=None, lang='ru')
        await menu.start(type="slash")

    @items.command(description="Удалить товар из магазина")
    async def delete(self, ctx, message_link: Option(str, "Ссылка на сообщение")):
        message_id = int(re.findall("(\d{18,19})/(\d{18,19})/(\d{18,19})", message_link)[0][2])
        if bool(current_items.find_one_document({"message_id": message_id})):
            shop_channel = ctx.guild.get_channel(SHOP_CHANNEL)
            message = await shop_channel.fetch_message(message_id)
            current_items.delete_document({"message_id": message_id})
            await message.delete()
            await ctx.respond("Товар удалён с продажи!", ephemeral=True)
        else:
            await ctx.respond("Сообщение не привязано к магазину!", ephemeral=True)


    @guide.command(description="Опубликовать сообщение с гайдом на получение валюты")
    async def balance(self, ctx):
        embed = discord.Embed(title="Discord валюта", description=f"Внутри нашего Discord сервера Вы можете "
                                                                  f"заработать валюту, за которую в <#{SHOP_CHANNEL}> "
                                                                  f"можно выводить реальные скины в свой инвентарь стим\n\n"
                                                                  f"> 1 минута в войсе = {COINS_PER_MINUTE} {COIN_EMOJI}\n"
                                                                  f"> 1 сообщение = {COINS_PER_MESSAGE} {COIN_EMOJI}\n"
                                                                  f"> 1 реакция = {COINS_PER_REACTION} {COIN_EMOJI}\n"
                                                                  f"`/balance` - Команда проверки баланса.\n\n"
                                                                  f"Не воспринимайте данную систему, как вид заработка, \n"
                                                                  f"так как она рассчитана лишь на то, "
                                                                  f"чтобы вы могли получать приятный бонус, используя наш Discord",
                              colour=int("FF724C", 16))
        view = View()
        view.add_item(discord.ui.Button(label="Магазин", emoji="🛒", style=discord.ButtonStyle.url,
                                        url=f"https://discord.com/channels/{GUILD_ID}/{SHOP_CHANNEL}"))
        await ctx.channel.send(embed=embed, view=view)
        await ctx.respond("Успешная публикация!", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"cog > {self.__class__.__name__} < is loaded")


def setup(client):
    client.add_cog(ItemsPanel(client))
