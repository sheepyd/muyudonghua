<template>
  <div class="film-home">
    <div class="ambient-backdrop" :style="activeBackdrop ? { backgroundImage: `url(${activeBackdrop})` } : {}"></div>
    <div class="ambient-color" :style="{ backgroundColor: activeAccent }"></div>
    <div class="ambient-gradient"></div>
    <div class="ambient-noise"></div>

    <header class="film-header" @click.stop>
      <div class="brand">
        <svg class="brand-icon" viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="4" width="18" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1.5" />
          <circle cx="8" cy="9" r="1.2" fill="currentColor" />
          <circle cx="8" cy="15" r="1.2" fill="currentColor" />
          <circle cx="16" cy="9" r="1.2" fill="currentColor" />
          <circle cx="16" cy="15" r="1.2" fill="currentColor" />
        </svg>
        <span class="brand-text">YDYD<span>.ME</span></span>
      </div>

      <div class="header-search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="6" fill="none" stroke="currentColor" stroke-width="1.5" />
          <path d="M16 16l4 4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        </svg>
        <input type="text" placeholder="SEARCH FILMS..." />
      </div>

      <div class="header-actions">
        <button class="header-icon-btn" type="button" aria-label="Maximize">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 3H3v4M17 3h4v4M7 21H3v-4M21 21h-4v-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    </header>

    <main class="film-stage" @click="clearSelection">
      <div v-if="activeTitle" class="film-number" :class="{ visible: hasSelected }">
        {{ activeNumber }}
      </div>

      <div ref="scrollContainer" class="film-gallery">
        <div
          v-for="(item, index) in items"
          :key="item.id"
          class="film-snap"
          :class="{ active: hasSelected && activeIndex === index }"
          :ref="(el) => setItemRef(el, index)"
        >
          <div
            class="film-item"
            :class="{ active: hasSelected && activeIndex === index }"
            @click.stop="selectItem(index)"
          >
            <div class="film-reel">
              <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <defs>
                  <linearGradient id="metalGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#d4d4d8" />
                    <stop offset="25%" stop-color="#a1a1aa" />
                    <stop offset="50%" stop-color="#e4e4e7" />
                    <stop offset="75%" stop-color="#71717a" />
                    <stop offset="100%" stop-color="#52525b" />
                  </linearGradient>
                  <radialGradient id="filmDark" cx="50%" cy="50%" r="50%">
                    <stop offset="80%" stop-color="#09090b" />
                    <stop offset="100%" stop-color="#18181b" />
                  </radialGradient>
                </defs>
                <circle cx="100" cy="100" r="96" fill="url(#filmDark)" stroke="#27272a" stroke-width="2" />
                <path
                  d="M100,100 m-95,0 a95,95 0 1,0 190,0 a95,95 0 1,0 -190,0 a95,95 0 1,0 -190,0 M100,100 m-25,0 a25,25 0 1,1 50,0 a25,25 0 1,1 -50,0 M100,20 L100,5 A95,95 0 0,1 182,52 L169,60 A80,80 0 0,0 100,20 M175,122 L188,129 A95,95 0 0,1 100,195 L100,180 A80,80 0 0,0 175,122 M25,122 A80,80 0 0,0 100,180 L100,195 A95,95 0 0,1 12,129 L25,122 M31,60 L18,52 A95,95 0 0,1 100,5 L100,20 A80,80 0 0,0 31,60"
                  fill="url(#metalGrad)"
                  fill-rule="evenodd"
                />
                <circle cx="100" cy="100" r="18" fill="#52525b" stroke="#3f3f46" stroke-width="1" />
                <circle cx="100" cy="100" r="6" fill="#18181b" />
                <g fill="#d4d4d8">
                  <circle cx="100" cy="88" r="1.5" />
                  <circle cx="100" cy="112" r="1.5" />
                  <circle cx="88" cy="100" r="1.5" />
                  <circle cx="112" cy="100" r="1.5" />
                </g>
                <circle cx="100" cy="100" r="95" fill="none" stroke="white" stroke-width="1" opacity="0.1" />
              </svg>
            </div>

            <div class="film-cover">
              <div class="film-cover__media">
                <img v-if="coverUrl(item)" :src="coverUrl(item)" :alt="item.title" loading="lazy" decoding="async" />
                <div v-else class="film-cover__fallback"></div>
                <div class="film-cover__grain"></div>
                <div class="film-cover__shade"></div>
              </div>
              <div class="film-cover__top">
                <div class="film-iso">
                  <span class="film-iso__value">{{ item.year || '----' }}</span>
                  <span class="film-iso__label">Premiere</span>
                </div>
              </div>
              <div class="film-cover__title">
                <div class="film-divider"></div>
                <h3 class="film-series">{{ headline(item) }}</h3>
              </div>
              <div class="film-cover__bottom">
                <div class="film-bottom__text">
                  <span class="film-title">{{ item.title }}</span>
                  <span class="film-type">{{ formatType(item.type) }}</span>
                </div>
                <svg class="aperture-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.4" />
                  <path
                    d="M12 4l4 7-4 7-4-7 4-7z"
                    fill="currentColor"
                    opacity="0.35"
                  />
                </svg>
              </div>
              <div class="film-cover__gloss"></div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="film-loading">Loading...</div>

      <div class="film-info" :class="{ visible: hasSelected }" @click.stop>
        <div class="film-status">
          <span class="status-dot" :class="{ live: hasSelected }"></span>
          <span class="status-text">{{ hasSelected ? 'Selected' : 'Standby' }}</span>
        </div>
        <h1 class="film-title-large">{{ activeTitle }}</h1>
        <div class="film-meta">
          <span class="film-badge">4K</span>
          <span>{{ activeYear }}</span>
          <span>|</span>
          <span>{{ activeType }}</span>
        </div>
      </div>

      <div class="film-controls" :class="{ visible: hasSelected }" @click.stop>
        <button class="play-button" @click="requestPlay" :disabled="!activeTitle">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <polygon points="7,5 19,12 7,19" fill="currentColor" />
          </svg>
        </button>
        <div class="control-row">
          <button class="control-btn" @click="prevItem" :disabled="activeIndex === 0">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="5" y="5" width="2.5" height="14" fill="currentColor" />
              <polygon points="19,5 9,12 19,19" fill="currentColor" />
            </svg>
          </button>
          <button class="control-btn" @click="nextItem" :disabled="activeIndex >= items.length - 1">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="16.5" y="5" width="2.5" height="14" fill="currentColor" />
              <polygon points="5,5 15,12 5,19" fill="currentColor" />
            </svg>
          </button>
        </div>
      </div>
    </main>

    <div class="film-progress" :class="{ visible: hasSelected }">
      <div class="film-progress__bar" :style="{ width: `${progress}%` }"></div>
    </div>

    <div v-if="authOpen" class="auth-overlay" @click.self="closeAuth">
      <div class="auth-modal" role="dialog" aria-modal="true" @click.stop>
        <div class="auth-brand">
          <svg class="auth-brand__icon" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="3" y="4" width="18" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1.5" />
            <circle cx="8" cy="9" r="1.2" fill="currentColor" />
            <circle cx="8" cy="15" r="1.2" fill="currentColor" />
            <circle cx="16" cy="9" r="1.2" fill="currentColor" />
            <circle cx="16" cy="15" r="1.2" fill="currentColor" />
          </svg>
          <div class="auth-brand__text">YDYD<span>.ME</span></div>
        </div>

        <p class="auth-subtitle">Enter password to unlock playback.</p>

        <label class="auth-field">
          <span class="auth-label">Password</span>
          <input
            ref="authInput"
            v-model="authPassword"
            class="auth-input"
            type="password"
            placeholder="••••••••"
            autocomplete="current-password"
            @keydown.enter.prevent="submitAuth"
          />
        </label>

        <div v-if="authError" class="auth-error">{{ authError }}</div>

        <div class="auth-actions">
          <button class="auth-btn secondary" type="button" @click="closeAuth">Cancel</button>
          <button class="auth-btn primary" type="button" @click="submitAuth">Unlock</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
	import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
	import { useRoute, useRouter } from 'vue-router';
	import { getAuthStatus, login } from '../utils/auth';

const route = useRoute();
const router = useRouter();

const items = ref([]);
const activeIndex = ref(0);
const hasSelected = ref(false);
const loading = ref(true);

const scrollContainer = ref(null);
const itemRefs = ref([]);

const accentPalette = ['#f59e0b', '#ef4444', '#0ea5e9', '#10b981', '#f97316', '#84cc16'];

const authOpen = ref(false);
const authPassword = ref('');
const authError = ref('');
const authInput = ref(null);
let authPendingAction = null;

const activeItem = computed(() => items.value[activeIndex.value] || null);
const activeTitle = computed(() => activeItem.value?.title || '');
const activeYear = computed(() => activeItem.value?.year || '----');
const activeType = computed(() => formatType(activeItem.value?.type));
const activeBackdrop = computed(() => activeItem.value?.backdrop_url || activeItem.value?.poster_url || '');
const activeNumber = computed(() => String(activeIndex.value + 1).padStart(2, '0'));
const activeAccent = computed(() => accentPalette[activeIndex.value % accentPalette.length]);
const progress = computed(() => (items.value.length ? ((activeIndex.value + 1) / items.value.length) * 100 : 0));

const coverUrl = (item) => item?.poster_url || item?.backdrop_url || '';
const headline = (item) => item?.title || '';
const formatType = (type) => {
  if (!type) return 'Unknown';
  if (type === 'Series') return 'Series';
  if (type === 'Movie') return 'Movie';
  return type;
};

const setItemRef = (el, index) => {
  if (!el) return;
  itemRefs.value[index] = el;
};

const selectItem = (index) => {
  activeIndex.value = index;
  hasSelected.value = true;
};

const clearSelection = () => {
  hasSelected.value = false;
};

const openAuth = async () => {
  authError.value = '';
  authPassword.value = '';
  authOpen.value = true;
  await nextTick();
  authInput.value?.focus?.();
};

const closeAuth = () => {
  authOpen.value = false;
  authPassword.value = '';
  authError.value = '';
  authPendingAction = null;

  if (route.query.auth || route.query.next) {
    router.replace({ name: 'Home', query: {} });
  }
};

const submitAuth = async () => {
  authError.value = '';
  const result = await login(authPassword.value);
  if (!result.ok) {
    authError.value = result.error || 'Incorrect password.';
    return;
  }

  // 清理掉 URL 上的 auth/next，避免按返回键回到首页又弹一次
  if (route.query.auth || route.query.next) {
    await router.replace({ name: 'Home', query: {} });
  }

  authOpen.value = false;
  authPassword.value = '';
  authError.value = '';

  const action = authPendingAction;
  authPendingAction = null;
  action?.();
};

const playItem = async (item) => {
  if (!item) return;

  if (item.type === 'Series') {
    try {
      const res = await fetch(`/api/videos?seriesId=${item.id}`);
      const data = await res.json();
      const firstEpisode = data.items?.[0];
      if (!firstEpisode) return;
      router.push({
        name: 'Player',
        params: { id: firstEpisode.id },
        query: { seriesId: item.id },
      });
      return;
    } catch (error) {
      console.error('Failed to fetch episodes:', error);
      return;
    }
  }

  router.push({ name: 'Player', params: { id: item.id } });
};

const requestPlay = async () => {
  const item = activeItem.value;
  if (!item) return;

  const authorized = await getAuthStatus();
  if (!authorized) {
    authPendingAction = () => playItem(item);
    await openAuth();
    return;
  }

  await playItem(item);
};

const prevItem = () => {
  if (activeIndex.value === 0) return;
  activeIndex.value -= 1;
  hasSelected.value = true;
};

const nextItem = () => {
  if (activeIndex.value >= items.value.length - 1) return;
  activeIndex.value += 1;
  hasSelected.value = true;
};

const fetchItems = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/videos?limit=40');
    const data = await res.json();
    items.value = data.items || [];
    itemRefs.value = [];
    if (items.value.length) {
      activeIndex.value = 0;
      hasSelected.value = true;
    }
  } catch (error) {
    console.error('Failed to fetch videos:', error);
  } finally {
    loading.value = false;
  }
};

const handleWheel = (event) => {
  if (!scrollContainer.value) return;
  if (event.deltaY === 0) return;
  event.preventDefault();
  scrollContainer.value.scrollLeft += event.deltaY;
};

watch(activeIndex, async () => {
  await nextTick();
  const el = itemRefs.value[activeIndex.value];
  if (el?.scrollIntoView) {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  }
});

watch(
  () => [route.query.auth, route.query.next],
  async ([authFlag, nextPath]) => {
    const authorized = await getAuthStatus();
    if (authorized) {
      if (authFlag || nextPath) router.replace({ name: 'Home', query: {} });
      return;
    }

    if (authFlag && nextPath && !authOpen.value) {
      authPendingAction = () => router.push(String(nextPath));
      await openAuth();
    }
  },
  { immediate: true }
);

onMounted(() => {
  fetchItems();
  const container = scrollContainer.value;
  if (container) {
    container.addEventListener('wheel', handleWheel, { passive: false });
  }
});

onUnmounted(() => {
  const container = scrollContainer.value;
  if (container) {
    container.removeEventListener('wheel', handleWheel);
  }
});
</script>

<style scoped>
.film-home {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: #f8fafc;
  background: #09090b;
  font-family: var(--font-sans);
}

.ambient-backdrop,
.ambient-color,
.ambient-gradient,
.ambient-noise {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.ambient-backdrop {
  background-size: cover;
  background-position: center;
  filter: blur(32px) brightness(0.35);
  opacity: 0.35;
  transition: background-image 1.2s ease, opacity 1.2s ease;
}

.ambient-color {
  opacity: 0.18;
  transition: background-color 1.2s ease;
}

.ambient-gradient {
  background: linear-gradient(180deg, rgba(9, 9, 11, 0.9) 0%, rgba(9, 9, 11, 0.7) 45%, rgba(9, 9, 11, 0.95) 100%);
}

.ambient-noise {
  opacity: 0.08;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
}

.film-stage {
  position: relative;
  z-index: 2;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-top: 110px;
  box-sizing: border-box;
}

.film-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 36px 18px;
  color: #f8fafc;
  mix-blend-mode: difference;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  letter-spacing: -0.02em;
  text-transform: uppercase;
}

.brand-icon {
  width: 22px;
  height: 22px;
}

.brand-text {
  font-size: 1.1rem;
  font-weight: 800;
}

.brand-text span {
  opacity: 0.5;
}

.header-search {
  display: none;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.3em;
}

.header-search svg {
  width: 14px;
  height: 14px;
}

.header-search input {
  background: transparent;
  border: none;
  outline: none;
  color: inherit;
  font-size: 0.65rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
}

.header-search input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}

.header-icon-btn svg {
  width: 18px;
  height: 18px;
}

.header-icon-btn:hover {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.05);
}

.film-number {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: clamp(10rem, 40vw, 30rem);
  font-weight: 800;
  color: rgba(255, 255, 255, 0.05);
  letter-spacing: -0.02em;
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
  z-index: 1;
}

.film-number.visible {
  opacity: 1;
}

.film-gallery {
  display: flex;
  align-items: center;
  gap: 3.5rem;
  padding: 0 50vw;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  height: 65vh;
  z-index: 3;
  scrollbar-width: none;
}

.film-gallery::-webkit-scrollbar {
  display: none;
}

.film-snap {
  flex: 0 0 auto;
  scroll-snap-align: center;
  perspective: 1200px;
  position: relative;
  z-index: 1;
}

.film-snap.active {
  z-index: 6;
}

.film-item {
  position: relative;
  width: 16rem;
  height: 16rem;
  cursor: pointer;
  transform: scale(0.9);
  opacity: 0.6;
  transition: transform 0.7s cubic-bezier(0.23, 1, 0.32, 1), opacity 0.7s ease;
  z-index: 1;
}

.film-item:hover {
  transform: scale(1);
  opacity: 1;
}

.film-item.active {
  transform: scale(1.1);
  opacity: 1;
  z-index: 6;
}

.film-reel {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 95%;
  height: 95%;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translateX(0) rotate(0deg);
  transition: transform 0.7s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 1;
}

.film-item.active .film-reel {
  transform: translateX(55%) rotate(12deg);
}

.film-item.active .film-reel svg {
  animation: spin-slow 10s linear infinite;
}

.film-reel svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0px 12px 20px rgba(0, 0, 0, 0.6));
}

.film-cover {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #111827;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6);
  z-index: 2;
}

.film-cover__media {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.film-cover__media img,
.film-cover__fallback {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.film-cover__fallback {
  background: linear-gradient(135deg, #1f2937, #111827);
}

.film-cover__grain {
  position: absolute;
  inset: 0;
  opacity: 0.35;
  background-image: url('https://www.transparenttextures.com/patterns/noise-lines.png');
}

.film-cover__shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.2) 0%, rgba(15, 23, 42, 0.7) 100%);
}

.film-cover__top,
.film-cover__title,
.film-cover__bottom {
  position: relative;
  z-index: 1;
}

.film-cover__top {
  padding: 1.2rem 1.3rem 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.film-iso {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.film-iso__value {
  font-size: 1.4rem;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.9);
}

.film-iso__label {
  font-size: 0.55rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
  font-family: var(--font-mono);
}

.film-cover__title {
  margin-top: auto;
  padding: 1.2rem 1.3rem 0.9rem;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.film-divider {
  width: 3rem;
  height: 0.2rem;
  background: rgba(255, 255, 255, 0.4);
  margin-bottom: 1rem;
}

.film-series {
  font-size: clamp(1.6rem, 4vw, 2.8rem);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: -0.02em;
  line-height: 0.9;
  margin: 0;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 12px 30px rgba(0, 0, 0, 0.7);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.film-cover__bottom {
  height: 3.6rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.3rem;
  background: rgba(0, 0, 0, 0.55);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.film-bottom__text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.film-title {
  font-size: 0.9rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.film-type {
  font-size: 0.6rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.6);
  font-family: var(--font-mono);
}

.aperture-icon {
  width: 1.2rem;
  height: 1.2rem;
  color: rgba(255, 255, 255, 0.45);
}

.film-cover__gloss {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, transparent 60%);
  pointer-events: none;
  z-index: 1;
}

.film-info {
  position: absolute;
  bottom: 3rem;
  left: 3rem;
  max-width: 34rem;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.7s ease, transform 0.7s ease;
  z-index: 4;
}

.film-info.visible {
  opacity: 1;
  transform: translateY(0);
}

.film-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.6rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 1rem;
  font-family: var(--font-mono);
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
}

.status-dot.live {
  background: #ef4444;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.6);
}

.film-title-large {
  font-size: clamp(2.5rem, 4.6vw, 4.6rem);
  font-weight: 800;
  margin: 0;
  line-height: 0.95;
  text-transform: uppercase;
  background: linear-gradient(90deg, #ffffff, #cbd5f5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.film-meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 1rem;
  font-family: var(--font-mono);
}

.film-badge {
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.35rem 0.6rem;
  border-radius: 6px;
}

.film-controls {
  position: absolute;
  bottom: 3rem;
  right: 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.7s ease 0.1s, transform 0.7s ease 0.1s;
  z-index: 4;
}

.film-controls.visible {
  opacity: 1;
  transform: translateY(0);
}

.play-button {
  width: 4.8rem;
  height: 4.8rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f8fafc;
  cursor: pointer;
  transition: transform 0.3s ease, background 0.3s ease, color 0.3s ease;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45);
}

.play-button:hover {
  background: #ffffff;
  color: #0f172a;
  transform: scale(1.05);
}

.play-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.play-button svg {
  width: 2rem;
  height: 2rem;
}

.control-row {
  display: flex;
  gap: 1rem;
}

.control-btn {
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.55);
  cursor: pointer;
  transition: color 0.3s ease, transform 0.3s ease;
}

.control-btn:hover {
  color: #ffffff;
  transform: scale(1.08);
}

.control-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.control-btn svg {
  width: 1.6rem;
  height: 1.6rem;
}

.film-progress {
  position: fixed;
  left: 0;
  bottom: 0;
  height: 4px;
  width: 100%;
  background: rgba(255, 255, 255, 0.08);
  opacity: 0;
  transition: opacity 0.4s ease;
  z-index: 5;
}

.film-progress.visible {
  opacity: 1;
}

.film-progress__bar {
  height: 100%;
  background: #ef4444;
  transition: width 0.5s ease;
}

.film-loading {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.9rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
  font-family: var(--font-mono);
  z-index: 3;
}

@keyframes auth-pop {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.auth-overlay {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background: rgba(9, 9, 11, 0.7);
  backdrop-filter: blur(18px);
}

.auth-modal {
  width: min(420px, 100%);
  border-radius: 26px;
  padding: 28px 26px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(24, 24, 27, 0.78);
  box-shadow: 0 40px 140px rgba(0, 0, 0, 0.65);
  animation: auth-pop 0.32s ease forwards;
}

.auth-modal::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 10%, rgba(245, 158, 11, 0.18), transparent 55%),
    radial-gradient(circle at 80% 90%, rgba(14, 165, 233, 0.14), transparent 60%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.06), transparent);
  opacity: 0.95;
  pointer-events: none;
}

.auth-modal > * {
  position: relative;
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.auth-brand__icon {
  width: 42px;
  height: 42px;
  color: rgba(226, 232, 240, 0.85);
}

.auth-brand__text {
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--font-mono);
  color: rgba(226, 232, 240, 0.92);
}

.auth-brand__text span {
  color: var(--accent);
}

.auth-subtitle {
  margin: 0 0 18px;
  color: rgba(226, 232, 240, 0.72);
  line-height: 1.5;
  font-size: 0.92rem;
}

.auth-field {
  display: grid;
  gap: 10px;
}

.auth-label {
  font-size: 0.65rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  font-family: var(--font-mono);
  color: rgba(226, 232, 240, 0.65);
}

.auth-input {
  width: 100%;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(9, 9, 11, 0.55);
  color: rgba(248, 250, 252, 0.95);
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  outline: none;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

.auth-input:focus {
  border-color: rgba(245, 158, 11, 0.65);
  box-shadow: 0 0 0 5px rgba(245, 158, 11, 0.15);
}

.auth-error {
  margin-top: 12px;
  font-size: 0.85rem;
  color: rgba(248, 113, 113, 0.95);
}

.auth-actions {
  margin-top: 22px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.auth-btn {
  border-radius: 999px;
  padding: 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
  font-family: var(--font-mono);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-size: 0.62rem;
  color: rgba(226, 232, 240, 0.85);
  transition: transform 0.25s ease, border-color 0.25s ease, background 0.25s ease, color 0.25s ease;
}

.auth-btn:hover {
  transform: translateY(-1px);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.1);
}

.auth-btn.primary {
  border-color: rgba(245, 158, 11, 0.55);
  background: rgba(245, 158, 11, 0.18);
  color: rgba(255, 255, 255, 0.95);
}

.auth-btn.primary:hover {
  border-color: rgba(245, 158, 11, 0.85);
  background: rgba(245, 158, 11, 0.25);
}

@keyframes spin-slow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 960px) {
  .film-header {
    padding: 22px 24px 16px;
  }

  .film-gallery {
    gap: 2.2rem;
    height: 55vh;
    padding: 0 40vw;
  }

  .film-item {
    width: 13rem;
    height: 13rem;
  }

  .film-info {
    left: 2rem;
    bottom: 5rem;
  }

  .film-controls {
    right: 2rem;
    bottom: 5rem;
  }
}

@media (max-width: 640px) {
  .film-stage {
    padding-top: 70px;
  }

  .film-header {
    mix-blend-mode: normal;
    padding: 18px 18px 12px;
  }

  .brand-text {
    font-size: 1rem;
  }

  .film-gallery {
    height: 50vh;
    padding: 0 35vw;
  }

  .film-item {
    width: 11rem;
    height: 11rem;
  }

  .film-info {
    left: 1.5rem;
    bottom: 6rem;
    max-width: 70%;
  }

  .film-controls {
    right: 1.5rem;
    bottom: 6rem;
  }

  .play-button {
    width: 4rem;
    height: 4rem;
  }
}

@media (min-width: 768px) {
  .header-search {
    display: flex;
    width: 280px;
  }
}
</style>
