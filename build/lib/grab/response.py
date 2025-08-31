# Back-ward compatibility
# pylint: disable=unused-import, unused-wildcard-import, wildcard-import
from grab.document import Document as Response  # noqa: I001
from grab.document import *  # noqa: F403

# TODO: throw warnings when anything from this proxy-module is used
