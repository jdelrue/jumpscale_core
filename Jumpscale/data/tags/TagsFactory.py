

from Jumpscale import j
from .Tags import Tags

JSBASE = j.application.JSBaseClass
class TagsFactory(JSBASE):
    """
    Factory Class of dealing with TAGS
    """

    def __init__(self):
        self.__jslocation__ = "j.data.tags"
        JSBASE.__init__(self)

    def getObject(self, tagstring="", setFunction4Tagstring=None, keepcase=False):
        """
        check whether labelname exists in the labels

        @param tagstring:  example "important customer:kristof"
        @type tagstring: string
        """
        return Tags(tagstring, setFunction4Tagstring, keepcase=keepcase)

    def getTagString(self, labels=None, tags=None):
        """
        Return a valid tags string, it's recommended to use this function
        and not to build the script manually to skip reserved letters.

        @param labels: A set of labels
        @param tags: A dict with key values
        """
        labels = labels or set()
        tags = tags or dict()
        if not isinstance(labels, set):
            raise TypeError("labels must be of type set")

        if not isinstance(tags, dict):
            raise TypeError("tags must be of type dict")

        t = Tags()
        t.labels = labels
        t.tags = tags
        return str(t)
