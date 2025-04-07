# EspPlayer

2025版本请使用homeassistant 2025.4 以后的版本

1、为 rf-bridge 盒子提供支持的TTS播放器

https://github.com/ryanh7/esphome-custom-components

通过上面esphome组件 esp8266 通过http流播放wav 等方法生成的esphome.rf_bridge_play_audio类似服务可播放音频，可用此集成。

因为盒子只能播放wav格式, 用了ffmpeg转码，需要在config/www目录下创建 wav目录，即：/config/www/wav/ 存在。

新版esphome会直接生成一下media_player实体，功能都齐全，但一般的TTS是MP3格式，无法播放，需要转成wav格式。

此集成生成一个新的media_player，状态传感器栏设置成原media_player的entity_id,即可通过新的实体在盒子中TTS.

2、为ESP8266-Play-MP3-TTS提供支持的TTS播放器

https://www.instructables.com/MQTT-Audio-Notifier-for-ESP8266-Play-MP3-TTS-RTTL/ 

通过mqtt播放音频，可用此集成。

先通过mqtt集成生成播放状态实体，用于播放器。

ha 2022.6.0之后版本在config/configuration.yaml中加入：

mqtt: \
  sensor: \
    - name: esp8266mqttplayerstate \
      unique_id: esp8266mqttplayerstate \
      expire_after: 600 \
      state_topic: "/mrdiynotifier/status"       
      
老版本加入：  

sensor: \
  - platform: mqtt \
    name: esp8266mqttplayerstate \
    unique_id: esp8266mqttplayerstate \
    expire_after: 600 \
    state_topic: "/mrdiynotifier/status"  \
    
重启ha后状态显示正常再添加此集成。


###示例1：

![1](https://user-images.githubusercontent.com/16587914/172015141-623a45e0-a98d-46a1-8ff4-2da8cc2cbe25.jpg)

![2](https://user-images.githubusercontent.com/16587914/172015151-3a46df46-5340-4221-89da-0c74c1232823.jpg)


![3](https://user-images.githubusercontent.com/16587914/172015153-54932b61-4c0e-4d4e-87fa-180dff378269.jpg)


![4](https://user-images.githubusercontent.com/16587914/172015163-324827e2-b994-464a-b2ce-a01dace2afd4.jpg)


###示例2：

![5](https://user-images.githubusercontent.com/16587914/172015204-c05889f2-e131-4042-ab77-f8c0fa0fa99d.jpg)

![6](https://user-images.githubusercontent.com/16587914/172015212-a251d3c3-2690-4a47-8fd6-bc7efcd55da2.jpg)

![7](https://user-images.githubusercontent.com/16587914/172015215-23f100be-5dc9-44a8-a6c3-01dde81cb27c.jpg)

![9](https://user-images.githubusercontent.com/16587914/172015378-cf5d5d32-d13f-4bc0-b2f4-51e71f3c8189.jpg)

![10](https://user-images.githubusercontent.com/16587914/172663047-303c55eb-6d28-4da6-bdaf-e3ad28507ac9.jpg)
设置音量控制 及 支持外网地址播放tts文件（利用公网ip或frp等反向代理使其它网络中的esp8266设备发声）
