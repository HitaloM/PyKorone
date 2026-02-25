from .client import LastFMClient
from .collage import LastFMCollageError, create_album_collage
from .deezer import DeezerClient, DeezerError
from .errors import LastFMAPIError, LastFMConfigurationError, LastFMError, LastFMPayloadError, LastFMRequestError
from .formatters import format_album_status, format_artist_status, format_lastfm_error, format_status
from .types import (
    LastFMAlbumInfo,
    LastFMArtistInfo,
    LastFMRecentTrack,
    LastFMTopAlbum,
    LastFMTopArtist,
    LastFMTrackInfo,
)

__all__ = (
    "DeezerClient",
    "DeezerError",
    "LastFMAPIError",
    "LastFMAlbumInfo",
    "LastFMArtistInfo",
    "LastFMClient",
    "LastFMCollageError",
    "LastFMConfigurationError",
    "LastFMError",
    "LastFMPayloadError",
    "LastFMRecentTrack",
    "LastFMRequestError",
    "LastFMTopAlbum",
    "LastFMTopArtist",
    "LastFMTrackInfo",
    "create_album_collage",
    "format_album_status",
    "format_artist_status",
    "format_lastfm_error",
    "format_status",
)
