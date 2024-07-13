# LastFM

The LastFM module allows you to get and view information about your favorite artists, albums and tracks. You can also view your recent plays and share them with your friends.

## Commands

- `/setlfm (your username)`: Set your LastFM username.
- `/lfm`: Get the track you are currently listening to or the last track you listened to.
- `/lfmrecent`: Get your last 5 played tracks.
- `/lfmartist`: Get the artist you are currently listening to or the last artist you listened to.
- `/lfmalbum`: Get the album you are currently listening to or the last album you listened to.
- `/lfmuser`: Get your total scrobbles, tracks, artists, and albums scrobbled.
- `/lfmtop (?type)`: Get your top artists, tracks, or albums (defaults to artists).
- `/lfmcompat`: Get the compatibility of your music taste with another user.
- `/lfmcollage (?size) (?period)`: Get a collage of your top albums (defaults to `3x3` and `all`).

```{note}
**Supported sizes**: `1`, `2`, `3`, `4`, `5`, `6`, `7`

**Supported periods**: `1d`, `7d`, `1m`, `3m`, `6m`, `1y`, `all`

**Supported types**: `artist`, `track`, `album`
```

### Examples

- Generate a collage of your top 5x5 albums in a period of 7 days:
  - `/lfmcollage 5 7d`

- Generate a collage of your top 7x7 albums in a period of 1 month without text:
  - `/lfmcollage 7 1m clean`

- Get your top 5 artists in a period of 1 year:
  - `/lfmtop 1y`

- Get your top 5 tracks of all time:
  - `/lfmtop track`
