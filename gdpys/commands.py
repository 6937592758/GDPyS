from listeners import listener
import asyncio

class Commands:
    def __init__(self, prefix):
        self.commands = {}
        self.prefix = prefix
    
    def command(self, func, *args):
        def wrapper():
            self.commands[func.__name__] = {"func": func, "args": args}
        return wrapper
  
    @listener.event
    def on_upload_comment(self, username, comment):
        for name, func in self.commands.items():
            if comment.startswith(self.prefix + name):
                func["func"](func["args"])
                # add delete comment
                
# fix listeners and add arguments for this to be complete