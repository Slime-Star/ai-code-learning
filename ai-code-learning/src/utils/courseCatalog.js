const coverAssets = import.meta.glob('../assets/pictures/*', { eager: true, query: '?url', import: 'default' })

export const normalizeCourses = items => items.map(item => ({
  ...item,
  cover: coverAssets[`../assets/pictures/${item.cover}`] || item.cover,
  isCollected: false
}))
