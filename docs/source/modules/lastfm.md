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

```{admonition} **Supported Sizes**:
:class: seealso

`1`, `2`, `3`, `4`, `5`, `6`, `7`<br>
The size is the number of rows and columns in the collage.
```

```{admonition} **Supported Periods**:
:class: seealso

`1d`, `7d`, `1m`, `3m`, `6m`, `1y`, `all`<br>
_d: day, m: month, y: year._<br>
The period is the time range for the collage, _all_ is all time since you started scrobbling.
```

```{admonition} **Supported Types**:
:class: seealso

`artist`, `track`, `album`<br>
The type is the category of the items that you want to get in the `/lfmtop' command.
```

### Examples

 Creates a collage of your top 5x5 albums from the last 7 days and sends it to you in chat.
  > `/lfmcollage 5 7d`

- Creates a collage of your top 7x7 albums from the last month without text in album covers and sends it to you in chat.
  > `/lfmcollage 7 1m clean`

- Sends you a list of your top 5 artists in the last year.
  > `/lfmtop 1y`

- Sends you a list of your top 5 tracks of all time.
  > `/lfmtop track`
