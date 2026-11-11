const themes = {
  Home: {theme:'editor',kind:'code',scene:'terminal',motion:'horizontal',phrase:'const idea = create();',symbol:'{ }',example:'write();\nrun();\nunderstand();'},
  LearningCenter: {theme:'knowledge',kind:'code',scene:'network',motion:'diagonal',phrase:'knowledge.connect(ideas)',symbol:'↗',example:'learn → practice\n      → understand'},
  Library: {theme:'documents',kind:'topic',scene:'books',motion:'shelves',phrase:'docs / references / notes',symbol:'.md',example:'readme.md\nguide.pdf\nreference.json'},
  Forum: {theme:'discussion',kind:'topic',scene:'chat',motion:'reverse',phrase:'ask → discuss → discover',symbol:'//',example:'question: "why?"\nreply: "try this"\ninsight: shared'},
  Competition: {theme:'challenge',kind:'competition',scene:'timer',motion:'diagonal',phrase:'think → solve → test',symbol:'test()',example:'input\nalgorithm\noutput'},
  Leaderboard: {theme:'ranking',kind:'topic',scene:'trophy',motion:'rise',phrase:'a little better, every day',symbol:'++',example:'effort + practice\n       = progress'},
  PointsMall: {theme:'rewards',kind:'topic',scene:'gift',motion:'sway',phrase:'collect small achievements',symbol:'+1',example:'effort → reward\ncuriosity → discovery'},
  DailyCheckIn: {theme:'calendar',kind:'topic',scene:'calendar',motion:'rise',phrase:'one day, one small step',symbol:'✓',example:'today: practice\nnext: keep going'},
  DailySignin: {theme:'calendar',kind:'topic',scene:'calendar',motion:'rise',phrase:'show up, grow a little',symbol:'✓',example:'day 01\nday 02\nday 03'},
  Class: {theme:'teamwork',kind:'topic',scene:'team',motion:'diagonal',phrase:'build things together',symbol:'&',example:'classmates.connect()\nideas.share()'},
  Messages: {theme:'mail',kind:'mail',motion:'reverse',phrase:'hello → conversation',symbol:'@',example:'from: a friend\nto: you\nmessage: hello!'},
  Profile: {theme:'identity',kind:'topic',scene:'identity',motion:'sway',phrase:'your journey, your pace',symbol:'me',example:'skills: growing\ncuriosity: always'},
  WrongQuestions: {theme:'debug',kind:'topic',scene:'debug',motion:'scan',phrase:'inspect → fix → understand',symbol:'?',example:'expected ≠ actual\nfind the difference\ntry again'},
  Login: {theme:'security',kind:'topic',scene:'shield',motion:'sway',phrase:'welcome back',symbol:'key',example:'identity.verify()\nlearning.resume()'},
  Register: {theme:'start',kind:'code',scene:'stack',motion:'rise',phrase:'a new chapter starts here',symbol:'new',example:'discover()\nexplore()\ncreate()'},
  TeacherWorkbench: {theme:'workflow',kind:'topic',scene:'pipeline',motion:'horizontal',phrase:'plan → teach → review',symbol:'→',example:'lesson.plan()\nclass.prepare()'},
  TeacherStudentData: {theme:'analytics',kind:'topic',scene:'data',motion:'rise',phrase:'observe the learning journey',symbol:'∑',example:'patterns\nprogress\ninsights'},
  TeacherLearningCenter: {theme:'teaching',kind:'topic',scene:'orbit',motion:'sway',phrase:'connect knowledge and people',symbol:'∞',example:'understand\nexplain\ninspire'},
  TeacherClassManage: {theme:'teamwork',kind:'topic',scene:'team',motion:'diagonal',phrase:'guide a class, grow together',symbol:'&',example:'members\ngroups\nconnections'},
  TeacherCheckinManage: {theme:'calendar',kind:'topic',scene:'calendar',motion:'rise',phrase:'consistency makes progress',symbol:'✓',example:'schedule\npractice\nfeedback'},
  TeacherCreateTask: {theme:'authoring',kind:'code',scene:'terminal',motion:'horizontal',phrase:'turn an idea into a task',symbol:'[]',example:'question\nexamples\nexpected output'},
  TeacherTaskManage: {theme:'tasks',kind:'topic',scene:'chip',motion:'scan',phrase:'organize the next challenge',symbol:'01',example:'check cases\nreview rules\nrefine tasks'},
  TeacherCompetitionManage: {theme:'assessment',kind:'competition',scene:'flags',motion:'reverse',phrase:'prepare a fair challenge',symbol:'GO',example:'plan\norganize\nreview'}
}
const learningSections = [
  themes.LearningCenter,
  {...themes.LearningCenter,theme:'learning-paths',kind:'code',scene:'stack',motion:'rise',phrase:'small steps build skills',symbol:'01',example:'foundation\npractice\nprojects'},
  {...themes.Library,theme:'course-notes',motion:'reverse',phrase:'discover the next lesson',symbol:'ABC',example:'concepts\nexamples\nexercises'}
]
export function getBackdropTheme(page,section=0) {
  return page === 'LearningCenter' ? learningSections[section % learningSections.length] : themes[page] || themes.Home
}
