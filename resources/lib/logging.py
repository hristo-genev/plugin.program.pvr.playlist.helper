import xbmc
from .utils import *

def log(msg, level=xbmc.LOGDEBUG):
  try:
    if settings.debug and level == xbmc.LOGDEBUG:
      level = xbmc.LOGINFO
    xbmc.log("%s v%s | %s" % (id, addon_version, str(msg)), level)
  except:
    pass


def log_info(msg):
  log(msg, xbmc.LOGINFO)


def log_error(msg):
  log(msg, xbmc.LOGERROR)


def log_last_exception():
  log_error(get_last_exception())