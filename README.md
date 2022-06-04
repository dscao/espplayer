# EspPlayer

此版本请尽量使用homeassistant 2022以后的版本，之前旧版本未测试

1、为 rf-bridge 盒子提供支持的TTS播放器

https://github.com/ryanh7/esphome-custom-components/tree/dev 

通过上面esphome组件 esp8266 通过http流播放wav 等方法生成的esphome.rf_bridge_play_audio类似服务可播放音频，可用此集成。



2、为 提供支持的TTS播放器
https://www.instructables.com/MQTT-Audio-Notifier-for-ESP8266-Play-MP3-TTS-RTTL/ 
通过mqtt播放音频，可用此集成。
先通过mqtt集成生成播放状态实体，用于播放器。
ha 2022.6.0之后版本在config/configuration.yaml中加入：
mqtt:
  sensor:
    - name: esp8266mqttplayerstate
      unique_id: esp8266mqttplayerstate
      expire_after: 600
      state_topic: "/mrdiynotifier/status" 
老版本加入：      
sensor:
  - platform: mqtt
    name: esp8266mqttplayerstate
    unique_id: esp8266mqttplayerstate
    expire_after: 600
    state_topic: "/mrdiynotifier/status" 
    
重启ha后状态显示正常再添加此集成。


