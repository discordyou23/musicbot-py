import asyncio
import discord
from discord.ext import commands
if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')

def __init__(self, bot):
        self.bot = bot

class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = ' {0.title} 작성자 {0.uploader}  {1.display_name} 가 신청했느니라'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [길이: {0[0]}분 {0[1]}초]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, '지금 틀고있는 노래이니라' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()
class Music:
    """여러 서버에서 사용중이느니라...
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """나도 왔느니라~ 헤헤."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('이미 채널에 있느니라..')
        except discord.InvalidArgument:
            await self.bot.say('으냣? 음성 채널이 아니구나!')
        else:
            await self.bot.say('음악을 틀 준비가 되었느니라 **' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """나를 불러 주어라."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('날 버리고 간것이냐...?')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def p(self, ctx, *, song : str):
        """너무길어서 곡밥이가 변역하기 귀찮타 하였느니라
        """
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            await self.bot.say("노래를 가져오는 중이니라")
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = '으에에에? 오류가 발생했느니라: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('신청받았다 ' + str(entry))
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """볼륨 설정중이니라."""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))
    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """노래 계속 틀겠느냐..?"""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """나는 이제 가보겠느니라!
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
            await self.bot.say("파티가 끝난것이느냐...")
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def s(self, ctx):
        """스킵하고 싶으면 3개 아상의 찬성을 받아야 하느니라. 신청자는 원하면 스킵이 가능하니라
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('아무거도 틀고있지 않느니라...')
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('신청자가 스킵을 하고싶다 하였느니라')
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.bot.say('으냐아앗? 결국 스킵했느나?')
                state.skip()
            else:
                await self.bot.say('스킵 할것이느냐? [{}/3]'.format(total_votes))
        else:
            await self.bot.say('이미 투표하였느니라! 반칙이다!')

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """지금 틀고있는 노래이니라.."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('정적만이 흐르고 있느니라....')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('지금 틀고있는 노래이니라! 스킵의 갯수는 이러하느니라~ {} [skips: {}/3]'.format(state.current, skip_count))
        
def setup(bot):
    bot.add_cog(Music(bot))
    print('풍악을 울려라!')

