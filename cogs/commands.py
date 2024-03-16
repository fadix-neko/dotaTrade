import discord

from utils.models import users
from discord.ext import commands
from discord import slash_command


class Commands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @staticmethod
    def check_user(ctx):
        user = users.find_one_document({"user_id": ctx.author.id})
        if not bool(user): users.insert_document({"user_id": ctx.author.id, "balance": 0})

        return users.find_one_document({"user_id": ctx.author.id})

    @slash_command(description="Посмотреть ваш баланс")
    async def balance(self, ctx):
        user = self.check_user(ctx)

        embed = discord.Embed(title=f"Баланс {ctx.author.display_name}", colour=int("FF724C", 16))
        embed.add_field(name="ㅤ", value=f'```{user["balance"]:.2f}```')
        try: embed.set_thumbnail(url=ctx.author.avatar.url)
        except: pass
        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"cog > {self.__class__.__name__} < is loaded")


def setup(client):
    client.add_cog(Commands(client))
