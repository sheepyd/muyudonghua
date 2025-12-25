<template>
  <div class="player-wrapper">
    <div ref="artRef" class="player-box"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";
import Artplayer from "artplayer";

const props = defineProps({
  videoId: {
    type: [String, Number],
    required: true
  }
});

const artRef = ref(null);
let art = null;

const initPlayer = async (id) => {
  if (art) {
    art.destroy(false);
    art = null;
  }
  
  if (!id) return;

  try {
    const res = await fetch(`/api/play/${id}`);
    const data = await res.json();
    
    if (data.url) {
       art = new Artplayer({
        container: artRef.value,
        url: data.url,
        volume: 0.5,
        isLive: false,
        muted: false,
        autoplay: true,
        autoSize: true,
        fullscreen: false,
        theme: '#e50914',
        
        // --- Enhanced Options from Example ---
        pip: true,
        autoMini: true,
        screenshot: true,
        setting: true,
        loop: true,
        flip: true,
        playbackRate: true,
        aspectRatio: true,
        fullscreenWeb: true,
        subtitleOffset: true,
        miniProgressBar: true,
        mutex: true,
        backdrop: true,
        playsInline: true,
        autoPlayback: true,
        airplay: true,
        lang: navigator.language.toLowerCase(),
        moreVideoAttr: {
          crossOrigin: 'anonymous',
        },
        
        // UI Customizations (Referenced from example)
        settings: [
          {
            html: 'Switcher',
            tooltip: 'OFF',
            switch: false,
            onSwitch(item) {
              item.tooltip = item.switch ? 'OFF' : 'ON'
              return !item.switch
            },
          },
          {
            html: 'Color Balance',
            tooltip: '5x',
            range: [5, 1, 10, 0.1],
            onRange(item) {
              return `${item.range[0]}x`
            },
          },
        ],
        controls: [
          {
            position: 'right',
            html: 'Control',
            index: 1,
            tooltip: 'Control Tooltip',
            style: {
              marginRight: '20px',
            },
            click() {
              console.info('You clicked on the custom control')
            },
          },
        ],
      });
    }
  } catch (e) {
    console.error("Error fetching play url:", e);
  }
};

onMounted(() => {
  initPlayer(props.videoId);
});

watch(() => props.videoId, (newId) => {
  initPlayer(newId);
});

onUnmounted(() => {
  if (art && art.destroy) {
    art.destroy(false);
  }
});
</script>

<style scoped>
.player-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.player-box {
  width: 100%;
  height: 100%;
}
</style>