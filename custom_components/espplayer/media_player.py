"""
Support for ESP Media Player.

Developed by dscao
"""

import requests
import xml.etree.ElementTree as etree
import re
import os
from urllib.parse import unquote
import asyncio
from datetime import timedelta

from homeassistant.components import media_source

import homeassistant.util.dt as dt_util

from homeassistant.helpers.network import get_url


from homeassistant.const import (
    STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING, CONF_NAME
)
    
from homeassistant.components.media_player.browse_media import (
    async_process_play_media_url,
)

from homeassistant.components.media_player import (
    MediaPlayerEntity, PLATFORM_SCHEMA, MediaPlayerEntityFeature,
)


from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import CONF_SENSORSTATE, CONF_ESPPLAY, CONF_ESPSTOP, CONF_ESPVOL, CONF_ESPWAN, DOMAIN
        
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC,
    ATTR_MEDIA_EXTRA,
    MEDIA_TYPE_PLAYLIST,
    REPEAT_MODE_ALL,
    REPEAT_MODE_OFF,
    REPEAT_MODE_ONE,
)
  

SUPPORT_ESP = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.CLEAR_PLAYLIST
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.BROWSE_MEDIA
)


import logging

_LOGGER = logging.getLogger(__name__)

SERVER_TYPE_AV = 0
SERVER_TYPE_CONTROL = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the espplayer Mediaplayer."""
    config = entry.data
    name = config[CONF_NAME]
    unique_id = f"espplayer-{config[CONF_SENSORSTATE]}-{config[CONF_ESPPLAY]}"
    sensorstate = config[CONF_SENSORSTATE]
    espplay = config[CONF_ESPPLAY]
    espstop = config[CONF_ESPSTOP]
    espvol = entry.options.get(CONF_ESPVOL)
    espwan = entry.options.get(CONF_ESPWAN)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.debug("sensorstate：%s, espplay：%s, espvol： %s", sensorstate,  espplay, espvol)

    dev = ESPPlayer(hass, unique_id, name, sensorstate, espplay, espstop, espvol, espwan)
    async_add_entities([dev])
    


class ESPPlayer(MediaPlayerEntity):
    """ESP Device"""
    def __init__(self, hass, unique_id, name, sensorstate, espplay, espstop, espvol, espwan):
        """Initialize the ESP Player."""
        self._hass = hass
        self._unique_id = unique_id
        self._sensorstate = sensorstate
        self._espplay = espplay
        self._espstop = espstop
        self._espvol = espvol
        self._espwan = espwan
        self._name = name
        self._volume = None
        self._muted = None
        self._state = None
        self._media_id = None
        self._mediatitle = None
        
        if self._sensorstate.split('.')[0] == "media_player":
            self.manufacturer = "Mp3toWav_Media_Player"
            self.model = "Esphome Rf-Bridge Speaker" 
        elif self._espplay.split('.')[0] == "esphome":
            self.manufacturer = "Esphome_Media_Player"
            self.model = "Esphome Rf-Bridge Speaker"                   
        elif self._espplay.split('/')[1] == "mrdiynotifier":
            self.manufacturer = "Esp8266mqttPlayer"
            self.model = "DIY Wifi Audio Notifier for ESP8266"
            self._state = STATE_OFF
        
        
    async def async_update(self) -> None:
        """Retrieve the latest data."""
        respState = self.get_entitystate(self._sensorstate)
        _LOGGER.debug ("entity：{}, respState:{}".format(self._sensorstate,respState))
        if respState:
            if respState.state == 'idle' or respState.state == 'on':
                self._state = STATE_IDLE
                self._volume = respState.attributes["volume_level"]
                self._muted = respState.attributes["is_volume_muted"]
            elif respState.state == 'playing':
                self._state = STATE_PLAYING
                self._volume = respState.attributes["volume_level"]
                self._muted = respState.attributes["is_volume_muted"]
            else:
                self._state = STATE_OFF            
        return True
        
    
    

    def get_entitystate(self,entityid):
        currentState=None
        entity = self.hass.states.get(entityid)
        if entity is None:
            _LOGGER.warning("Unable to find entity %s", entityid)
            self.entityFound = False
        else:
            self.entityFound = True
            currentState = entity
        return currentState
        
    
    async def async_audio2wav(self,audio_name: str):
        """
        任意音频格式转换为wav格式，需要安装ffmpeeg
        """
        input_path = "tts/"+audio_name
        output_name = audio_name.split('.')[0]+'.wav'
        output_path = "www/wav/"+output_name
        await self.wait_file(input_path)
        if os.path.isfile(input_path):
            os.system("ffmpeg -i "+ input_path+ " -n -acodec pcm_s16le -ac 1 -ar 16000 " +output_path )
            _LOGGER.debug("real media： %s", output_name)
        return output_name
        
    async def wait_file(self,input_path):
        """Scan for MediaPlayer."""
        i = 0
        while(i < 10):
            i = i+ 1
            if os.path.isfile(input_path):
                return
            await asyncio.sleep(1)
        
    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Implement the websocket media browsing helper."""
        if self._sensorstate.split('.')[0] == "media_player":
            mediatype = "audio/wav"
        elif self._espplay.split('/')[1] == "mrdiynotifier":
            mediatype = "audio/mpeg"
        else:
            mediatype = "audio/"
            
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
            content_filter=lambda item: item.media_content_type.startswith(mediatype),
        )

    async def async_play_media(self, media_type: str, media_id: str, **kwargs):
        didl_metadata: str | None = None
        title: str = ""
        """Play a piece of media."""
        if media_source.is_media_source_id(media_id):
            sourced_media = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
            media_type = sourced_media.mime_type
            media_id = sourced_media.url
            
            if sourced_metadata := getattr(sourced_media, "didl_metadata", None):
                didl_metadata = didl_lite.to_xml_string(sourced_metadata).decode(
                    "utf-8"
                )
                title = sourced_metadata.title

        # If media ID is a relative URL, we serve it from HA.
        media_id = async_process_play_media_url(self.hass, media_id)

        extra: dict[str, Any] = kwargs.get(ATTR_MEDIA_EXTRA) or {}
        metadata: dict[str, Any] = extra.get("metadata") or {}
        
        
        
        self._path = os.path.dirname(media_id)
        mediatitle = os.path.basename(media_id)
        self._mediatitle = unquote(mediatitle, encoding="UTF-8")      
         
        _LOGGER.debug("source media_id： %s", media_id)
        
        if self._sensorstate.split('.')[0] == "media_player":
            _LOGGER.debug("media_id is %s ,player: %s", media_id, self._espplay)
            if self._espwan is not None and self._espwan != "auto":
                instance_url = get_url(self.hass)
                media_id = media_id.replace(instance_url,self._espwan)
            if self._mediatitle.split('.')[1] == "mp3":
                wavfile = await self.async_audio2wav(self._mediatitle) 
                media_id = media_id.replace(".mp3",".wav")
                media_id = media_id.replace("/api/tts_proxy/","/local/wav/")
            
            await self.hass.services.async_call("media_player",
                    "play_media",
                    {"media_content_id": media_id, "media_content_type":"music", "entity_id": self._sensorstate},
                    blocking=True,)
        elif self._espplay.split('.')[0] == "esphome":
            _LOGGER.debug("media_id is %s ,player: %s", media_id, self._espplay)
            if self._espwan is not None and self._espwan != "auto":
                instance_url = get_url(self.hass)
                media_id = media_id.replace(instance_url,self._espwan)
            if self._mediatitle.split('.')[1] == "mp3":
                wavfile = await self.async_audio2wav(self._mediatitle) 
                media_id = media_id.replace(".mp3",".wav")
                media_id = media_id.replace("/api/tts_proxy/","/local/wav/")
            
            await self.hass.services.async_call(self._espplay.split('.')[0],
                    self._espplay.split('.')[1],
                    {"url": media_id},
                    blocking=True,)   
        elif self._espplay.split('/')[1] == "mrdiynotifier":
            media_id = media_id.replace(".wav",".mp3")
            if self._espwan is not None and self._espwan != "auto":
                instance_url = get_url(self.hass)
                media_id = media_id = media_id.replace(instance_url,self._espwan)
            _LOGGER.debug("media_id is %s ,player: %s", media_id, self._espplay)
            await self.hass.services.async_call("mqtt",
                    "publish",
                    {"topic": self._espplay,"payload": media_id},
                    blocking=True,)
                    
        self._media_id = media_id
        _LOGGER.debug("play media_id： %s", self._media_id)
            
                 

    @property
    def name(self):
        """Return the name of the device."""
        return self._name
        
    @property    
    def unique_id(self):
        """Return a unique_id for this entity."""
        return "mediaplayer_" + self._unique_id
        
    @property
    def available(self):
        """Return True if entity is available."""
        return self._state != None

    @property
    def state(self):
        """Return the state of the device."""
        return self._state
        
    @property
    def device_class(self):
        """Return the state of the device."""
        return "speaker"

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self._name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "sw_version": "1.0",
        }
        
    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        supported_features = 0

        supported_features |= MediaPlayerEntityFeature.PLAY
        supported_features |= MediaPlayerEntityFeature.STOP        
        
        
        if (self._espvol != "" and self._espvol !=None) or (self._volume !=None):
            supported_features |= MediaPlayerEntityFeature.VOLUME_SET
            supported_features |= MediaPlayerEntityFeature.VOLUME_STEP
        if self._muted !=None:
            supported_features |= MediaPlayerEntityFeature.VOLUME_MUTE

        supported_features |= (
            MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.BROWSE_MEDIA
        )
     

        return supported_features    

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted
        
        
    @property
    def media_content_id(self):
        """Content ID of current playing media."""
        return self._media_id
        
    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC
        
    @property
    def media_title(self):
        """Title of current playing media."""
        return self._mediatitle


    def media_play(self):
        """Send play commmand."""
        pass

    def media_pause(self):
        """Send pause command."""
        pass
        
    # @property
    # def volume_level(self) -> float | None:
        # """Volume level of the media player (0..1)."""
        # if not self._device or not self._device.has_volume_level:
            # return None
        # return self._device.volume_level

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        if self._sensorstate.split('.')[0] == "media_player":         
            await self.hass.services.async_call("media_player",
                    "volume_set",
                    {"volume_level": volume, "entity_id": self._sensorstate},
                    blocking=True,) 
        elif self._espplay.split('.')[0] == "esphome":
            assert self._espvol is not None and self._espvol != "None"
            await self.hass.services.async_call(self._espplay.split('.')[0],
                    self._espplay.split('.')[1],
                    {"set_volume": volume},
                    blocking=True,)   
        elif self._espplay.split('/')[1] == "mrdiynotifier":
            assert self._espvol is not None and self._espvol != "None"
            await self.hass.services.async_call("mqtt",
                    "publish",
                    {"topic": self._espvol,"payload":volume},
                    blocking=True,)
        
    async def async_mute_volume(self, mute: bool):
        """Send mute_volume command."""
        if self._sensorstate.split('.')[0] == "media_player":
            await self.hass.services.async_call("media_player",
                    "volume_mute",
                    {"is_volume_muted": mute,"entity_id": self._sensorstate},
                    blocking=True,)
        

    async def async_media_stop(self):
        """Send stop command."""
        if self._sensorstate.split('.')[0] == "media_player":
            assert self._espstop is not None
            await self.hass.services.async_call("media_player",
                    "media_stop",
                    {"entity_id": self._sensorstate},
                    blocking=True,)
        elif self._espplay.split('.')[0] == "esphome":
            assert self._espstop is not None
            await self.hass.services.async_call(self._espstop.split('.')[0],
                    self._espstop.split('.')[1],
                    {},
                    blocking=True,) 
        elif self._espplay.split('/')[1] == "mrdiynotifier":            
            assert self._espstop is not None
            await self.hass.services.async_call("mqtt",
                    "publish",
                    {"topic": self._espstop},
                    blocking=True,)
            # /mrdiynotifier/stop 有时无效，用空白发言来停止之前的音频。
            await self.hass.services.async_call("mqtt",
                    "publish",
                    {"topic": "/mrdiynotifier/say","payload":" "},
                    blocking=True,)

    def play_media(self, media_id: str, **kwargs):
        """Send play_media commmand."""
        # Replace this with calling your media player play media function.
        pass
          
