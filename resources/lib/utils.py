# -*- coding: utf-8 -*-
import os
import sys
import json
import xbmc
import time
from .settings import settings 
from .addon import *
from .logging import log_info, log_error, log_last_exception

pl_cache      = os.path.join(profile_path, ".cache")
pl_streams    = os.path.join(profile_path, ".streams")
pl_name       = 'playlist.m3u'
pl_path       = os.path.join(profile_path, pl_name)

RUNSCRIPT     = 'RunScript(%s, True)' % id
STREAM_URL    = 'http://%s:%s/stream/' % (settings.stream_ip, settings.port) + '%s'
ALL           = "Всички"

if settings.firstrun:
  addon.openSettings()
  settings.firstrun = False
  
  
def show_progress(progress_bar, percent, msg):
  if progress_bar:
    progress_bar.update(percent, str(msg))
    log_info(msg)
    
    
def get_user_agent():
  user_agent = 'Kodi %s, %s:%s' % (get_kodi_build(), id, addon_version)
  log_info("Addon running on: %s" % user_agent)
  return user_agent


def get_kodi_build():
  try:
    return xbmc.getInfoLabel("System.BuildVersion")
  except Exception:
    return "Unknown"
  
  
def is_scheduled_run():
  scheduled_run = len(sys.argv) > 1 and sys.argv[1] == str(True)  
  if scheduled_run:
    log_info('Automatic playlist generation')
  return scheduled_run
  
def get_m3u_location():
  '''
  '''
  m3u_location = settings.m3u_path if settings.m3u_path_type == 0 else settings.m3u_url
  return m3u_location
  

def get_map_location():
  '''
  '''
  map_location = settings.map_path if settings.map_path_type == 0 else settings.map_url
  return map_location


def get_stream_url(name):
  """
  Reads stream list from cache and returns url of the selected stream name
  """
  try:
    streams = json.load(open(pl_streams, encoding='utf-8'))
    log_info("Deserialized %s streams from file %s" % (len(streams), pl_streams))
    return streams.get(name)
  except Exception as er:
    log_last_exception()
    return None


def schedule_next_run(interval):
  log_info('Scheduling next run after %s minutes' % interval)  
  command = "AlarmClock('ScheduledReload', %s, %s, silent)" % (RUNSCRIPT, interval)
  xbmc.executebuiltin(command)


def __update__(action, location, crash=None):
  try:
    lu = settings.last_update
    day = time.strftime("%d")
    if lu != day:
      settings.last_update = day
      from ga import ga
      p = {}
      p['an'] = addon_name
      p['av'] = addon_version
      p['ec'] = 'Addon actions'
      p['ea'] = action
      p['ev'] = '1'
      p['ul'] = xbmc.getLanguage()
      p['cd'] = location
      ga('UA-79422131-9').update(p, crash)
  except Exception as er:
    log_error(er)
  
__update__('operation', 'start')