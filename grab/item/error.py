from grab.error import GrabError


class ItemError(GrabError):
    pass


class ChoiceFieldError(ItemError):
    pass
