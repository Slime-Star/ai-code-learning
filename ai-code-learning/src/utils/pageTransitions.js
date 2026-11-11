// Match the actual menu order so motion conveys navigation direction.
const menuOrder={Home:0,LearningCenter:1,TeacherLearningCenter:1,DailyCheckIn:2,TeacherCheckinManage:2,Library:3,Competition:4,TeacherCompetitionManage:4,Forum:5,Leaderboard:6,Messages:7,Class:8,PointsMall:9,TeacherWorkbench:10,TeacherClassManage:10,TeacherStudentData:10,TeacherTaskManage:10}
const detailPages=new Set(['Profile','WrongQuestions','Login','Register','Learn','CodeJudge','CompetitionPlay','TeacherCreateTask'])

export function getPageTransition(to,from){
  if(from==='Login' && to!=='Login' && to!=='Register')return {mode:'login',direction:1}
  if(detailPages.has(to) || detailPages.has(from))return {mode:'depth',direction:detailPages.has(to)?1:-1}
  const next=menuOrder[to],previous=menuOrder[from]
  if(next===undefined || previous===undefined)return {mode:'turn',direction:1}
  const distance=next-previous,direction=distance<0?-1:1
  if(Math.abs(distance)>=3)return {mode:'stack',direction}
  return {mode:direction>0?'turn':'glide',direction}
}
