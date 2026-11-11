const finite = value => Number.isFinite(Number(value)) ? Math.max(0, Number(value)) : 0
export const learningRateColors = [
  { label: '暂无提交', color: '#77718e' },
  { label: '低于 60%', color: '#d6a496' },
  { label: '60%–85%', color: '#b7a1e4' },
  { label: '85% 及以上', color: '#9bcab8' }
]
export function studentRate(student) {
  if (!finite(student?.stats?.total_submissions)) return null
  return Math.min(100, finite(student?.stats?.success_rate))
}
export function summarizeStudents(students) {
  const unique = [...new Map(students.map(student => [String(student.id), student])).values()]
  const total = unique.reduce((sum, student) => sum + finite(student.stats?.total_submissions), 0)
  const passed = unique.reduce((sum, student) => {
    const runs = finite(student.stats?.total_submissions)
    const success = student.stats?.success_count
    return sum + Math.min(runs, success == null ? runs * (studentRate(student) || 0) / 100 : finite(success))
  }, 0)
  return { count: unique.length, active: unique.filter(student => studentRate(student) !== null).length, total, rate: total ? passed / total * 100 : null }
}
const colorForRate = rate => learningRateColors[rate === null ? 0 : rate < 60 ? 1 : rate < 85 ? 2 : 3].color
const classColors = ['#9676c2', '#8e82c9', '#ac82bb', '#7a91b8', '#a393cf', '#b888a8']
const classColor = id => classColors[Array.from(String(id)).reduce((sum, char) => sum + char.charCodeAt(0), 0) % classColors.length]
const gradient = color => ({ type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color }, { offset: 1, color: `${color}b5` }] })

export function buildLearningSunburst(classes, students, { focusedClassId = '', selectedStudentId = '' } = {}) {
  const visible = focusedClassId ? classes.filter(item => String(item.id) === String(focusedClassId)) : classes
  return visible.map(item => {
    const members = students.filter(student => String(student.classId) === String(item.id))
    const summary = summarizeStudents(members)
    const children = members.length ? members.map(student => {
      const rate = studentRate(student), selected = String(student.id) === String(selectedStudentId)
      return {
        id: `student:${item.id}:${student.id}`, name: String(student.name || student.username || '未命名学生'), value: 1,
        nodeType: 'student', studentId: student.id, classId: item.id, className: item.name,
        successRate: rate, totalSubmissions: finite(student.stats?.total_submissions),
        itemStyle: { color: gradient(colorForRate(rate)), borderColor: selected ? '#f2ddb7' : '#261d3b', borderWidth: selected ? 3 : 2, borderRadius: 5 },
        label: { color: '#241c34' }, cursor: 'pointer'
      }
    }) : [{ id: `empty:${item.id}`, name: '暂无学生', value: 1, nodeType: 'empty', className: item.name, itemStyle: { color: '#5a4f70', opacity: .4 }, label: { show: false }, cursor: 'default' }]
    return {
      id: `class:${item.id}`, name: String(item.name || '未命名班级'), value: children.length,
      classId: item.id, className: item.name, nodeType: focusedClassId ? 'class_focus' : 'class',
      avgRate: summary.rate, studentCount: members.length, totalSubmissions: summary.total,
      itemStyle: { color: gradient(classColor(item.id)), borderColor: '#261d3b', borderWidth: 3, borderRadius: 7 },
      children, cursor: focusedClassId ? 'default' : 'pointer'
    }
  })
}

export function createLearningSunburstOption(data, { compact = false } = {}) {
  const focused=data.some(node=>node.nodeType==='class_focus')
  const rateText = value => value == null ? '暂无提交' : `${Number(value).toFixed(1)}%`
  return {
    backgroundColor: 'transparent', animation: true, animationDuration: 800, animationDurationUpdate: 720,
    animationEasing: 'cubicOut', animationEasingUpdate: 'cubicInOut',
    tooltip: {
      trigger: 'item', renderMode: 'richText', confine: true, backgroundColor: '#241b36', borderColor: '#7f669d',
      borderWidth: 1, padding: [13, 16], textStyle: { color: '#eee4f7', fontSize: 12, lineHeight: 22 },
      formatter: params => {
        const node = params.data || {}
        if (node.nodeType === 'empty') return `${node.className}\n暂无学生`
        if (node.nodeType === 'student') return `${node.name} · ${node.className}\n正确率  ${rateText(node.successRate)}\n提交次数  ${node.totalSubmissions}\n点击联动右侧错误分析 ↗`
        return `${node.name}\n学生人数  ${node.studentCount}\n整体正确率  ${rateText(node.avgRate)}\n${node.nodeType === 'class' ? '点击展开班级 ↗' : '外圈为班级学生'}`
      }
    },
    series: [{
      id: 'teacher-learning-orbit', type: 'sunburst', data, center: ['50%', '50%'], radius: ['35%', focused?'91%':'89%'],
      animation: true, animationDuration: 800, animationDurationUpdate: 720,
      animationEasing: 'cubicOut', animationEasingUpdate: 'cubicInOut',
      sort: null, startAngle: 90, nodeClick: false, animationType: 'scale',
      emphasis: { focus: 'relative', itemStyle: { borderColor: '#f0deff', borderWidth: 3, shadowBlur: 15, shadowColor: '#cbb1ff60' } },
      blur: { itemStyle: { opacity: .3 }, label: { opacity: .25 } },
      label: { color: '#eee4f7', fontFamily: 'Microsoft YaHei, sans-serif', overflow: 'truncate', silent: true },
      levels: [
        {},
        { radius: ['36%', focused?'50%':'57%'], label: { rotate: 'tangential', fontSize: compact ? 10 : 12, fontWeight: 600, minAngle: 17, width: compact ? 58 : 85 } },
        { radius: [focused?'53%':'60%', focused?'91%':'89%'], label: {
          rotate: 'radial', minAngle: compact ? 16 : 12, fontSize: compact ? 10 : 11, width: compact ? 50 : 65,
          formatter: params => params.data?.nodeType === 'student' ? String(params.name || '') : ''
        } }
      ]
    }]
  }
}
