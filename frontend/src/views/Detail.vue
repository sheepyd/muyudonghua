<template>
  <div class="detail-view">
    <div class="backdrop" :style="{ backgroundImage: `url(${backdropUrl || ''})` }">
      <div class="backdrop-overlay"></div>
    </div>

    <div class="content-wrapper">
      <div class="header">
        <h1>{{ title }}</h1>
        <button v-if="isMovie" class="play-btn-large" @click="playVideo(id)">
          ▶ 播放电影
        </button>
      </div>

      <div v-if="isSeries" class="episodes-section">
        <h2>剧集列表</h2>
        <div class="episodes-grid">
          <div 
            v-for="ep in episodes" 
            :key="ep.id" 
            class="episode-card"
            @click="playVideo(ep.id)"
          >
            <div class="ep-poster">
              <img :src="ep.poster_url" loading="lazy" />
              <div class="ep-overlay">▶</div>
            </div>
            <div class="ep-info">
              <h4>{{ ep.title }}</h4> <!-- Usually "Episode 1" etc. -->
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const id = route.params.id;
const type = route.query.type;
const title = route.query.title;
const backdropUrl = route.query.backdrop;

const episodes = ref([]);

const isSeries = computed(() => type === 'Series');
const isMovie = computed(() => type === 'Movie');

const fetchEpisodes = async () => {
  if (!isSeries.value) return;
  try {
    const res = await fetch(`/api/videos?seriesId=${id}`);
    const data = await res.json();
    episodes.value = data.items;
  } catch (e) {
    console.error(e);
  }
};

const playVideo = (videoId) => {
  router.push({ name: 'Player', params: { id: videoId } });
};

onMounted(() => {
  fetchEpisodes();
});
</script>

<style scoped>
.detail-view {
  min-height: 100vh;
  position: relative;
  padding-top: 80px; /* Navbar space */
}

.backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 60vh;
  background-size: cover;
  background-position: center;
  z-index: -1;
}

.backdrop-overlay {
  width: 100%;
  height: 100%;
  background: linear-gradient(to bottom, rgba(20,20,20,0.2) 0%, #141414 100%);
}

.content-wrapper {
  padding: 0 4%;
  margin-top: 20vh;
}

.header {
  margin-bottom: 40px;
}

.header h1 {
  font-size: 3rem;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px black;
}

.play-btn-large {
  background-color: #e50914;
  color: white;
  border: none;
  padding: 15px 40px;
  font-size: 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: 0.3s;
}

.play-btn-large:hover {
  background-color: #ff0a16;
}

.episodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.episode-card {
  background: #222;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}

.episode-card:hover {
  transform: scale(1.05);
  background: #333;
}

.ep-poster {
  position: relative;
  aspect-ratio: 16/9;
}

.ep-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ep-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.episode-card:hover .ep-overlay {
  opacity: 1;
}

.ep-info {
  padding: 10px;
}

.ep-info h4 {
  margin: 0;
  font-size: 1rem;
  color: #ddd;
}
</style>