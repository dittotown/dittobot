import random

import discord
import os


from dotenv import load_dotenv
from discord import app_commands


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('GUILD_ID'))

V_SPOT = int(os.getenv('V_SPOT'))
VN_CHANNEL = int(os.getenv('VN_CHANNEL'))
THE_ROAD = int(os.getenv('THE_ROAD'))
PATO = int(os.getenv('PATO'))
DITTO_ID = int(os.getenv('DITTO_ID'))
OCTO_ID = int(os.getenv('OCTO_ID'))
GOOD_ROLE = int(os.getenv('GOOD_ROLE'))
BAD_ROLE = int(os.getenv('BAD_ROLE'))
LAW_DISOBEYER_ROLE = int(os.getenv('LAW_DISOBEYER_ROLE'))


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


@client.event
async def setup_hook():
    print("setup hook running")
    print("command trees sync'ed")

    await tree.sync()

    global ditto, octo
    ditto = await client.fetch_user(DITTO_ID)
    octo = await client.fetch_user(OCTO_ID)


    await ditto.send(f"dittobot set up!")
    v_spot = await client.fetch_channel(V_SPOT)
    # await v_spot.send(f"From {ditto.mention} — [lots of tags here][more tags]")


@client.event
async def on_message(message):

    # bad ditto if in the road 
    if message.channel.id == THE_ROAD and message.author != ditto and message.author != client.user:
        member = message.author 

        # Resolve the roles from the guild
        good_ditto = message.guild.get_role(GOOD_ROLE)
        bad_ditto = message.guild.get_role(BAD_ROLE)
        law_disobeyer = message.guild.get_role(LAW_DISOBEYER_ROLE)

        good = good_ditto in member.roles if good_ditto else False
        bad = bad_ditto in member.roles if bad_ditto else False

        the_road = client.get_channel(THE_ROAD)

        if good and not bad:
            try:
                await member.add_roles(bad_ditto, reason="Entered The Road")
                await member.add_roles(law_disobeyer, reason="Entered The Road")
                await member.remove_roles(good_ditto, reason="Entered The Road")
                await the_road.send(f"# {member.mention} YOU HAVE ENTERED THE ROAD")
            except discord.Forbidden:
                print("no perms to update roles")
            except discord.HTTPException as e:
                print(f"failed to update roles: {e}")
    
    # pato mention
    if message.author != client.user:
        if "pato" in message.content.lower():
            response_options = [
                "# OMG PATO THE CUTIEEEEE!",
                "i love pato",
                "pato cutest kitty",
                "kitty.....",
                "https://tenor.com/view/happy-cat-gif-10804346947536782797",
                "meowmeowmeow",
            ]
            response = random.choice(response_options)
            await message.add_reaction("🐈")
            await message.add_reaction("😺")
            await message.add_reaction("😻")
            await message.reply(response)

    # stinky mention
    if message.author != client.user:
        if "stinky" in message.content.lower():
            response_options = [
                f"thats right! {octo.mention} is super stinky!",
                "ditto isnt stinky at all!",
                f"{octo.mention} is the most stinky!",
                f"ewwwww {octo.mention} stinky af",
            ]
            response = random.choice(response_options)
            await message.reply(response)

    # pato pic by octo
    if message.channel.id == PATO and message.author == octo and len(message.attachments) != 0:
        attached = message.attachments
        if attached[0].content_type.startswith("image") or attached[0].content_type.startswith("video"):
            if not "gif" in attached[0].url and not "tenor" in attached[0].url:
                await message.add_reaction("🐈")
                await message.add_reaction("😺")
                await message.add_reaction("😻")
                await message.reply("thank you so much for the pato pic")
    
    # Check if it's a DM (no guild)
    if message.guild is None and message.author.id != client.user.id:
        # Forward the DM content to ditto, tagged with the sender
        try:
            await ditto.send(f"DM from {message.author}")
            await message.forward(ditto)
        except discord.Forbidden:
            print("cant dm ditto")


    # fwd vn and tags test

    vn_channel = client.get_channel(VN_CHANNEL)

    if message.author == ditto and len(message.attachments) != 0:
         if message.channel.id == V_SPOT:
            attached = message.attachments
            
            if attached[0].is_voice_message():
                    await message.forward(vn_channel)

                    # Forward tags 
                    if message.reference is not None:
                        # see if message was a reply to another message 
                        
                        request = message.reference.resolved

                        # the user replied to a message sent BY the bot
                        if request is not None and request.author.id == client.user.id:

                            tags = request.content.split("—")[-1].strip()
                            await vn_channel.send(tags)

    

@tree.command(name="dmbehalf", description="Set a user to DM and relay messages to ditto")
@app_commands.describe(user="The user ID who the bot should DM")
@app_commands.describe(message="The initial message to send to the user")
async def dmbehalf(interaction: discord.Interaction, user: discord.User, message: str):
    
    # ditto use only
    if interaction.user.id != ditto.id:
        await interaction.response.send_message("You're not authorized to use this command.", ephemeral=True)
        return

    try:
        await user.send(message)
        await interaction.response.send_message("success", ephemeral=True)
        await ditto.send(f"DM sent to {user.mention} containing: {message}")
    except discord.Forbidden:
        await interaction.response.send_message(
            f"failed to DM {user.mention}.",
            ephemeral=True
        )

@tree.command(name="sendchannel", description="Send a message to a channel on behalf of ditto")
@app_commands.describe(channel_id="The channel to send the message in")
@app_commands.describe(message="The message to send")
async def sendchannel(interaction: discord.Interaction, channel_id: str, message: str):
    
    # ditto use only
    if interaction.user.id != ditto.id:
        await interaction.response.send_message(
            "You're not authorized to use this command.", ephemeral=True
        )
        return

    # obtain channel 
    try:
        channel = interaction.client.get_channel(int(channel_id))
        if channel is None:
            await interaction.response.send_message("Invalid channel ID.", ephemeral=True)
            return
    except ValueError:
        await interaction.response.send_message("Invalid channel ID format.", ephemeral=True)
        return

    # send message
    try:
        await channel.send(message)
        await interaction.response.send_message("success", ephemeral=True)
        await ditto.send(f"Message sent to {channel.mention} containing: {message}")
    except discord.Forbidden:
        await interaction.response.send_message(
            f"no permission to send messages in {channel.mention}.",
            ephemeral=True
        )
    except discord.HTTPException as e:
        await interaction.response.send_message(
            f"Failed to send: {e}", ephemeral=True
        )

# RUN BOT #

client.run(TOKEN)
