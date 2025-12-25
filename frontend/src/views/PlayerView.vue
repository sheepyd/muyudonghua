<template>
  <div class="player-view">
    <!-- 背景层 -->
    <div class="background-layer" :style="backgroundStyle"></div>

    <div class="content-container">
      <!-- 顶部导航 -->
      <div class="top-bar">
        <button class="back-btn" @click="$router.go(-1)">
          <span class="icon">←</span> 返回
        </button>
        <div class="title-area">
          <img v-if="logoUrl" :src="logoUrl" class="video-logo" alt="Logo" />
          <h2 v-else class="video-title">{{ videoTitle }}</h2>
        </div>
      </div>

      <!-- 主要内容区域：左侧播放器，右侧选集 -->
      <div class="main-content">
        <div class="player-section">
          <div class="player-wrapper">
             <Player :video-id="id" />
          </div>
        </div>

        <!-- 选集侧边栏 (仅当有选集时显示) -->
        <div v-if="episodes.length > 0" class="sidebar">
          <div class="sidebar-header">
            <h3>选集</h3>
            <span class="episode-count">{{ episodes.length }} 集</span>
          </div>
          <div class="episode-list">
            <div 
              v-for="ep in episodes" 
              :key="ep.id" 
              class="episode-item"
              :class="{ active: ep.id == id }"
              @click="switchEpisode(ep.id)"
            >
              <div class="ep-index">{{ ep.index }}</div>
              <div class="ep-info">
                <div class="ep-title">{{ ep.title }}</div>
              </div>
              <div v-if="ep.id == id" class="playing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Player from '../components/player.vue';

const route = useRoute();
const router = useRouter();
const id = ref(route.params.id);

const backdropUrl = ref('');
const posterUrl = ref('');
const logoUrl = ref('');
const seriesId = ref(null);
const videoTitle = ref('');
const episodes = ref([]);

const backgroundStyle = computed(() => {
  // 优先使用 poster_url，如果没有再尝试 backdrop_url
  const url = posterUrl.value || backdropUrl.value;
  return url 
    ? { backgroundImage: `url(${url})` }
    : { backgroundColor: '#141414' };
});

// 获取当前播放视频的信息（背景、SeriesId等）
const fetchPlayInfo = async (videoId) => {
  try {
    const res = await fetch(`/api/play/${videoId}`);
    const data = await res.json();
    backdropUrl.value = data.backdrop_url || '';
    posterUrl.value = data.poster_url || '';
    logoUrl.value = data.logo_url || '';
    seriesId.value = data.series_id;
    videoTitle.value = data.title;
    
    // Debug logging
    console.log("Play Info Loaded:", {
      id: videoId,
      poster: posterUrl.value,
      backdrop: backdropUrl.value
    });
    
    // 如果有 SeriesId，获取选集列表
    if (seriesId.value) {
      fetchEpisodes(seriesId.value);
    } else {
      episodes.value = []; // 清空选集
    }
  } catch (e) {
    console.error("Error fetching play info:", e);
  }
};

const fetchEpisodes = async (sid) => {
  try {
    const res = await fetch(`/api/videos?seriesId=${sid}`);
    const data = await res.json();
    // 简单处理一下标题，假设标题是 "Episode 1" 这种，也可以加个 index 字段
    episodes.value = data.items.map((item, index) => ({
      ...item,
      index: index + 1 // 简单的序号
    }));
  } catch (e) {
    console.error("Error fetching episodes:", e);
  }
};

const switchEpisode = (newId) => {
  if (newId === id.value) return;
  router.replace({ name: 'Player', params: { id: newId } });
};

// 监听路由参数变化（点击选集切换时）
watch(() => route.params.id, (newId) => {
  id.value = newId;
  fetchPlayInfo(newId);
});

onMounted(() => {
  fetchPlayInfo(id.value);
});
</script>

<style scoped>
.player-view {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: #0a0a0a;
  color: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.background-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  filter: blur(40px) brightness(0.4);
  z-index: 0;
  transform: scale(1.1);
  opacity: 0.8;
}

.content-container {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.top-bar {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 40px;
  background: rgba(25, 26, 30, 0.6);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.back-btn {
  background: none;
  border: none;
  color: #b8b8b8;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  margin-right: 30px;
  transition: color 0.2s;
  font-weight: bold;
}

.back-btn:hover {
  color: #f76cc6;
}

.title-area {
  display: flex;
  align-items: center;
  height: 50px;
}

.video-logo {
  height: 100%;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
}

.video-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #f5f5f5;
  margin: 0;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 30px;
  gap: 30px;
}

/* 左侧播放器区域 */
.player-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-width: 0;
}

.player-wrapper {
  width: 100%;
  max-width: 1400px;
  aspect-ratio: 16 / 9;
  background: #000;
  box-shadow: 0 20px 50px rgba(133, 62, 255, 0.15), 0 0 60px rgba(247, 108, 198, 0.1);
  border-radius: 12px;
  overflow: hidden;
  border: none;
}

/* 右侧选集侧边栏 */
.sidebar {
  width: 350px;
  background: rgba(25, 26, 30, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  border: none;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.sidebar-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  background: rgba(255, 255, 255, 0.03);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #f5f5f5;
}

.episode-count {
  font-size: 0.85rem;
  color: #a78bfa;
  background: rgba(133, 62, 255, 0.15);
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: bold;
}

.episode-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

/* Scrollbar override for this specific container */
.episode-list::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #853eff, #f76cc6);
}

.episode-item {
  display: flex;
  align-items: center;
  padding: 15px 12px;
  margin-bottom: 5px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-bottom: 1px solid transparent;
}

.episode-item:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(133, 62, 255, 0.06));
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.episode-item.active {
  background: rgba(133, 62, 255, 0.2);
  color: #f9a8d4;
  box-shadow: inset 0 0 10px rgba(133, 62, 255, 0.1);
}

.ep-index {
  font-size: 1rem;
  color: #b8b8b8;
  width: 35px;
  text-align: center;
  font-weight: bold;
}

.episode-item.active .ep-index {
  color: #f9a8d4;
}

.ep-info {
  flex: 1;
  margin-left: 10px;
  overflow: hidden;
}

.ep-title {
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

/* 播放中跳动动画 */
.playing-indicator {
  display: flex;
  gap: 2px;
  align-items: flex-end;
  height: 12px;
  margin-left: 10px;
}

.playing-indicator span {
  width: 3px;
  background: #f76cc6;
  animation: bounce 1s infinite ease-in-out;
}

.playing-indicator span:nth-child(1) { animation-delay: 0s; height: 6px; }
.playing-indicator span:nth-child(2) { animation-delay: 0.2s; height: 12px; }
.playing-indicator span:nth-child(3) { animation-delay: 0.4s; height: 8px; }

@keyframes bounce {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1); }
}

@media (max-width: 1000px) {
  .main-content {
    flex-direction: column;
    padding: 15px;
    gap: 20px;
  }
  
  .sidebar {
    width: 100%;
    height: 300px;
    flex: none;
  }
}
</style>