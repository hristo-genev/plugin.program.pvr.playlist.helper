The PVR Playlist Helper Kodi addon does the following:
1. Allows you to modify any property of any stream in a given playlist.
2. Raplaces dynamic stream URLs with static, which helps the Kodi TV Channel's manager to remember the changes done on any channel. 
3. Reorder streams
4. Disable streams 

To modify any stream property in a playlist, you need to provide a JSON map with key-value pairs, where the key is the name of the stream.
For instance, the following map tells the app to change the group-title stream attribute of each stream:

`{
  'Channel 1': { 'group-title': 'National', 'tvg-id': 'channel.1.id' },
  'The Sport Channel': { 'group-title': 'Sports' }
}`

As a result, a stream like this:

`#EXTINF:-1 tvg-id="id1" group-title="cinema",Channel 1`

becomes:

`#EXTINF:-1 tvg-id="channel.1.id" group-title="National",Channel 1`


Dynamic stream URLs are changed to static ones and servered from a small HTTP server which redirects to the original stream. 
This helps Kodi TV Manager remembers any changes you do to any stream/channels. 
As a result of the modification, stream URL like this:

`http://cdn.streaming.server.com/stream/55432A32F12CC19B`

becomes:

`http://127.0.0.1:18910/streams/Channel1` 
