<template>
  <canvas ref="canvas" class="star-background"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvas = ref(null)
let animationFrameId = null

const createStars = (ctx, width, height) => {
  const stars = []
  const starCount = 200

  for (let i = 0; i < starCount; i++) {
    stars.push({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 1.5,
      speed: Math.random() * 0.5,
      brightness: Math.random()
    })
  }

  return stars
}

const animate = (ctx, stars, width, height) => {
  ctx.clearRect(0, 0, width, height)

  stars.forEach(star => {
    ctx.beginPath()
    ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(255, 255, 255, ${star.brightness})`
    ctx.fill()

    star.y += star.speed
    if (star.y > height) {
      star.y = 0
      star.x = Math.random() * width
    }

    star.brightness = Math.sin(Date.now() * 0.001 + star.x) * 0.5 + 0.5
  })

  animationFrameId = requestAnimationFrame(() => animate(ctx, stars, width, height))
}

onMounted(() => {
  const ctx = canvas.value.getContext('2d')
  const resizeCanvas = () => {
    canvas.value.width = window.innerWidth
    canvas.value.height = window.innerHeight
  }

  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)

  const stars = createStars(ctx, canvas.value.width, canvas.value.height)
  animate(ctx, stars, canvas.value.width, canvas.value.height)
})

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<style scoped>
.star-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}
</style> 