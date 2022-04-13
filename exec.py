# -*- coding: utf-8 -*-
import os
import sys
from xbmc import executebuiltin
from xbmcgui import DialogProgressBG
from resources.lib.utils import RUNSCRIPT, STREAM_URL, get_m3u_location, get_map_location, pl_path, pl_name, log_info, log_error
from resources.lib.logging import log
from resources.lib.settings import settings 
from resources.lib.utils import addon, resource_path, profile_path, get_last_exception
from resources.lib.notifications import notify_error
from resources.lib.playlist import Playlist
from resources.lib.map import StreamsMap

user_agent    = 'Kodi %s' % addon.getAddonInfo('version')
scheduled_run = len(sys.argv) > 1 and sys.argv[1] == str(True)
mapping_file  = os.path.join( resource_path, 'mapping.json' )
progress_bar  = None

log_info("Addon running on: %s" % user_agent)
if scheduled_run:
  log_info('Automatic playlist generation')
  
### Only if addon is started manually or is in debug mode, display the progress bar 
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
  
  streamsmap = StreamsMap(
    path=get_map_location()
    , log_delegate=log
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

    ### Copy playlist to additional folder if specified
    # if settings.copy_playlist and os.path.isdir(settings.copy_to_folder):
    #   pl.save(os.path.join(settings.copy_to_folder, pl_name))

except Exception as er:
  log_error(get_last_exception())

### Schedule next run
mode = settings.m3u_refresh_mode
if mode > 0:
  interval = settings.m3u_refresh_interval_mins
  log_info('Scheduling next run after %s minutes' % interval)  
  command = "AlarmClock('ScheduledReload', %s, %s, silent)" % (RUNSCRIPT, interval)
  executebuiltin(command)

if progress_bar:
  progress_bar.close()
