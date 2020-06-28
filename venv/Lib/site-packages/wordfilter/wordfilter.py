import json
from pkg_resources import resource_string

# We'll need this to check if something is a string later.
# This isn't great, but it's better than a dependency on six.
try:
    str
except NameError:
    str = str


class Wordfilter(object):

    """filter out bad words"""

    blacklist = []

    def __init__(self, blacklist=None, datafile=None):
        if isinstance(blacklist, list):
            self.blacklist = blacklist
            return

        if datafile:
            with open(datafile, 'r') as f:
                self.blacklist = f.read().splitlines()

        else:
            data = resource_string('wordfilter', '../badwords.json').decode('utf-8')
            self.blacklist = [s.lower() for s in json.loads(data)]

    def blacklisted(self, string):
        string = string.lower()
        return any(word in string for word in self.blacklist)

    def add_words(self, lis):
        if isinstance(lis, str):
            lis = [lis]

        self.blacklist.extend([s.lower() for s in lis])

    def remove_words(self, lis):
        if isinstance(lis, str):
            lis = [lis]

        for s in lis:
            try:
                self.blacklist.remove(s.lower())
            except ValueError:
                pass

    def clear_list(self):
        self.blacklist = []

# instantiates instance so functions are available directly from module
_module_instance = Wordfilter()
blacklisted = _module_instance.blacklisted
add_words = _module_instance.add_words
clear_list = _module_instance.clear_list
remove_words = _module_instance.remove_words
