# -*- coding: utf-8 -*-
from xbmcgui import DialogProgressBG
from resources.lib.utils import *
from resources.lib.logging import log
from resources.lib.settings import settings 
from resources.lib.utils import addon, profile_path
from resources.lib.notifications import notify_error
from resources.lib.playlist import Playlist
from resources.lib.map import StreamsMap

user_agent    = get_user_agent()
scheduled_run = is_scheduled_run()
progress_bar  = None

if not scheduled_run or settings.debug:
  progress_bar = DialogProgressBG()
  progress_bar.create(heading=addon.getAddonInfo('name'))

try:
  pl = Playlist(
    log_delegate=log,
    user_agent=user_agent, 
    progress_delegate=progress_bar,
    include_only_mapped_streams=settings.only_streams_from_map,
    temp_folder=profile_path
    )

  pl.load(get_m3u_location())

  ### TODO ###
  # Concatenate other playlists
  # if settings.concat_second_playlist:
  # streams = Parser(path=get_m3u2_location(), log_delegate=log).generated_streams
  # pl.add_strems(streams)

  streamsmap = StreamsMap(
    path=get_map_location(), 
    log_delegate=log
    )
  pl.overwrite_values(streamsmap)

  if pl.has_no_streams():
    notify_error('The playlist has NO channels!')
  else:
    if settings.reorder_playlist:
      pl.reorder()
    
    pl.set_static_stream_urls(STREAM_URL)

    if not pl.save(pl_path):
      notify_error('The playlist was NOT saved!')

    # TODO
    # Copy playlist to additional folder if specified
    # if settings.copy_playlist and os.path.isdir(settings.copy_to_folder):
    #   pl.save(os.path.join(settings.copy_to_folder, pl_name))

except Exception as er:
  log_last_exception()

if settings.m3u_refresh_mode > 0:
  schedule_next_run(settings.m3u_refresh_interval_mins)

if progress_bar:
  progress_bar.close()
