export const winningLines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
export function gameResult(board) {
  for (const line of winningLines) if (board[line[0]] && line.every(index => board[index] === board[line[0]])) return { winner: board[line[0]], line }
  return board.every(Boolean) ? { winner: 'draw', line: [] } : null
}
export function bestComputerMove(board) {
  if (gameResult(board)) return -1
  function score(state, turn, depth, alpha, beta) {
    const result = gameResult(state)
    if (result) return result.winner === 'O' ? 10 - depth : result.winner === 'X' ? depth - 10 : 0
    let best = turn === 'O' ? -Infinity : Infinity
    for (let i = 0; i < 9; i++) {
      if (state[i]) continue
      state[i] = turn
      const value = score(state, turn === 'O' ? 'X' : 'O', depth + 1, alpha, beta)
      state[i] = ''
      best = turn === 'O' ? Math.max(best, value) : Math.min(best, value)
      if (turn === 'O') alpha = Math.max(alpha, best); else beta = Math.min(beta, best)
      if (beta <= alpha) break
    }
    return best
  }
  let choice = -1, best = -Infinity
  const state = [...board]
  for (const index of [4,0,2,6,8,1,3,5,7]) {
    if (state[index]) continue
    state[index] = 'O'
    const value = score(state, 'X', 0, -Infinity, Infinity)
    state[index] = ''
    if (value > best) { best = value; choice = index }
  }
  return choice
}
