# -*- coding: utf-8 -*-
from xbmcgui import DialogProgressBG
from resources.lib.utils import *
from resources.lib.settings import settings 
from resources.lib.utils import addon, profile_path
from resources.lib.notifications import notify_error

# import web_pdb; web_pdb.set_trace()

progress_bar = None
if is_manual_run() or settings.debug:
  progress_bar = DialogProgressBG()
  progress_bar.create(heading=addon_name)

try:
  playlist = PlaylistFactory.create(
    progress_delegate=progress_bar
  )
  playlist.load(get_m3u_location())

  if settings.concat_second_playlist:
    playlist2 = PlaylistFactory.create(
      progress_delegate=progress_bar
    )
    playlist2.load(get_m3u2_location())
    playlist.add_streams(playlist2.streams)

  playlist.overwrite_values(streamsmap, remove_unmapped_streams=settings.only_streams_from_map)

  if playlist.has_no_streams():
    notify_error('The playlist has NO channels!')
  
  else:
    if settings.reorder_playlist:
      playlist.reorder()

    if not playlist.save(pl_path):
      notify_error('The playlist was NOT saved!')

    if settings.copy_playlist and os.path.isdir(settings.copy_to_folder):
      playlist.save(os.path.join(settings.copy_to_folder, pl_name))

except Exception as er:
  log_last_exception()

if settings.m3u_refresh_mode > 0:
  schedule_next_run(settings.m3u_refresh_interval_mins)

if progress_bar:
  progress_bar.close()
