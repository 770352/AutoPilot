from discord.ext import commands
import discord, json
import asyncio
from discord.utils import get
import urllib.request, urllib.parse, urllib.request
from bs4 import BeautifulSoup
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL
isCog = True
isEnabled = False

def setup(client):
    client.add_cog(MusicModule(client))

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)

class MusicModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.queues = {}
        self.next = asyncio.Event()

    async def joinVC(self,context):
        channel = context.message.author.voice.channel
        if not channel:
            await context.send("You are not connected to a voice channel")
        voice = get(self.client.voice_clients, guild=context.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        return voice

    async def autoPlay(self,context,VC):

        print(str(self.queues))
        guildID = context.guild.id
        if len(self.queues[str(guildID)]['Queue']) < 1:
            print("Removing Queue")
            del self.queues[str(guildID)]
            return
        source  = self.queues[str(guildID)]['Queue'].pop(0)
        print("Playing new song")
        source = await YTDLSource.regather_stream(source, loop=self.client.loop)

        VC.play(source, after=lambda _: self.client.loop.create_task(self.autoPlay(context,VC)))


    async def play(self,context,search):
        VC = await self.joinVC(context)
        source = await YTDLSource.create_source(context, search, loop=self.client.loop, download=False)
        id = context.guild.id
        if str(id) in self.queues.keys():
            self.queues[str(id)]['Queue'].append(source)
        else:
            print("Starting New AutoPlay")
            self.queues.update({str(id):{'Queue':[source],'VC':VC}})
            self.client.loop.create_task(self.autoPlay(context,VC))

    @commands.command()
    async def skip(self,context):
        id = context.guild.id
        VC = self.queues[str(id)]["VC"]
        VC.stop()
        await context.send("Song has been skiped")

    @commands.command()
    async def queue(self,context):
        embed = discord.Embed(title="Queue for server: " + str(context.guild.name))
        guildID = context.guild.id
        for song in self.queues[str(guildID)]:
            pass

    @commands.command()
    async def search(self,context):
        print("Running Muisc Search")
        channel = context.channel
        async with channel.typing():
            thumbnail = "https://http.cat/404"
            duration = "N/A"
            Srequest = context.message.content
            textToSearch = Srequest.split(' ', 1)[1]
            query = urllib.parse.quote(textToSearch)
            HasResults = False
            while not HasResults:
                url = "https://www.youtube.com/results?search_query=" + query + "&sp=EgIQAQ%253D%253D"
                response = urllib.request.urlopen(url)
                await asyncio.sleep(0.1)
                html = response.read()
                await asyncio.sleep(0.1)
                soup = BeautifulSoup(html, 'html.parser')
                await asyncio.sleep(0.1)
                vidcount = 1

                embed = discord.Embed(title="Results For \"" + str(textToSearch) + "\"", color=0x00ff00)
                if len(soup.findAll(attrs={'class': 'yt-uix-tile-link'})) > 2:
                    for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
                        result = ("#" + str(vidcount) + " " + str(vid['title']))
                        embed.add_field(name="Song#" + str(vidcount), value=str(result), inline=False)
                        if vidcount > 4:
                            break
                        vidcount = vidcount + 1
                    HasResults = True
                else:
                    await context.send("HTML response is empty")


            message = await context.send("Select The Song To Play", embed=embed)
            noSelection = True
            while noSelection:
                await message.clear_reactions()
                #await message.add_reaction(u"\N{Digit One}")
                await message.add_reaction(u"\u0031\u20E3")
                await message.add_reaction(u"\u0032\u20E3")
                await message.add_reaction(u"\u0033\u20E3")
                await message.add_reaction(u"\u0034\u20E3")
                await message.add_reaction(u"\u0035\u20E3")
                #await message.add_reaction(":x:")
                #await message.add_reaction("U+FEB45")
                reacts = [u"\u0031\u20E3", u"\u0032\u20E3", u"\u0033\u20E3", u"\u0034\u20E3", u"\u0035\u20E3"]
                def check(reaction, user):
                    print(str(reaction) + ":" + str(reacts))
                    print(str(user) + ":" + str(context.message.author))
                    return user == context.message.author and reaction.emoji in reacts

                # await client.add_reaction(message,'❌')
                await asyncio.sleep(0.5)
                try:
                    react, user = await self.client.wait_for('reaction_add', timeout=20, check=check)
                except asyncio.TimeoutError:
                    await context.send("Request Timed Out")
                    return
                print("React")
                noSelection = False
                if str(react) == "1⃣":
                    select = 0
                elif str(react) == u"\u0031\u20E3":
                    select = 0
                elif str(react) == u"\u0032\u20E3":
                    select = 1
                elif str(react) == u"\u0033\u20E3":
                    select = 2
                elif str(react) == u"\u0034\u20E3":
                    select = 3
                elif str(react) == u"\u0035\u20E3":
                    select = 4
                else:
                    noSelection = True

            print("Selected: " + str(select))
            vid = soup.findAll(attrs={'class': 'yt-uix-tile-link'})[select]


            # print(str(vid))
            id = vid['href'].split("=")[1]
            thumbnail = "https://img.youtube.com/vi/" + str(id) + "/hqdefault.jpg"
            # print(str(vid))
            embed = discord.Embed(title="Playing: " + str(vid['title']), color=0x00ff00)
            embed.set_thumbnail(url=str(thumbnail))
            embed.add_field(name="Length", value="Working...", inline=True)
            await message.edit(content=" ", embed=embed)
            embed2 = discord.Embed(title="Playing: " + str(vid['title']), color=0x00ff00)
            try:
                api_key = "AIzaSyCPwakxCnVg_q3RyDWmbBUr5yB-YIL-MNY"
                searchUrl = "https://www.googleapis.com/youtube/v3/videos?id=" + str(id) + "&key=" + str(api_key) + "&part=contentDetails"
                response = urllib.request.urlopen(str(searchUrl)).read()
                data = json.loads(response)
                # print(str(data))
                all_data = data['items']
                contentDetails = all_data[0]['contentDetails']
                # print(str(contentDetails))
                durationdata = contentDetails['duration']
                duration = durationdata.split("PT")[1]
                lminutes = duration.split("M")[0]
                lseconds = duration.split("M")[1]
                embed2.add_field(name="Length", value=str(lminutes) + ":" + str(lseconds.split("S")[0]), inline=True)
            except Exception as e:
                print(str(e))
                embed2.add_field(name="Length", value=str(e), inline=True)
                print("no length")
            embed2.set_thumbnail(url=str(thumbnail))


            await message.edit(content=" ", embed=embed2)

            #await self.play(context,"https://www.youtube.com/watch?v=" + str(id))
            await self.play(context,str(id))
            return
            # return str('https://www.youtube.com'+ vid['href'])



class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f'**Now Playing:** `{source.title}` requested by '
                                               f'`{source.requester}`')
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        #await ctx.send(f'```ini\n[Added {data["title"]} to the Queue.]\n```', delete_after=15)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)
