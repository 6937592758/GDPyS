import asyncio
from aiohttp.payload_streamer import streamer
from helpers.userhelper import user_helper
from helpers.levelhelper import level_helper
from helpers.generalhelper import dict_keys
from helpers.timehelper import get_timestamp
from objects.comments import CommandContext, Comment, CommentBan
from constants import Permissions
from config import user_config
from exceptions import GDPySCommandError
from objects.levels import Level, Rating

COMMANDS = {}

class Client:
    def __init__(self):
        pass
    
    ############################
    #           User           #
    ############################ 

    async def username_to_id(self, username: str) -> int:
        """Convert a username to an id"""
        return await user_helper.get_accountid_from_username(username)

    async def get_user_rank(self, id: int) -> int:
        """Get the rank of a user"""
        return await user_helper.get_rank(id)

    async def post_account_comment(self, id: int, comment: str) -> bool:
        """Post an account comment to a user's account"""
        return await user_helper.post_account_comment(id, comment, False, False)

    ############################
    #           Level          #
    ############################ 

    async def get_level(self, id: int) -> Level:
        """Get a level object"""
        return await level_helper.get_level_obj(id)

    async def star_to_difficulty(stars: int) -> int:
        """Convert star rating to a difficulty"""
        return await level_helper.star_to_difficulty(stars)

    async def like_level(id: int):
        """Bump a level's likes by one"""
        return await level_helper.bump_likes(id)

    async def upload_level(level: Level):
        """Uploads a level from a level object"""
        return await level_helper.upload_level(level)

    async def rate_level(rating: Rating):
        """Rates a level given a Rating object"""
        return await level_helper.rate_level(rating)

    ############################
    #         Commands         #
    ############################ 

    def command(self, coro: asyncio.coroutine, name: str=None, permission: Permissions=None):
        """Decorator to create commands"""
        if not asyncio.iscoroutine(coro):
            raise Exception("Function is not a coroutine function!")

        if name is None:
            name = coro.__name__.lower()

        def decorator(coro):
            loop = asyncio.new_event_loop()
            loop.create_task(self.create_command(name, coro, permission))

        return decorator

    async def create_command(self, name: str, coro: asyncio.coroutine, permission: Permissions) -> None:
        """Create a command"""
        COMMANDS[name]= {
            "handler": coro,
            "permission": permission
        }

    def _command_exists(self, command : str) -> bool:
        """:meta private: Checks if a given comment is a valid command."""
        command = command.split(" ")[0].lower()
        return command[len(user_config["command_prefix"]):] in dict_keys(COMMANDS)
    
    async def _create_context(self, comment : Comment) -> CommandContext:
        """:meta private: Creates a context object for a command."""
        level = await level_helper.get_level_obj(comment.level_id)
        account = await user_helper.get_object(await user_helper.accid_userid(comment.user_id))
        return CommandContext(
            level,
            comment,
            account
        )

    async def _execute_command(self, command_obj : Comment):
        """:meta private: Executes a GDPyS command comment command. Returns a bool or commentban object."""
        command_args = command_obj.comment[len(user_config["command_prefix"]):].split(" ")
        command = COMMANDS[command_args[0].lower()]
        ctx = await self.create_context(command_obj)
        account = await user_helper.get_object(await user_helper.accid_userid(command_obj.user_id)) # SHOULD be already cached.
        if not user_helper.has_privilege(account, command["permission"]):
            return False
        try:
            await command["handler"](ctx)
        except GDPySCommandError as e:
            return CommentBan(
                0, # /shrug
                get_timestamp(),
                f"GDPyS Command Exception in {command['handler'].__name__.replace('_', '-')}:\n{e}" # Replace as _s mess up the response
            )
        return True

client = Client()