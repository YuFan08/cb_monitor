"""Domain exceptions for CB Monitor."""


class CbMonitorError(RuntimeError):
    """Base class for expected application errors."""


class AuthRequiredError(CbMonitorError):
    """Raised when authenticated Chaturbate access is not configured or expired."""


class CloudflareChallengeError(CbMonitorError):
    """Raised when Cloudflare rejects the current browser session."""


class EmptyFollowedListError(CbMonitorError):
    """Raised when no followed live rooms can be parsed."""


class RoomOfflineError(CbMonitorError):
    """Raised when a room page does not expose a playable stream."""


class PlaylistParseError(CbMonitorError):
    """Raised when a master playlist cannot be parsed."""


class PlayerLaunchError(CbMonitorError):
    """Raised when mpv cannot be launched."""
