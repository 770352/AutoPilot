import discord, asyncio, random, youtube_dl, string, os
from discord.ext import commands
from discord.ext.commands import command
import AutoPilot
import math
from Cogs import moderationCog


# External Music player Code, was not wrote by me.

# Whomever wrote this was stupid as they labeled context as message please don't ever do this

defaultVolume = 0.5
volumes = {}

# flat-playlist:True?
# extract_flat:True
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '{}',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    "extractaudio": True,
    "audioformat": "opus",
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

stim = {
    'default_search': 'auto',
    "ignoreerrors": True,
    'quiet': True,
    "no_warnings": True,
    "simulate": True,  # do not keep the video files
    "nooverwrites": True,
    "keepvideo": False,
    "noplaylist": True,
    "skip_download": True,
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
    # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}


class Downloader(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get("url")
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')
        self.views = data.get('view_count')
        self.playlist = {}

    @classmethod
    async def video_url(cls, url, ytdl, *, loop=None, stream=False):
        """
        Download the song file and data
        """
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        data1 = {'queue': []}
        if 'entries' in data:
            if len(data['entries']) > 1:
                playlist_titles = [title['title'] for title in data['entries']]
                data1 = {'title': data['title'], 'queue': playlist_titles}
                data1['queue'].pop(0)

            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data), data1

    async def get_info(self, url):
        """
        Get the info of the next song by not downloading the actual file but just the data of song/query
        """
        yt = youtube_dl.YoutubeDL(stim)
        down = yt.extract_info(url, download=False)
        data1 = {'queue': []}
        if 'entries' in down:
            if len(down['entries']) > 1:
                playlist_titles = [title['title'] for title in down['entries']]
                data1 = {'title': down['title'], 'queue': playlist_titles}

            down = down['entries'][0]['title']

        return down, data1


class MusicPlayer(commands.Cog, name='Music'):
    def __init__(self, client):
        self.bot = client
        self.modUtility = moderationCog.ModUtilityModule(self.bot)
        # self.database = pymongo.MongoClient(os.getenv('MONGO'))['Discord-Bot-Database']['General']
        # self.music=self.database.find_one('music')
        self.player = {
            "audio_files": []
        }

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        await self.removeFromAFK()

    async def removeFromAFK(self):
        await asyncio.sleep(1)
        guilds = await self.bot.fetch_guilds(limit=150).flatten()
        for guild in guilds:
            guild = self.bot.get_guild(int(guild.id))
            afkChannel = guild.afk_channel
            if afkChannel:
                for member in afkChannel.members:
                    await member.edit(voice_channel=None)

    @property
    def random_color(self):
        return discord.Color.from_rgb(random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))

    # def cog_unload(self):
    #     """
    #     Update the database in mongodb to the latest changes when the bot is disconnecting
    #     """
    #     current=self.database.find_one('music')
    #     if current != self.voice:
    #         self.database.update_one({'_id':'music'},{'$set':self.music})

    @commands.Cog.listener('on_voice_state_update')
    async def music_voice(self, user, before, after):
        """
        Clear the server's playlist after bot leave the voice channel
        """
        if after.channel is None and user.id == self.bot.user.id:
            try:
                self.player[user.guild.id]['queue'].clear()
            except KeyError:
                # NOTE: server ID not in bot's local self.player dict
                print(
                    f"Failed to get guild id {user.guild.id}")  # Server ID lost or was not in data before disconnecting

    async def filename_generator(self):
        """
        Generate a unique file name for the song file to be named as
        """
        chars = list(string.ascii_letters + string.digits)
        name = ''
        for i in range(random.randint(9, 25)):
            name += random.choice(chars)

        if name not in self.player['audio_files']:
            return name

        return await self.filename_generator()

    async def playlist(self, data, context):
        """
        THIS FUNCTION IS FOR WHEN YOUTUBE LINK IS A PLAYLIST
        Add song into the server's playlist inside the self.player dict
        """
        for i in data['queue']:
            self.player[context.guild.id]['queue'].append({'title': i, 'author': context})

    async def queue(self, context, song):
        """
        Add the query/song to the queue of the server
        """
        title1 = await Downloader.get_info(self, url=song)
        title = title1[0]
        data = title1[1]
        # NOTE:needs fix here
        if data['queue']:
            await self.playlist(data, context)
            # NOTE: needs to be embeded to make it better output
            return await context.send(f"Added playlist {data['title']} to queue")
        self.player[context.guild.id]['queue'].append({'title': title, 'author': context})
        embed = discord.Embed(title="Song Added to queue", description=f"**{title}**".title())
        return await context.send(embed=embed)

    async def voice_check(self, context):
        """
        function used to make bot leave voice channel if music not being played for longer than 2 minutes
        """
        if context.voice_client is not None:
            await asyncio.sleep(120)
            if context.voice_client is not None and context.voice_client.is_playing() is False and context.voice_client.is_paused() is False:
                await context.voice_client.disconnect()

    async def clear_data(self, context):
        """
        Clear the local dict data
            name - remove file name from dict
            remove file and filename from directory
            remove filename from global audio file names
        """
        name = self.player[context.guild.id]['name']
        os.remove(name)
        self.player['audio_files'].remove(name)

    async def loop_song(self, context):
        """
        Loop the currently playing song by replaying the same audio file via `discord.PCMVolumeTransformer()`
        """
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.player[context.guild.id]['name']))
        loop = asyncio.get_event_loop()
        try:
            context.voice_client.play(source, after=lambda a: loop.create_task(self.done(context)))
            # if str(context.guild.id) in self.music:
            #     context.voice_client.source.volume=self.music['vol']/100
        except Exception as Error:
            # Has no attribute play
            print(Error)  # NOTE: output back the error for later debugging

    async def done(self, context, contextId: int = None):
        """
        Function to run once song completes
        Delete the "Now playing" message via ID
        """
        if contextId:
            try:
                message = await context.channel.fetch_message(contextId)
                await message.delete()
            except Exception as Error:
                print("Failed to get the message")

        if self.player[context.guild.id]['reset'] is True:
            self.player[context.guild.id]['reset'] = False
            return await self.loop_song(context)

        if context.guild.id in self.player and self.player[context.guild.id]['repeat'] is True:
            return await self.loop_song(context)

        await self.clear_data(context)

        if self.player[context.guild.id]['queue']:
            queue_data = self.player[context.guild.id]['queue'].pop(0)
            return await self.start_song(context=queue_data['author'], song=queue_data['title'])


        else:
            await self.voice_check(context)

    async def start_song(self, context, song):

        new_opts = ytdl_format_options.copy()
        audio_name = await self.filename_generator()

        self.player['audio_files'].append(audio_name)
        new_opts['outtmpl'] = new_opts['outtmpl'].format(audio_name)

        ytdl = youtube_dl.YoutubeDL(new_opts)

        download1 = await Downloader.video_url(song, ytdl=ytdl, loop=self.bot.loop)

        download = download1[0]
        data = download1[1]
        self.player[context.guild.id]['name'] = audio_name
        emb = discord.Embed(colour=self.random_color, title='Now Playing', description=download.title, url=download.url)
        emb.set_thumbnail(url=download.thumbnail)
        emb.set_footer(text=f'Requested by {context.author.display_name}', icon_url=context.author.avatar_url)
        loop = asyncio.get_event_loop()

        if data['queue']:
            await self.playlist(data, context)

        contextId = await context.send(embed=emb)
        self.player[context.guild.id]["player"] = download
        self.player[context.guild.id]['author'] = context
        context.voice_client.play(download, after=lambda a: loop.create_task(self.done(context, contextId.id)))
        try:
            context.voice_client.source.volume = volumes[context.guild.id]
        except KeyError:
            context.voice_client.source.volume = defaultVolume
            volumes[context.guild.id] = defaultVolume

        # if str(context.guild.id) in self.music: #NOTE adds user's default volume if in database
        #     context.voice_client.source.volume=self.music[str(context.guild.id)]['vol']/100
        return context.voice_client

    @commands.command()
    async def play(self, context, *, song):
        """
        Play a song with given url or title from Youtube
        `Ex:` s.play Titanium David Guetta
        `Command:` play(song_name)
        """
        channel = context.channel
        async with channel.typing():
            pass

        if context.guild.id in self.player:
            if context.voice_client.is_playing() is True:  # NOTE: SONG CURRENTLY PLAYING
                return await self.queue(context, song)

            if self.player[context.guild.id]['queue']:
                return await self.queue(context, song)

            if context.voice_client.is_playing() is False and not self.player[context.guild.id]['queue']:
                try:
                    return await self.start_song(context, song)
                except ValueError:
                    await context.send("AutoPilot was unable to find that song")


        else:
            # IMPORTANT: THE ONLY PLACE WHERE NEW `self.player[context.guild.id]={}` IS CREATED
            self.player[context.guild.id] = {
                'player': None,
                'queue': [],
                'author': context,
                'name': None,
                "reset": False,
                'repeat': False
            }
            try:
                return await self.start_song(context, song)
            except ValueError:
                await context.send("AutoPilot was unable to find that song")

    @play.before_invoke
    async def before_play(self, context):
        """
        Check voice_client
            - User voice = None:
                please join a voice channel
            - bot voice == None:
                joins the user's voice channel
            - user and bot voice NOT SAME:
                - music NOT Playing AND queue EMPTY
                    join user's voice channel
                - items in queue:
                    please join the same voice channel as the bot to add song to queue
        """

        if context.author.voice is None:
            return await context.send('**Please join a voice channel to play music**'.title())

        if context.voice_client is None:
            return await context.author.voice.channel.connect()

        if context.voice_client.channel != context.author.voice.channel:

            # NOTE: Check player and queue
            if context.voice_client.is_playing() is False and not self.player[context.guild.id]['queue']:
                return await context.voice_client.move_to(context.author.voice.channel)
                # NOTE: move bot to user's voice channel if queue does not exist

            if self.player[context.guild.id]['queue']:
                # NOTE: user must join same voice channel if queue exist
                return await context.send("Please join the same voice channel as the bot to add song to queue")


    @commands.command()
    async def repeat(self, context):
        """
        Repeat the currently playing or turn off by using the command again
        `Ex:` .repeat
        `Command:` repeat()
        """
        if context.guild.id in self.player:
            if context.voice_client.is_playing() is True:
                if self.player[context.guild.id]['repeat'] is True:
                    self.player[context.guild.id]['repeat'] = False
                    # return await context.message.add_reaction(emoji='✅')
                    return

                self.player[context.guild.id]['repeat'] = True
                # return await context.message.add_reaction(emoji='✅')
                return

            return await context.send("No audio currently playing")
        return await context.send("Bot not in voice channel or playing music")

    @commands.command(aliases=['restart-loop'])
    async def reset(self, context):
        """
        Restart the currently playing song  from the begining
        `Ex:` s.reset
        `Command:` reset()
        """
        if context.voice_client is None:
            return await context.send(f"**{context.author.display_name}, there is no audio currently playing from the bot.**")

        if context.author.voice is None or context.author.voice.channel != context.voice_client.channel:
            return await context.send(f"**{context.author.display_name}, you must be in the same voice channel as the bot.**")

        if self.player[context.guild.id]['queue'] and context.voice_client.is_playing() is False:
            return await context.send("**No audio currently playing or songs in queue**".title(), delete_after=25)

        self.player[context.guild.id]['reset'] = True
        context.voice_client.stop()

    @commands.command()
    async def skip(self, context):
        """
        Skip the current playing song
        `Ex:` s.skip
        `Command:` skip()
        """
        if context.voice_client is None:
            return await context.send("**No music currently playing**".title(), delete_after=60)

        if context.author.voice is None or context.author.voice.channel != context.voice_client.channel:
            return await context.send("Please join the same voice channel as the bot")

        def check(reaction, user):
            return user in context.author.voice.channel.members and reaction.emoji in "✅" and user is not context.author

        if self.modUtility.getAPLevel(context.guild, context.author.id) >= 1:
            await self._skip(context)
            return
        else:
            await context.message.clear_reactions()
            await context.message.add_reaction("✅")
            waiting = True
            voted = 0
            required = math.floor(len(context.author.voice.channel.members) * 0.5)
            while waiting and voted < required:
                try:
                    react, user = await self.bot.wait_for('reaction_add', timeout=20, check=check)
                    voted += 1
                except asyncio.TimeoutError:
                    await context.send("Not enough members voted")
                    return
            await self._skip(context)


    async def _skip(self, context):
        if self.player[context.guild.id]['queue'] and context.voice_client.is_playing() is False:
            return await context.send("**No songs in queue to skip**".title(), delete_after=60)

        self.player[context.guild.id]['repeat'] = False
        context.voice_client.stop()
        return await context.message.add_reaction(emoji='✅')

    @commands.command()
    async def stop(self, context):
        """
        Stop the current playing songs and clear the queue
        `Ex:` s.stop
        `Command:` stop()
        """
        if context.voice_client is None:
            return await context.send("Bot is not connect to a voice channel")

        if context.author.voice is None:
            return await context.send("You must be in the same voice channel as the bot")

        if context.author.voice is not None and context.voice_client is not None:
            if context.voice_client.is_playing() is True or self.player[context.guild.id]['queue']:
                self.player[context.guild.id]['queue'].clear()
                self.player[context.guild.id]['repeat'] = False
                context.voice_client.stop()
                # return await context.message.add_reaction(emoji='✅')
                return

            return await context.send(
                f"**{context.author.display_name}, there is no audio currently playing or songs in queue**")


    @commands.command(aliases=['get-out', 'disconnect', 'leave-voice'])
    async def leave(self, context):
        """
        Disconnect the bot from the voice channel
        `Ex:` s.leave
        `Command:` leave()
        """
        if context.author.voice is not None and context.voice_client is not None:
            if context.voice_client.is_playing() is True or self.player[context.guild.id]['queue']:
                self.player[context.guild.id]['queue'].clear()
                context.voice_client.stop()
                return await context.voice_client.disconnect(), await context.message.add_reaction(emoji='✅')

            return await context.voice_client.disconnect(), await context.message.add_reaction(emoji='✅')

        if context.author.voice is None:
            return await context.send("You must be in the same voice channel as bot to disconnect it via command")


    @commands.command()
    async def pause(self, context):
        """
        Pause the currently playing audio
        `Ex:` s.pause
        `Command:` pause()
        """
        if context.author.voice is not None and context.voice_client is not None:
            if context.voice_client.is_paused() is True:
                return await context.send("Song is already paused")

            if context.voice_client.is_paused() is False:
                context.voice_client.pause()
                # await context.message.add_reaction(emoji='✅')


    @commands.command()
    async def resume(self, context):
        """
        Resume the currently paused audio
        `Ex:` s.resume
        `Command:` resume()
        """
        if context.author.voice is not None and context.voice_client is not None:
            if context.voice_client.is_paused() is False:
                return await context.send("Song is already playing")

            if context.voice_client.is_paused() is True:
                context.voice_client.resume()
                return
                # return await context.message.add_reaction(emoji='✅')

    @command(name='queue', aliases=['song-list', 'q', 'current-songs'])
    async def _queue(self, context):
        """
        Show the current songs in queue
        `Ex:` s.queue
        `Command:` queue()
        """
        if context.voice_client is not None:
            if context.guild.id in self.player:
                if self.player[context.guild.id]['queue']:
                    emb = discord.Embed(colour=self.random_color, title='queue')
                    emb.set_footer(text=f'Command used by {context.author.name}', icon_url=context.author.avatar_url)
                    for i in self.player[context.guild.id]['queue']:
                        emb.add_field(name=f"**{i['author'].author.name}**", value=i['title'], inline=False)
                    return await context.send(embed=emb, delete_after=120)

        return await context.send("No songs in queue")

    @command(name='song-info', aliases=['song?', 'nowplaying', 'current-song'])
    async def song_info(self, context):
        """
        Show information about the current playing song
        `Ex:` s.song-info
        `Command:` song-into()
        """
        if context.voice_client is not None and context.voice_client.is_playing() is True:
            emb = discord.Embed(colour=self.random_color, title='Currently Playing',
                                description=self.player[context.guild.id]['player'].title)
            emb.set_footer(text=f"{self.player[context.guild.id]['author'].author.name}", icon_url=context.author.avatar_url)
            emb.set_thumbnail(url=self.player[context.guild.id]['player'].thumbnail)
            return await context.send(embed=emb, delete_after=120)

        return await context.send(f"**No songs currently playing**".title(), delete_after=30)

    @command(aliases=['move-bot', 'move-b', 'mb', 'mbot'])
    async def join(self, context, *, channel: discord.VoiceChannel = None):
        """
        Make bot join a voice channel you are in if no channel is mentioned
        `Ex:` .join (If voice channel name is entered, it'll join that one)
        `Command:` join(channel:optional)
        """
        if context.voice_client is not None:
            return await context.send(f"Bot is already in a voice channel\nDid you mean to use {context.prefix}moveTo")

        if context.voice_client is None:
            if channel is None:
                return await context.author.voice.channel.connect(), await context.message.add_reaction(emoji='✅')

            return await channel.connect(), await context.message.add_reaction(emoji='✅')

        else:
            if context.voice_client.is_playing() is False and not self.player[context.guild.id]['queue']:
                return await context.author.voice.channel.connect(), await context.message.add_reaction(emoji='✅')

    @join.before_invoke
    async def before_join(self, context):
        if context.author.voice is None:
            return await context.send("You are not in a voice channel")

    @join.error
    async def join_error(self, context, error):
        if isinstance(error, commands.BadArgument):
            return context.send(error)

        if error.args[0] == 'Command raised an exception: Exception: playing':
            return await context.send("**Please join the same voice channel as the bot to add song to queue**".title())

    @command(aliases=['vol'])
    async def volume(self, context, vol):
        """
        Change the volume of the bot
        `Ex:` .vol 100 (200 is the max)
        `Permission:` manage_channels
        `Command:` volume(amount:integer)
        """
        vol = float(vol)
        if vol > 200:
            vol = 200
        vol = vol / 100

        if context.author.voice is not None:
            if context.voice_client is not None:
                if context.voice_client.channel == context.author.voice.channel and context.voice_client.is_playing() is True:
                    context.voice_client.source.volume = vol
                    # if (context.guild.id) in self.music:
                    #     self.music[str(context.guild.id)]['vol']=vol
                    volumes[context.guild.id] = vol

    @volume.error
    async def volume_error(self, context, error):
        if isinstance(error, commands.MissingPermissions):
            return await context.send("Manage channels or admin perms required to change volume", delete_after=30)


def setup(bot):
    bot.add_cog(MusicPlayer(bot))