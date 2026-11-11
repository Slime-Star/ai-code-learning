export function shuffled(values) {
  const result = [...values]
  for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [result[i], result[j]] = [result[j], result[i]] }
  return result
}
export function gridNeighbors(index) {
  return [index - 3, index + 3, index - 1, index + 1].filter(i => i >= 0 && i < 9 && Math.abs(Math.floor(i / 3) - Math.floor(index / 3)) + Math.abs(i % 3 - index % 3) === 1)
}
export function toggleLights(board, index) {
  const affected = [index, ...gridNeighbors(index)]
  return board.map((value, i) => affected.includes(i) ? !value : value)
}
export function newLights() {
  let board = Array(9).fill(false)
  for (const index of shuffled([0,1,2,3,4,5,6,7,8]).slice(0,4)) board = toggleLights(board,index)
  return board.some(Boolean) ? board : toggleLights(board,4)
}
export function slideTile(board,index) {
  const empty = board.indexOf(0)
  if (!gridNeighbors(empty).includes(index)) return board
  const next = [...board]; [next[empty],next[index]] = [next[index],next[empty]]
  return next
}
export const puzzleSolved = board => board.every((value,index) => value === (index + 1) % 9)
export function newPuzzle() {
  let board = [1,2,3,4,5,6,7,8,0], previous = -1
  for (let step = 0; step < 40; step++) {
    const empty = board.indexOf(0), choices = gridNeighbors(empty).filter(i => i !== previous)
    board = slideTile(board,choices[Math.floor(Math.random() * choices.length)])
    previous = empty
  }
  return puzzleSolved(board) ? slideTile(board,7) : board
}
