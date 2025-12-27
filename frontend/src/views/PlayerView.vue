<template>
  <div class="cinema-player">
    <div class="player-backdrop" :style="backgroundStyle"></div>

    <div class="player-shell animate-theater-enter">
      <header class="player-header animate-slide-down-fade">
        <button class="back-btn" @click="$router.go(-1)">
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path d="M11.8 4.2L6 10l5.8 5.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
          <span class="back-text">Back to Reel</span>
        </button>

        <div class="header-title">
          <span class="title-text">{{ videoTitle || 'Now Playing' }}</span>
        </div>

        <div class="header-actions">
          <span class="quality-badge">4K</span>
          <button class="icon-btn" type="button" aria-label="Cast">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="4" y="5" width="16" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.5" />
              <path d="M7 20c0-3.3-2.7-6-6-6" fill="none" stroke="currentColor" stroke-width="1.5" />
              <path d="M11 20c0-5.5-4.5-10-10-10" fill="none" stroke="currentColor" stroke-width="1.5" />
            </svg>
          </button>
          <button class="icon-btn" type="button" aria-label="Settings">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.5" />
              <path d="M19 12l2-1-2-1-1-2-2 1-2-1-2 1-2-1-2 1-1 2-2 1 2 1 1 2 2-1 2 1 2-1 2 1 2-1z" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </header>

      <div class="player-body">
        <section class="player-screen animate-fade-in-slow">
          <div class="screen-shadow"></div>
          <div class="player-inner">
            <Player :video-id="id" />
          </div>
        </section>

        <aside v-if="playlistItems.length" class="playlist animate-slide-in-right-delayed">
          <div class="playlist-header">Playlist</div>
          <div class="playlist-list">
            <div
              v-for="ep in playlistItems"
              :key="ep.id"
              class="playlist-item"
              :class="{ active: ep.id == id }"
              @click="switchEpisode(ep.id)"
            >
              <div class="playlist-thumb">
                <img v-if="thumbUrl(ep)" :src="thumbUrl(ep)" :alt="ep.title" loading="lazy" decoding="async" />
                <div v-else class="thumb-fallback"></div>
                <div class="thumb-overlay"></div>
                <div class="thumb-number">{{ formatIndex(ep.display_index ?? ep.index) }}</div>
              </div>

              <div class="playlist-info">
                <div class="playlist-meta">
                  <span v-if="ep.id == id" class="active-dot"></span>
                  <span class="meta-text">EP {{ formatIndex(ep.display_index ?? ep.index) }}</span>
                </div>
                <h4 class="playlist-title">{{ ep.title }}</h4>
              </div>
            </div>
          </div>
        </aside>
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
const seriesId = ref(null);
const seasonId = ref(null);
const parentId = ref(null);
const itemType = ref('');
const videoTitle = ref('');
const episodes = ref([]);

const backgroundStyle = computed(() => {
  const url = posterUrl.value || backdropUrl.value;
  return url
    ? { backgroundImage: `url(${url})` }
    : { backgroundColor: '#09090b' };
});

const playlistItems = computed(() => {
  const sourceItems = episodes.value.length
    ? episodes.value
    : [
        {
          id: id.value,
          title: videoTitle.value || 'Now Playing',
          poster_url: posterUrl.value,
          backdrop_url: backdropUrl.value,
        },
      ];

  const toPositiveInt = (value) => {
    if (value === null || value === undefined) return null;
    const num = Number(value);
    if (!Number.isFinite(num)) return null;
    const intValue = Math.trunc(num);
    return intValue > 0 ? intValue : null;
  };

  const parseEpisodeFromTitle = (title) => {
    if (!title) return null;
    const matchCn = title.match(/第\s*(\d+)\s*(?:集|话|話|回|章|卷|巻)/);
    if (matchCn) return toPositiveInt(matchCn[1]);
    const matchEn = title.match(/(?:EP|E)\s*(\d+)/i);
    if (matchEn) return toPositiveInt(matchEn[1]);
    return null;
  };

  return sourceItems.map((item, index) => {
    const realIndex =
      toPositiveInt(item.index_number) ?? parseEpisodeFromTitle(item.title) ?? index + 1;
    return {
      ...item,
      index: index + 1,
      display_index: realIndex,
    };
  });
});

const formatIndex = (value) => String(value).padStart(2, '0');
const thumbUrl = (item) => item?.poster_url || item?.backdrop_url || '';

const fetchPlayInfo = async (videoId) => {
  const routeSeriesId = route.query.seriesId || route.query.sid;

  const candidatesFromPlay = (data) =>
    [routeSeriesId, data?.series_id, data?.season_id, data?.parent_id, videoId]
      .filter(Boolean)
      .map((value) => String(value));

  const resolveEpisodes = async (candidates) => {
    const uniqueCandidates = [...new Set(candidates)];

    let bestEpisodes = [];
    let bestCount = 0;
    let hasAny = false;

    for (const candidateId of uniqueCandidates) {
      const loaded = await fetchEpisodes(candidateId);
      if (!loaded) continue;

      hasAny = true;
      if (episodes.value.length > bestCount) {
        bestEpisodes = episodes.value;
        bestCount = episodes.value.length;
      }

      if (routeSeriesId && candidateId === String(routeSeriesId)) break;
      if (episodes.value.length > 1) break;
    }

    episodes.value = hasAny ? bestEpisodes : [];
    applyMetaFromEpisodes();
  };

  try {
    const res = await fetch(`/api/play/${videoId}`);
    const data = await res.json();

    backdropUrl.value = data.backdrop_url || '';
    posterUrl.value = data.poster_url || '';
    seriesId.value = data.series_id ?? null;
    seasonId.value = data.season_id ?? null;
    parentId.value = data.parent_id ?? null;
    itemType.value = data.type || '';
    videoTitle.value = data.title || '';

    await resolveEpisodes(candidatesFromPlay(data));
  } catch (error) {
    console.error('Error fetching play info:', error);
    await resolveEpisodes([routeSeriesId, videoId].filter(Boolean).map((value) => String(value)));
  }
};

const fetchEpisodes = async (sid) => {
  try {
    const res = await fetch(`/api/videos?seriesId=${sid}`);
    const data = await res.json();
    episodes.value = data.items || [];
    return episodes.value.length > 0;
  } catch (e) {
    console.error('Error fetching episodes:', e);
    return false;
  }
};

const applyMetaFromEpisodes = () => {
  if (!episodes.value.length) return;
  const current = episodes.value.find((ep) => String(ep.id) === String(id.value));
  if (!current) return;

  if (!videoTitle.value && current.title) videoTitle.value = current.title;
  if (!posterUrl.value && current.poster_url) posterUrl.value = current.poster_url;
  if (!backdropUrl.value && current.backdrop_url) backdropUrl.value = current.backdrop_url;
};

const switchEpisode = (newId) => {
  if (newId === id.value) return;
  router.replace({ name: 'Player', params: { id: newId }, query: route.query });
};

watch(
  () => route.params.id,
  (newId) => {
    id.value = newId;
    fetchPlayInfo(newId);
  }
);

onMounted(() => {
  fetchPlayInfo(id.value);
});
</script>

<style scoped>
.cinema-player {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: #09090b;
  color: #e2e8f0;
  font-family: var(--font-sans);
}

.player-backdrop {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  filter: blur(45px) brightness(0.35);
  opacity: 0.75;
  transform: scale(1.05);
  z-index: 0;
}

.player-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.player-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(9, 9, 11, 0.7);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: rgba(226, 232, 240, 0.6);
  cursor: pointer;
  transition: color 0.3s ease;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.25em;
  text-transform: uppercase;
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.back-btn:hover {
  color: #ffffff;
}

.header-title {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 0;
  text-align: center;
  font-weight: 600;
  color: rgba(226, 232, 240, 0.8);
}

.title-text {
  font-size: 0.95rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quality-badge {
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-family: var(--font-mono);
  color: rgba(226, 232, 240, 0.8);
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: transparent;
  color: rgba(148, 163, 184, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.3s ease, border-color 0.3s ease, transform 0.3s ease;
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

.icon-btn:hover {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.4);
  transform: scale(1.05);
}

.player-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.player-screen {
  flex: 1;
  background: #000;
  position: relative;
  min-width: 0;
}

.screen-shadow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  box-shadow: inset 0 0 80px rgba(0, 0, 0, 0.6);
  z-index: 1;
}

.player-inner {
  position: relative;
  z-index: 0;
  width: 100%;
  height: 100%;
}

.playlist {
  width: 340px;
  flex: 0 0 340px;
  background: rgba(9, 9, 11, 0.92);
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(12px);
}

.playlist-header {
  padding: 22px 24px;
  font-size: 0.65rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  font-weight: 700;
  color: rgba(148, 163, 184, 0.6);
  font-family: var(--font-mono);
}

.playlist-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.playlist-item {
  display: flex;
  gap: 16px;
  cursor: pointer;
  opacity: 0.45;
  transition: opacity 0.3s ease;
}

.playlist-item:hover {
  opacity: 0.8;
}

.playlist-item.active {
  opacity: 1;
}

.playlist-thumb {
  width: 128px;
  aspect-ratio: 16 / 9;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
  background: #111827;
  filter: grayscale(1);
  transition: filter 0.3s ease, opacity 0.3s ease, box-shadow 0.3s ease;
}

.playlist-item.active .playlist-thumb {
  filter: grayscale(0);
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.5);
}

.playlist-thumb img,
.thumb-fallback {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-fallback {
  background: linear-gradient(135deg, #1f2937, #0f172a);
}

.thumb-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.15);
}

.thumb-number {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.12);
  mix-blend-mode: overlay;
}

.playlist-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.playlist-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.meta-text {
  font-size: 0.6rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  font-family: var(--font-mono);
  color: rgba(148, 163, 184, 0.65);
}

.active-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #f59e0b;
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.6);
  animation: pulse 1.6s ease-in-out infinite;
}

.playlist-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(148, 163, 184, 0.75);
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-item.active .meta-text {
  color: rgba(245, 158, 11, 0.9);
}

.playlist-item.active .playlist-title {
  color: #ffffff;
}

.playlist-item:hover .playlist-title {
  color: rgba(226, 232, 240, 0.9);
}

@keyframes theater-enter {
  0% {
    opacity: 0;
    transform: scale(0.98) translateY(10px);
    filter: blur(8px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
    filter: blur(0);
  }
}

@keyframes slide-in-right {
  0% {
    transform: translateX(80px);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slide-down {
  0% {
    transform: translateY(-100%);
    opacity: 0;
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.4);
    opacity: 0.5;
  }
}

.animate-theater-enter {
  animation: theater-enter 1s cubic-bezier(0.22, 1, 0.36, 1);
}

.animate-slide-in-right-delayed {
  animation: slide-in-right 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.2s backwards;
}

.animate-slide-down-fade {
  animation: slide-down 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}

.animate-fade-in-slow {
  animation: fade-in 1.4s ease;
}

@media (max-width: 1024px) {
  .playlist {
    width: 300px;
  }
}

@media (max-width: 900px) {
  .player-body {
    flex-direction: column;
    overflow-y: auto;
  }

  .playlist {
    width: 100%;
    flex: 0 0 auto;
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .player-screen {
    flex: none;
    height: 55vh;
  }
}

@media (max-width: 640px) {
  .player-header {
    padding: 0 16px;
  }

  .header-actions {
    gap: 8px;
  }

  .playlist-header,
  .playlist-list {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
