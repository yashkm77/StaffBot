import os
import discord
from discord import app_commands

from staff_scraper import get_staff


# ============================================================
# DISCORD TOKEN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable is not set."
    )


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()


# ============================================================
# BOT CLASS
# ============================================================

class StaffBot(discord.Client):

    def __init__(self):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)


    async def setup_hook(self):

        await self.tree.sync()

        print("Slash commands synced.")


# ============================================================
# CREATE BOT
# ============================================================

client = StaffBot()


# ============================================================
# BOT READY
# ============================================================

@client.event
async def on_ready():

    print(f"Logged in as {client.user}")


# ============================================================
# /STAFF COMMAND
# ============================================================

@client.tree.command(
    name="staff",
    description="Look up anime episode staff"
)
@app_commands.describe(
    anime="Anime name, e.g. Jujutsu Kaisen S2",
    episode="Episode number, e.g. 4"
)
async def staff(
    interaction: discord.Interaction,
    anime: str,
    episode: int
):

    # --------------------------------------------------------
    # Show Discord loading state
    # --------------------------------------------------------

    await interaction.response.defer()


    # --------------------------------------------------------
    # Validate episode
    # --------------------------------------------------------

    if episode <= 0:

        embed = discord.Embed(
            title="❌ Invalid Episode",
            description="Episode number must be greater than 0.",
            color=discord.Color.red()
        )

        await interaction.followup.send(embed=embed)

        return


    # --------------------------------------------------------
    # Get staff information
    # --------------------------------------------------------

    roles, error = await get_staff(
        anime,
        episode
    )


    # --------------------------------------------------------
    # Error
    # --------------------------------------------------------

    if error:

        embed = discord.Embed(
            title="❌ Staff Lookup Failed",
            description=error,
            color=discord.Color.red()
        )

        embed.set_footer(
            text="KeyFrame Staff List"
        )

        await interaction.followup.send(
            embed=embed
        )

        return


    # ========================================================
    # CREATE MAIN EMBED
    # ========================================================

    embed = discord.Embed(
        title=f"{anime} — Episode {episode}",
        description="**Episode staff credits**",
        color=discord.Color.blurple()
    )


    # ========================================================
    # STORYBOARD
    # ========================================================

    if roles.get("SB"):

        embed.add_field(
            name="SB",
            value=", ".join(roles["SB"]),
            inline=False
        )


    # ========================================================
    # EPISODE DIRECTOR
    # ========================================================

    if roles.get("ED"):

        embed.add_field(
            name="ED",
            value=", ".join(roles["ED"]),
            inline=False
        )


    # ========================================================
    # CHIEF ANIMATION DIRECTOR
    # ========================================================

    if roles.get("CAD"):

        embed.add_field(
            name="CAD",
            value=", ".join(roles["CAD"]),
            inline=False
        )


    # ========================================================
    # ANIMATION DIRECTOR
    # ========================================================

    if roles.get("AD"):

        embed.add_field(
            name="AD",
            value=", ".join(roles["AD"]),
            inline=False
        )


    # ========================================================
    # ASSISTANT ANIMATION DIRECTOR
    # ========================================================

    if roles.get("AAD"):

        embed.add_field(
            name="Ass. AD",
            value=", ".join(roles["AAD"]),
            inline=False
        )


    # ========================================================
    # KEY ANIMATION
    # ========================================================

    if roles.get("KA"):

        ka_text = ", ".join(
            roles["KA"]
        )

        # Discord embed field limit = 1024 characters
        if len(ka_text) > 1024:

            ka_text = (
                ka_text[:1020]
                + "..."
            )

        embed.add_field(
            name="KA",
            value=ka_text,
            inline=False
        )


    # ========================================================
    # 2ND KEY ANIMATION
    # ========================================================

    if roles.get("2KA") is not None:

        embed.add_field(
            name="2KA",
            value=str(
                roles["2KA"]
            ),
            inline=False
        )


    # ========================================================
    # FOOTER
    # ========================================================

    embed.set_footer(
        text="KeyFrame Staff List"
    )


    # ========================================================
    # SEND EMBED
    # ========================================================

    await interaction.followup.send(
        embed=embed
    )


# ============================================================
# RUN BOT
# ============================================================

client.run(TOKEN)