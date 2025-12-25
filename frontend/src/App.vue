<template>
  <div class="app-container">
    <nav class="navbar">
      <div class="logo">MuYuDonghua</div>
      <div class="links">
        <router-link to="/">首页</router-link>
      </div>
    </nav>
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 4%;
  background: rgba(25, 26, 30, 0.6); /* Semi-transparent dark */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  position: fixed;
  top: 0;
  width: 92%;
  z-index: 100;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.logo {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #853eff 0%, #f76cc6 100%); /* Reference Gradient */
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-transform: uppercase;
  letter-spacing: 2px;
  filter: drop-shadow(0 0 15px rgba(133, 62, 255, 0.3));
}

.links a {
  margin-left: 20px;
  font-weight: 600;
  color: #b8b8b8; /* --item-left-text-color */
  font-family: 'Ubuntu', sans-serif;
  transition: all 0.3s ease;
}

.links a:hover, .links a.router-link-active {
  color: #f76cc6; /* Pink accent */
  text-shadow: 0 0 10px rgba(247, 108, 198, 0.4);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>