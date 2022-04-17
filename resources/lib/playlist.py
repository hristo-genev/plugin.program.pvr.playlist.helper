# -*- coding: utf8 -*-
import os
import sys
import json
import requests
import urllib.request, urllib.parse, urllib.error
from .m3u_parser import PlaylistParser
from .enums import StreamQuality, PlaylistType
from .map import StreamsMap
  
  
class Playlist:
  
  def __init__(self, **kwargs):

    self.name = kwargs.get('name', 'playlist.m3u')
    self.streams = []
    self.size = 0
    self._cache_file = ".cache"
    self._streams_file = ".streams"
    self.__streams_info_map = kwargs.get('map', StreamsMap())
    self._log_delegate = kwargs.get('log_delegate', None)
    self._progress_delegate = kwargs.get('progress_delegate')
    self.__only_mapped = kwargs.get('include_only_mapped_streams')
    self._user_agent = kwargs.get('user_agent')
    self._map_location = kwargs.get('map_location')
    self._type = kwargs.get('type', PlaylistType.KODIPVR)
    self._temp_folder = kwargs.get('temp_folder')
    if self._temp_folder:
      self._cache_file = os.path.join(self._temp_folder, self._cache_file)
      self._streams_file = os.path.join(self._temp_folder, self._streams_file)
      

  def load(self, resource_path):
    '''
      Loads a given resource. Automatically choses to load from file or from local path
    '''
    if resource_path.startswith('http') or resource_path.startswith('ftp'):
      return self.load_from_url(resource_path)
    return self.load_from_file(resource_path)


  def load_from_file(self, file_path):
    ''' 
    Loads m3u from local storage
    '''
    result = True
    self.__log("load_from_file() started")
    self.__progress(5, "Loading playlist from: %s" % file_path)
    
    self.__parse(file_path)
    self.__serialize()
    self.__log("load_from_file() ended")


  def load_from_url(self, url):
    '''
      Downloads the playlist from HTTP or FTP server
      Caches it on disk 
    '''
    result = True
    self.__log("load_from_url() started")
    self.__progress(5, "Loading playlist from: %s" % url)
    
    try:
      headers = {}
      if self._user_agent:
        headers = {"User-agent": self._user_agent}
        
      self.__log("Downloading resource from: %s " % url)
      response = requests.get(url, headers=headers)
      self.__log("Server status_code: %s " % response.status_code)
      
      if response.status_code >= 200 and response.status_code < 400:
        chunk_size = self.__get_chunk_size__(response)
        #using response.text.splitlines() is way too slow on singleboard devices!!!
        self.__cache(self.__iter_lines__(response, chunk_size))
        self.__parse(self._cache_file)
        self.__serialize()
      else:
        self.__log("Unsupported status code received from server: %s" % response.status_code)
        result = False
        
      self.__log("load_from_url() ended")
      return result
      
    except Exception as ex:
      self.__log("Downloading resource failed! %s" % ex)
      return False
    
  
  def overwrite_values(self, map=None):
    '''
    '''
    if map: 
      self.__streams_info_map = map
      
    for stream in self.streams:
      stream_info_map = self.__streams_info_map.get_stream_info(stream.name)
      if self.__only_mapped and stream_info_map == {}:
        self.__log('Stream %s disabled as per addon settings' % stream.name)
        stream.disabled = True
        continue
      stream.replace_values(stream_info_map)


  def __get_chunk_size__(self, response):
    '''
      Gets the size of the response
    '''
    try:
      size = int(response.headers['Content-length'])
      self.__log("Response size: %s" % size)
      if size > 0: 
        return size/100 
    except: pass
    return 2048
  

  def __iter_lines__(self, response, chunk_size, delimiter=None):
    '''
      Implementation of iter_lines to include a progress bar
    '''
    pending = None
    for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=True):
      if pending is not None:
        chunk = pending + chunk

      if delimiter:
        lines = chunk.split(delimiter)
      else:
        lines = chunk.splitlines()
        
      if lines and lines[-1] and chunk and lines[-1][-1] == chunk[-1]:
        pending = lines.pop()
      else:
        pending = None
        
      for line in lines:
        yield line
        
    if pending is not None:
        yield pending


  def __cache(self, content):
    '''
    Saves the m3u locally and counts the lines 
    Needed for the progress bar
    '''
    self.__log("cache() started!")
    
    self.__log ("Using cache file: %s" %  self._cache_file)
    with open(self._cache_file, 'w', encoding='utf-8') as file:
      for line in content:
        self.size += 1
        file.write("%s\n" % line.rstrip().decode()) #.encode("utf-8"))
        
    self.__log("cache() ended!")
 
 
  def __parse(self, file_path):
    '''
    '''
    with open(file_path, "r", encoding="utf8") as file_content:
      self.__log("__parse() started")
      parser = PlaylistParser(
        size = self.size,
        log_delegate = self.__log,
        progress_delegate = self._progress_delegate,
        progress_max_value = 80
      )
      parser.parse(file_content)
      self.streams = parser.extracted_streams
      self.__log("Parsed %s streams" % (len(self.streams)))
      self.__log("__parse() ended")
      
    
  def __serialize(self):
    '''
    Serializes streams dict into a file so it can be used later
    '''
    self.__log("__serialize() started")
    self.__progress(80, "Serializing streams")
    _streams = {}
    
    for stream in self.streams:
      _streams[stream.name] = stream.url
      
    self.__log("serializing %s streams in %s" % (len(_streams), self._streams_file))
    
    with open(self._streams_file, "w", encoding="utf8") as w:
      w.write(json.dumps(_streams, ensure_ascii=False))
      
    self.__log("__serialize() ended")

    
  def reorder(self, map=None):
    ''' 
    Reorders channels in the playlist
    '''
    self.__log("reorder() started") 
    if map:
      self.__streams_info_map = map
    self.__assign_stream_order_from_map()
    self.streams = sorted(self.streams, key=lambda stream:int(stream.properties['ch-order']))    
    self.__log("reorder() ended")


  def __assign_stream_order_from_map(self):
    '''
    Asigns each stream a 'ch-order' property as per the map
    '''
    percent = 95
    max = 3
    step = round(len(self.streams)/max)    
    self.__progress(percent, "Reordering playlist")
    for i, stream in enumerate(self.streams):
      if i % step == 0: 
        percent += 1
      stream.set_order(self.__streams_info_map.get_stream_order(stream.name, i))


  def add(self, new_m3u_location):
    ''' 
    Adds channels from new playlist to current one
    '''
    self.load(new_m3u_location)


  def has_no_streams(self):
    '''
    '''
    return len(self.streams) == 0


  def __to_string(self, type):
    ''' 
      Outputs the current streams into different formats
    '''
    self.__log("__to_string() started!")
    if not type:
      type = self._type
    self.__progress(98, "Saving playlist. Type: %s" % type.name)
    
    buffer = '#EXTM3U\n'
    percent = 0
    n = len(self.streams)
    # step = round(n/100)
    enabled_streams = 0
    
    for i in range(0, n):
      # if i % step == 0: 
        # percent += 1
      # self.__progress(percent, "1. Saving playlist. Type: %s" % type)
      # Disable streams from disabled groups or streams with offset (only when hide_timeshifted is enabled)
      # if self.streams[i].offset and settings.hide_timeshifted:
      #   self.streams[i].disabled = True
      
      if not self.streams[i].disabled or type == PlaylistType.NAMES or type == PlaylistType.JSON:
        stream_string = self.streams[i].to_string()
        enabled_streams += 1
        if type == PlaylistType.JSON:
          if i < (n-1): stream_string += ","
        buffer += stream_string
    
    # if type == PlaylistType.KODIPVR or type == PlaylistType.PLAIN:
    #   buffer = "%s\n%s" % (self.__START_MARKER__, buffer)
      
    if type == PlaylistType.JSON:
      buffer = "[%s]" % buffer
    
    self.__log("__to_string() returned %s streams" % enabled_streams)
    return buffer
    
   
    
  def save(self, file_path, ouput_type = None):
    '''
    Saves current playlist into a file
    Kwargs:
      path - path to the file where the playlist will be saved. 
        If no path is given and the playlist is loaded from file 
        it will be overwritten. If no path is given and the 
        playlist is loaded from url, it will be saved in the current folder 
      type - the type of playlist
    '''
    
    # If no path is provided overwite current file
    if not file_path:
      raise Exception('No path provided to save the playlist')

    if not ouput_type:
      ouput_type = self._type
      
    try:
      with open(file_path, 'w', encoding="utf8") as file:
        self.__log("Saving playlist type %s in %s " % (self._type, file_path))
        file.write(self.__to_string(self._type))        
      return True
    
    except Exception as er:
      self.__log_exception()
      return False


  def set_static_stream_urls(self, url):
    '''
    Replaces all stream urls with static ones
    That point to our proxy server
    '''
    for stream in self.streams:
      name = urllib.parse.quote(stream.name)
      stream.url = url % (name)
  

  def set_preferred_quality(self, preferred_quality, forced_disable=False):
    '''
    Disables streams that are not of preferred quality, enable all others
    Args:
      preferred_quality: The preffered quality of the channel - UHD, HD, SD or LQ
      forced_disable: Should a channel be disabled if it has no alternative qualities. Defaults to False
        Example:
        If a channel has only one stream and forced_disable is False, the stream will be enabled 
        regardless of its quality. If a channel has more than one streams but none of them matches 
        the preferred_quality, the logic will select the highest available quality.
    '''
    _streams = []
    try:
      self.__log("set_preferred_quality() started")
      i = 0
      percent = 90
      max = 5
      step = round(len(self.channels) / max)
      
      for channel_name, channel in self.channels.items():
        if i % step == 0: 
          percent += 1
        self.__progress(percent, "Selecting %s streams for channel %s" % (preferred_quality.name, channel_name))
        i += 1
        __preferred_quality = preferred_quality
        self.__log("Searching for '%s' stream from channel '%s'" % (__preferred_quality, channel_name))
        
        ### change quality if there is no stream with the preferred_quality
        if not channel.streams.get(__preferred_quality):
          __preferred_quality = StreamQuality.HD if __preferred_quality == StreamQuality.SD else StreamQuality.SD
          self.__log("No %s stream for channel '%s'. Changing quality to %s" % (preferred_quality, channel_name, __preferred_quality))
          
        # disable streams with unpreferred quality
        for quality, stream in channel.streams.items():
        
          if quality == __preferred_quality:
            stream.disabled = False
            self.__log("Preferred %s stream found. Adding '%s'" % (stream.quality, stream.name))            
          else:
            ## if it's a channel with a single stream, add it.
            if len(channel.streams) == 1 and not forced_disable:
              stream.disabled = False
              self.__log("Adding '%s' stream '%s' (single stream, quality setting is ignored)" % (stream.quality, stream.name))      
            else:
              self.__log("Disabling unpreferred '%s' stream %s" % (stream.quality, stream.name))
              stream.disabled = True
          _streams.append(stream)
      
      self.streams = _streams
      
    except Exception as er:
      self.__log_exception()

    self.__log("Filtered %s channels with preferred quality"% len(self.streams) )
    self.__log("set_preferred_quality() ended!")

  def __log(self, msg):
    if self._log_delegate:
      self._log_delegate(msg) 

  def __log_exception(self):
    import traceback
    msg = traceback.format_exc(sys.exc_info())
    self.__log(msg, 4)
    
  
  def __progress(self, percent, msg):
    if self._progress_delegate:
      self._progress_delegate.update(percent, str(msg))