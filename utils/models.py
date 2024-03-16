import string
from urllib.parse import quote

import discord
from discord import Interaction
from discord.ui import View
from fsonbase import fsonbase, fcluster
from cfg import SHOP_CHANNEL, COIN_EMOJI, GUILD_ID, GUIDE_FARM_CHANNEL
from faginator import Faginator
from utils.steamAPI import steambot

database = fsonbase("database")
current_items = database.connect("current_items")
users = database.connect("users")
safe_symbols = list(string.ascii_letters) + list(string.digits) + [' ']

def safe_name(name):
    return ''.join([x for x in name if x in safe_symbols]).replace(" ", '_')

def check_admin(ctx):
    if isinstance(ctx, discord.Interaction):
        return ctx.user.guild_permissions.administrator
    return ctx.author.guild_permissions.administrator

def generate_inventory(user, items):
    custom_description = ''
    shop_buttons = []
    shop_buttons_ext = []
    embeds = []
    for i, v in enumerate(items):
        custom_description += f"`{i + 1}.` {v['name']}\n Количество: {len(v['item_id'])}\n\n"
        shop_buttons_ext.append(SteamItemButton(user=user, fbase=current_items, label=(i + 1),
                                                custom_id=safe_name(v['name']), style=discord.ButtonStyle.primary))

        if (i + 1) % 5 == 0 and (i + 1) >= 1:
            emb = discord.Embed(title='Управление инвентарём стима', description=custom_description,
                                colour=discord.Colour.embed_background())
            embeds.append(emb)
            shop_buttons.append(shop_buttons_ext)
            shop_buttons_ext = []
            custom_description = f''

    if custom_description != f'':
        emb = discord.Embed(title="Управление инвентарём стима", description=custom_description,
                            colour=discord.Colour.embed_background())
        embeds.append(emb)
        shop_buttons.append(shop_buttons_ext)

    if embeds == []:
        embeds.append(
            discord.Embed(title='Управление инвентарём стима', description='*Инвентарь в стиме пуст*',
                          colour=discord.Colour.embed_background()))

    return [embeds, shop_buttons]


class SteamItemButton(discord.ui.Button):
    def __init__(self, user: discord.Member, fbase: fcluster, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.db = fbase
        self.channel = user.guild.get_channel(SHOP_CHANNEL)

    async def callback(self, interaction: Interaction):
        if interaction.user != self.user: return

        doc = self.db.find_one_document({"name_id": interaction.custom_id})
        if bool(doc):
            view = View()
            btns = [
                discord.ui.Button(label="Утвердить", custom_id="accept", style=discord.ButtonStyle.green),
                discord.ui.Button(label="Отмена", custom_id="decline", style=discord.ButtonStyle.red)
            ]

            async def button_callback(confirm_interaction: Interaction):
                if confirm_interaction.user == interaction.user:
                    if confirm_interaction.custom_id == "accept":
                        linked_message = await self.channel.fetch_message(doc['message_id'])
                        await linked_message.delete()
                        self.db.delete_document(doc)

                        embeds, buttons = generate_inventory(self.user, steambot.parse_inventory())
                        if buttons == []: shop_buttons = None
                        menu = Faginator(interaction, embeds=embeds, extra_buttons=buttons, timeout=None, lang='ru')
                        await menu.start(interact=confirm_interaction, type='interaction', action="edit")
                        await confirm_interaction.followup.send(f"Предмет {doc['name']} был удален из магазина",
                                                                ephemeral=True)
                    else:
                        embeds, buttons = generate_inventory(self.user, steambot.parse_inventory())
                        if buttons == []: shop_buttons = None
                        menu = Faginator(interaction, embeds=embeds, extra_buttons=buttons, timeout=None, lang='ru')
                        await menu.start(interact=confirm_interaction, type='interaction', action="edit",
                                         ephemeral=True)
                        await confirm_interaction.followup.send(f"Отмена")

            for btn in btns:
                btn.callback = button_callback
                view.add_item(btn)

            await interaction.response.edit_message(embed=discord.Embed(description="Вы уверены, что хотите удалить этот предмет из магазина?",
                                                                        colour=discord.Colour.embed_background()), view=view)
        else:
            modal = discord.ui.Modal(title="Добавление предмета", timeout=720)

            async def modal_callback(modal_interaction: Interaction):
                name_ru = modal_interaction.data["components"][0]["components"][0]["value"]
                price = int(modal_interaction.data["components"][1]["components"][0]["value"])
                item = [x for x in steambot.parse_inventory() if safe_name(x['name']) == interaction.custom_id][0]

                embed = discord.Embed(title=f"{name_ru}",
                                      description=f"После приобретения вы получите данный "
                                                  f"скин в свой инвентарь steam.\n"
                                                  f"`Цена`: **{price}** {COIN_EMOJI}\n\n"
                                                  f"[Торговая площадка стим](https://steamcommunity.com/market/listings/570/{quote(item['name'])})",
                                      colour=discord.Colour.embed_background()
                                      )
                embed.set_thumbnail(url=item['icon'])

                shop_view = View()
                shop_view.add_item(discord.ui.Button(label="Вывести", style=discord.ButtonStyle.green,
                                                     custom_id=f"shop@{safe_name(item['name'])}"))
                shop_view.add_item(discord.ui.Button(label="Как фармить?", style=discord.ButtonStyle.link,
                                                     url=f"https://discord.com/channels/{GUILD_ID}/{GUIDE_FARM_CHANNEL}"))
                new_message = await self.channel.send(embed=embed, view=shop_view)

                self.db.insert_document({"name": item['name'], "item_id": item['item_id'], 'icon': item['icon'],
                                         "name_id": safe_name(item['name']), "name_ru": name_ru, "price": price,
                                         "amount": len(item['item_id']), "message_id": new_message.id})

                await modal_interaction.response.send_message("Предмет был успешно добавлен в магазин", ephemeral=True)

            name_input = discord.ui.InputText(label="Название предмета")
            price_input = discord.ui.InputText(label="Стоимость (скрап)")

            modal.callback = modal_callback

            modal.add_item(name_input)
            modal.add_item(price_input)

            await interaction.response.send_modal(modal)
