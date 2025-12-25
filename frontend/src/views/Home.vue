<template>
  <div class="home">
    <!-- Hero Carousel -->
    <div v-if="heroItems.length > 0" class="hero-carousel">
      <div 
        v-for="(item, index) in heroItems" 
        :key="item.id"
        class="hero-slide"
        :class="{ active: index === currentHeroIndex }"
        :style="{ backgroundImage: `url(${item.backdrop_url || item.poster_url})` }"
      >
        <div class="hero-overlay">
          <div class="hero-content">
            <h1 class="hero-title">{{ item.title }}</h1>
            <p class="hero-meta">{{ item.year }} | {{ item.type }}</p>
            <button class="play-btn" @click="goToDetail(item)">
              <span class="icon">▶</span> 立即观看
            </button>
          </div>
        </div>
      </div>
      
      <!-- Indicators -->
      <div class="hero-indicators">
        <span 
          v-for="(item, index) in heroItems" 
          :key="index"
          class="indicator" 
          :class="{ active: index === currentHeroIndex }"
          @click="currentHeroIndex = index"
        ></span>
      </div>
    </div>

    <!-- Latest Updates Section (Accordion Style) -->
    <div class="section-container">
      <h2 class="section-title">热门推荐</h2>
      <div class="accordion-gallery">
        <div 
          v-for="item in videos.slice(0, 10)" 
          :key="item.id" 
          class="accordion-item"
          :style="{ backgroundImage: `url(${item.backdrop_url || item.poster_url})` }"
          @click="goToDetail(item)"
        >
          <div class="accordion-overlay">
            <h3 class="accordion-title">{{ item.title }}</h3>
            <div class="accordion-content">
              <p class="accordion-meta">{{ item.year }} | {{ item.type }}</p>
              <button class="mini-play-btn">▶</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const videos = ref([]);
const heroItems = ref([]);
const currentHeroIndex = ref(0);
const router = useRouter();
let carouselInterval = null;

const fetchVideos = async () => {
  try {
    const res = await fetch('/api/videos?limit=50');
    const data = await res.json();
    videos.value = data.items;
    
    // Setup Hero (First 5 items)
    heroItems.value = videos.value.slice(0, 5);
    startCarousel();
    
  } catch (error) {
    console.error("Failed to fetch videos:", error);
  }
};

const startCarousel = () => {
  if (carouselInterval) clearInterval(carouselInterval);
  carouselInterval = setInterval(() => {
    currentHeroIndex.value = (currentHeroIndex.value + 1) % heroItems.value.length;
  }, 5000);
};

const goToDetail = (item) => {
  router.push({
    name: 'Detail',
    params: { id: item.id },
    query: { 
      type: item.type,
      title: item.title,
      backdrop: item.backdrop_url
    }
  });
};

onMounted(() => {
  fetchVideos();
});

onUnmounted(() => {
  if (carouselInterval) clearInterval(carouselInterval);
});
</script>

<style scoped>
.home {
  padding-bottom: 50px;
  /* background managed by style.css body */
}

/* Hero Carousel Styles */
.hero-carousel {
  height: 75vh;
  position: relative;
  overflow: hidden;
  margin-bottom: 40px;
  /* Mimic reference container style slightly */
  box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.5);
}

.hero-slide {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  opacity: 0;
  transition: opacity 1s ease-in-out;
  display: flex;
  align-items: flex-end;
}

.hero-slide.active {
  opacity: 1;
  z-index: 1;
}

.hero-overlay {
  background: linear-gradient(to top, #0a0a0a 0%, rgba(25, 26, 30, 0.6) 60%, rgba(0,0,0,0) 100%);
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  align-items: flex-end;
}

.hero-content {
  padding: 0 6% 80px;
  max-width: 800px;
  transform: translateY(20px);
  opacity: 0;
  transition: transform 0.8s ease, opacity 0.8s ease;
}

.hero-slide.active .hero-content {
  transform: translateY(0);
  opacity: 1;
  transition-delay: 0.3s;
}

.hero-title {
  font-family: 'Ubuntu', sans-serif;
  font-size: 3.5rem;
  margin-bottom: 10px;
  color: white;
  text-shadow: 0 4px 15px rgba(133, 62, 255, 0.3); /* Purple glow */
  font-weight: 700;
}

.hero-meta {
  font-size: 1.1rem;
  color: #e8e8e8;
  margin-bottom: 25px;
  background: rgba(25, 26, 30, 0.6);
  display: inline-block;
  padding: 5px 15px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.05);
}

.hero-indicators {
  position: absolute;
  bottom: 30px;
  right: 6%;
  z-index: 10;
  display: flex;
  gap: 12px;
}

.indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 0 2px transparent;
}

.indicator.active {
  background: linear-gradient(135deg, #853eff, #f76cc6); /* Reference dot */
  transform: scale(1.3);
  box-shadow: 0 0 15px rgba(133, 62, 255, 0.6);
}

.play-btn {
  background: linear-gradient(135deg, #853eff, #f76cc6);
  color: white;
  border: none;
  padding: 12px 35px;
  font-size: 1.1rem;
  border-radius: 30px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-weight: bold;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(133, 62, 255, 0.3);
}

.play-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 30px rgba(133, 62, 255, 0.5), 0 0 20px rgba(247, 108, 198, 0.4);
}

.play-btn .icon {
  margin-right: 8px;
}

/* Section Common */
.section-container {
  padding: 0 6%;
  margin-top: 40px;
  position: relative;
  z-index: 10;
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}

.section-title {
  font-size: 1.8rem;
  margin-bottom: 30px;
  /* Reference title bar style */
  position: relative;
  padding-left: 15px;
  color: #fff;
  font-weight: 800;
  border-left: none;
}

.section-title::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 5px;
    height: 65%;
    background: linear-gradient(180deg, #853eff, #f76cc6);
    border-radius: 3px;
    box-shadow: 0 0 15px rgba(133, 62, 255, 0.3);
}

/* Accordion Gallery (Reference .projectItem style) */
.accordion-gallery {
  display: flex;
  gap: 15px;
  height: 450px;
}

.accordion-item {
  flex: 1;
  background-size: cover;
  background-position: center;
  border-radius: 12px;
  position: relative;
  cursor: pointer;
  transition: flex 0.5s cubic-bezier(0.4, 0, 0.2, 1), transform 0.4s;
  overflow: hidden;
  /* Base card style from reference */
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  border: none;
}

/* Overlay to dim background initially */
.accordion-item::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(25, 26, 30, 0.4);
    transition: opacity 0.4s ease;
    z-index: 0;
}

.accordion-item:hover {
  flex: 3.5;
  transform: translateY(-12px) scale(1.02);
  z-index: 10;
  /* Hover glow from reference */
  box-shadow: 0 20px 50px rgba(133, 62, 255, 0.25),
              0 10px 30px rgba(0, 0, 0, 0.15),
              0 0 80px rgba(247, 108, 198, 0.15),
              inset 0 0 60px rgba(133, 62, 255, 0.03);
  filter: brightness(1.05);
}

.accordion-item:hover::before {
    opacity: 0; /* Show full image brightness */
}

.accordion-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(to top, rgba(25, 26, 30, 0.95) 0%, rgba(25, 26, 30, 0.6) 60%, rgba(0,0,0,0) 100%);
  padding: 30px 20px;
  opacity: 0.9;
  transition: opacity 0.3s;
  z-index: 1;
}

.accordion-title {
  font-size: 1.4rem;
  margin: 0;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  transition: color 0.3s ease;
}

.accordion-item:hover .accordion-title {
    /* Gradient text on hover */
    background: linear-gradient(135deg, #f76cc6, #ffa5d8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.accordion-content {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.5s ease;
  opacity: 0;
}

.accordion-item:hover .accordion-content {
  max-height: 100px;
  opacity: 1;
}

.accordion-meta {
  font-size: 0.95rem;
  color: #b8b8b8;
  margin: 8px 0 15px;
}

.mini-play-btn {
  background: linear-gradient(135deg, rgba(133, 62, 255, 0.35), rgba(247, 108, 198, 0.35));
  box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  width: 45px;
  height: 45px;
  border-radius: 12px; /* Reference uses rounded squares for small icons usually, or circle */
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-play-btn:hover {
  transform: scale(1.1) rotate(5deg);
  background: linear-gradient(135deg, #853eff, #f76cc6);
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .hero-title { font-size: 2.5rem; }
  .accordion-gallery { flex-direction: column; height: auto; }
  .accordion-item { height: 120px; flex: none; width: 100%; }
  .accordion-item:hover { flex: none; height: 350px; }
  .hero-carousel { height: 60vh; }
}
</style>