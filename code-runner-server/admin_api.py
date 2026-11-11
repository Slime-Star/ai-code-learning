"""Administrator API. SQL identifiers come only from the module allowlist below."""
import base64
import csv
import io
import json
import secrets
import sqlite3
import urllib.request
import urllib.error
import urllib.parse
from contextlib import closing
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Header, HTTPException, Query
from fastapi.responses import Response

LABELS = dict(zip(
    'id username name email role avatar created_at updated_at student_id student_name problem_id code language input_data output error success teacher_id class_id title description starter_code expected_output solution_code due_at user_id joined_at competition_id task_id category points sort status type duration register_time competition_time tags detail_desc rules rewards mode ended_at competition_name user_name registered_at passed score feedback graded_by graded_at goods_id goods_name goods_image stock image change reason signin_date consecutive_days daily_checkin practice_done conversation_id sender_id content friend_id from_user_id to_user_id kind key expires_at last_read_at last_read_id author_id author_name pinned post_id admin_id admin_name action module record_key before_data after_data exercise_metadata collected_courses'.split(),
    '编号 用户名 名称 邮箱 角色 头像 创建时间 更新时间 学生编号 学生姓名 题目编号 代码 语言 输入 输出 错误信息 执行成功 教师编号 班级编号 标题 描述 初始代码 预期输出 参考答案 截止时间 用户编号 加入时间 测试编号 题目编号 分类 积分 排序 状态 类型 时长 报名时间 测试时间 标签 详细介绍 规则 奖励 模式 结束时间 测试名称 用户姓名 报名时间 是否通过 分数 评语 评分教师 评分时间 商品编号 商品名称 商品图片 库存 图片 积分变动 原因 签到日期 连续天数 打卡记录 练习记录 会话编号 发送者 内容 好友编号 发起者 接收者 类型 解锁编号 有效期 已读时间 已读消息 作者编号 作者 置顶 帖子编号 操作人编号 操作人 操作 模块 记录编号 修改前 修改后 题目资料 收藏课程'.split()))
LABELS.update({'desc': '简介', 'code': '代码 / 邀请码', 'difficulty': '难度', 'participants': '参加人数'})
JSON_FIELDS = {'tags', 'rules', 'rewards', 'daily_checkin', 'practice_done', 'exercise_metadata', 'collected_courses'}
NUMBERS = {'points', 'stock', 'change', 'score', 'participants', 'sort', 'consecutive_days', 'last_read_id'}
TEXTAREAS = {'code', 'input_data', 'output', 'error', 'description', 'desc', 'detail_desc', 'starter_code', 'expected_output', 'solution_code', 'content', 'feedback', 'before_data', 'after_data'} | JSON_FIELDS
CHOICES = {'role': ['student', 'teacher', 'admin'], 'language': ['python', 'javascript', 'java', 'cpp', 'c'], 'success': [0, 1], 'passed': [0, 1], 'pinned': [0, 1]}
FILTERS = {
    'users': {'role': CHOICES['role']},
    'runs': {'language': CHOICES['language'], 'success': [0, 1], 'day': None},
    'tasks': {'language': CHOICES['language']},
    'competitions': {'status': ['registering', 'ongoing', 'ended'], 'mode': ['general', 'problem_set']},
    'submissions': {'language': CHOICES['language'], 'passed': [0, 1]},
    'posts': {'pinned': [0, 1]},
    'exchanges': {'status': ['pending', 'completed']},
    'exercises': {'language': CHOICES['language']},
}


def parse_filters(module, raw):
    try:
        values = json.loads(raw) if raw else {}
        if not isinstance(values, dict):
            raise ValueError()
        result = {}
        for name, value in values.items():
            if name not in FILTERS.get(module, {}):
                raise ValueError()
            if value is None or value == '':
                continue
            options = FILTERS[module][name]
            if name == 'day':
                if not isinstance(value, str) or datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d') != value:
                    raise ValueError()
            elif value not in options:
                raise ValueError()
            result[name] = value
        return result
    except (ValueError, TypeError):
        raise HTTPException(422, '筛选条件无效，请清除筛选后重试')


def spec(label, group, table, keys, fields, editable='', create=False):
    return {'label': label, 'group': group, 'table': table, 'keys': keys.split(), 'columns': fields.split(), 'editable': editable.split(), 'create': create, 'delete': True}


MODULES = {
    'users': spec('用户账号', '账号与安全', 'users', 'id', 'id username name email role created_at collected_courses', 'username name email role avatar collected_courses', True),
    'sessions': spec('登录会话', '账号与安全', 'sessions', '_rowid', '_rowid user_id expires_at created_at'),
    'runs': spec('代码运行记录', '学习数据', 'code_submissions', 'id', 'id student_id student_name problem_id language success created_at code input_data output error exercise_metadata', 'student_name problem_id code language input_data output error success exercise_metadata'),
    'states': spec('打卡与练习进度', '学习数据', 'user_state', 'user_id', 'user_id daily_checkin practice_done updated_at', 'daily_checkin practice_done'),
    'signin': spec('每日签到记录', '学习数据', 'daily_signin', 'id', 'id user_id signin_date consecutive_days created_at'),
    'unlocks': spec('答案解锁记录', '学习数据', 'solution_unlocks', 'user_id kind key', 'user_id kind key created_at'),
    'classes': spec('班级管理', '教学管理', 'classes', 'id', 'id name code teacher_id created_at', 'name teacher_id', True),
    'members': spec('班级成员', '教学管理', 'class_members', 'class_id student_id', 'class_id student_id joined_at', '', True),
    'tasks': spec('教师题目', '教学管理', 'checkin_tasks', 'id', 'id title teacher_id class_id language due_at created_at description starter_code expected_output solution_code', 'title teacher_id class_id language due_at description starter_code expected_output solution_code', True),
    'competitions': spec('班级测试', '教学管理', 'competitions', 'id', 'id name teacher_id type mode status difficulty participants duration register_time competition_time created_at desc tags detail_desc rules rewards ended_at', 'name teacher_id type mode status difficulty duration register_time competition_time desc tags detail_desc rules rewards', True),
    'problems': spec('测试题目配置', '教学管理', 'competition_problems', 'id', 'id competition_id task_id category points sort created_at', 'category points sort', True),
    'registrations': spec('测试报名', '教学管理', 'competition_registrations', 'id', 'id competition_id competition_name user_id user_name registered_at', 'user_name'),
    'submissions': spec('测试提交与评分', '教学管理', 'competition_submissions', 'id', 'id competition_id task_id user_id language passed score feedback graded_by graded_at created_at code input_data output error', 'score feedback'),
    'posts': spec('论坛帖子', '内容管理', 'forum_posts', 'id', 'id title author_id author_name category pinned created_at content', 'title author_name category pinned content', True),
    'comments': spec('论坛评论', '内容管理', 'forum_comments', 'id', 'id post_id user_id user_name created_at content', 'user_name content'),
    'likes': spec('论坛点赞', '内容管理', 'forum_likes', 'post_id user_id', 'post_id user_id created_at'),
    'goods': spec('积分商品', '积分管理', 'points_goods', 'id', 'id name category points stock image created_at desc', 'name category points stock image desc', True),
    'points': spec('积分流水', '积分管理', 'points_logs', 'id', 'id user_id change type reason created_at', 'reason', True),
    'exchanges': spec('兑换记录', '积分管理', 'exchange_records', 'id', 'id user_id goods_id goods_name points status created_at goods_image', 'status'),
    'conversations': spec('消息会话', '消息与社交', 'conversations', 'id', 'id type title class_id created_at', 'title'),
    'conversation-members': spec('会话成员', '消息与社交', 'conversation_members', 'conversation_id user_id', 'conversation_id user_id joined_at last_read_at last_read_id'),
    'messages': spec('站内消息', '消息与社交', 'messages', 'id', 'id conversation_id sender_id content created_at', 'content'),
    'friends': spec('好友关系', '消息与社交', 'friends', 'user_id friend_id', 'user_id friend_id created_at'),
    'friend-requests': spec('好友申请', '消息与社交', 'friend_requests', 'id', 'id from_user_id to_user_id status created_at'),
    'audit': spec('管理操作记录', '账号与安全', 'admin_audit', 'id', 'id admin_name action module record_key created_at before_data after_data'),
}
MODULES['audit']['delete'] = False
# Earned points and sign-in rewards are immutable facts. Corrections use an explicit points adjustment.
MODULES['points']['delete'] = False
MODULES['signin']['delete'] = False

CATALOGS = {
    'courses': {'label': '课程管理', 'fields': 'name desc cover duration level teacher score tags category videoUrl', 'required': ['name', 'videoUrl']},
    'exercises': {'label': '每日练习题库', 'fields': 'title language languageLabel difficulty topic description starterCode expectedOutput solutionCode', 'required': ['title', 'language', 'description']},
}
CAT_LABELS = {'name': '课程名称', 'desc': '简介', 'cover': '封面地址或图片文件名', 'duration': '课时', 'level': '级别', 'teacher': '讲师', 'score': '评分', 'tags': '标签（JSON数组）', 'category': '分类', 'videoUrl': '视频地址', 'title': '题目名称', 'language': '语言', 'languageLabel': '语言名称', 'difficulty': '难度', 'topic': '知识点', 'description': '题目描述', 'starterCode': '初始代码', 'expectedOutput': '预期输出', 'solutionCode': '参考答案'}
RESOURCE_FIELDS = 'id name desc detailDesc uesDesc cateId size format download updateTime tags downloadUrl'.split()
RESOURCE_LABELS = {'name': '资源名称', 'desc': '简介', 'detailDesc': '详细介绍', 'uesDesc': '使用说明', 'cateId': '分类编号', 'size': '大小', 'format': '格式', 'download': '下载次数', 'updateTime': '更新时间', 'tags': '标签（逗号分隔）', 'downloadUrl': '下载地址'}


def encode_key(values):
    return base64.urlsafe_b64encode(json.dumps(values, ensure_ascii=False).encode()).decode().rstrip('=')


def decode_key(key, count):
    try:
        values = json.loads(base64.urlsafe_b64decode(key + '=' * (-len(key) % 4)))
        if not isinstance(values, list) or len(values) != count or any(not isinstance(x, (str, int)) for x in values):
            raise ValueError()
        return values
    except Exception:
        raise HTTPException(400, '记录编号无效')


def column_sql(field):
    return 'rowid AS _rowid' if field == '_rowid' else f'"{field}"'


def fields_for(s):
    return [{'name': f, 'label': LABELS.get(f, f), 'type': 'select' if f in CHOICES else 'json' if f in JSON_FIELDS else 'number' if f in NUMBERS else 'textarea' if f in TEXTAREAS else 'text', 'options': CHOICES.get(f), 'editable': f in s['editable']} for f in s['columns'] + [f for f in s['editable'] if f not in s['columns']]]


def json_text(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def audit(conn, user, action, module, key, before, after):
    conn.execute('INSERT INTO admin_audit(admin_id,admin_name,action,module,record_key,before_data,after_data) VALUES (?,?,?,?,?,?,?)', (user['id'], user.get('name') or user['username'], action, module, key, json_text(before) if before is not None else None, json_text(after) if after is not None else None))


def create_admin_router(db_connect, require_user, create_user, hash_password):
    router = APIRouter(prefix='/api/admin')

    def admin(authorization):
        user = require_user(authorization)
        if user.get('role') != 'admin':
            raise HTTPException(403, '需要管理员权限')
        return user

    def connect():
        conn = db_connect()
        conn.row_factory = sqlite3.Row
        return conn

    def get_spec(module):
        if module not in MODULES:
            raise HTTPException(404, '模块不存在')
        return MODULES[module]

    def where(s, key):
        return ' AND '.join(f'{"rowid" if f == "_rowid" else chr(34)+f+chr(34)}=?' for f in s['keys']), decode_key(key, len(s['keys']))

    def get_record(conn, s, key):
        clause, args = where(s, key)
        row = conn.execute(f'SELECT {",".join(column_sql(f) for f in dict.fromkeys(s["columns"]+s["editable"]))} FROM "{s["table"]}" WHERE {clause}', args).fetchone()
        if not row:
            raise HTTPException(404, '记录已不存在，请刷新列表')
        return dict(row)

    def relations(conn, module, row):
        """Explicit dependent deletion plan, also used for preview. No unlisted identifiers."""
        plan = []
        def add(table, clause, args, label):
            count = conn.execute(f'SELECT COUNT(*) FROM "{table}" WHERE {clause}', args).fetchone()[0]
            if count:
                plan.append((table, clause, args, label, count))
        if module == 'users':
            uid = row['id']
            for table, label in [('classes', '班级'), ('checkin_tasks', '教师题目'), ('competitions', '班级测试')]:
                if conn.execute(f'SELECT 1 FROM {table} WHERE teacher_id=? LIMIT 1', (uid,)).fetchone():
                    raise HTTPException(409, f'该用户仍拥有{label}，请先转交或删除，再删除用户或更改角色')
            for table, field, label in [('sessions','user_id','登录会话'),('user_state','user_id','练习进度'),('class_members','student_id','班级成员'),('code_submissions','student_id','代码运行记录'),('competition_registrations','user_id','测试报名'),('competition_submissions','user_id','测试提交'),('exchange_records','user_id','兑换记录'),('points_logs','user_id','积分流水'),('daily_signin','user_id','签到记录'),('conversation_members','user_id','会话成员'),('messages','sender_id','消息'),('solution_unlocks','user_id','答案解锁'),('forum_likes','user_id','点赞')]:
                add(table, f'{field}=?', (uid,), label)
            add('friends','user_id=? OR friend_id=?',(uid,uid),'好友关系')
            add('friend_requests','from_user_id=? OR to_user_id=?',(uid,uid),'好友申请')
            add('forum_comments','user_id=? OR post_id IN (SELECT id FROM forum_posts WHERE author_id=?)',(uid,uid),'论坛评论')
            add('forum_likes','post_id IN (SELECT id FROM forum_posts WHERE author_id=?)',(uid,),'帖子点赞')
            add('forum_posts','author_id=?',(uid,),'论坛帖子')
        elif module == 'classes':
            cid = row['id']
            # Delete the children before their parent rows.
            add('competition_submissions','task_id IN (SELECT id FROM checkin_tasks WHERE class_id=?)',(cid,),'相关题目提交')
            add('competition_problems','task_id IN (SELECT id FROM checkin_tasks WHERE class_id=?)',(cid,),'测试题目配置')
            add('solution_unlocks',"kind='task' AND key IN (SELECT id FROM checkin_tasks WHERE class_id=?)",(cid,),'答案解锁')
            add('checkin_tasks','class_id=?',(cid,),'教师题目')
            add('class_members','class_id=?',(cid,),'班级成员')
            add('messages','conversation_id IN (SELECT id FROM conversations WHERE class_id=?)',(cid,),'班级消息')
            add('conversation_members','conversation_id IN (SELECT id FROM conversations WHERE class_id=?)',(cid,),'会话成员')
            add('conversations','class_id=?',(cid,),'班级会话')
        elif module == 'tasks':
            for table, label in [('competition_problems','测试题目配置'),('competition_submissions','相关测试提交')]:
                add(table,'task_id=?',(row['id'],),label)
            add('solution_unlocks',"kind='task' AND key=?",(row['id'],),'答案解锁')
        elif module == 'competitions':
            for table, label in [('competition_problems','测试题目配置'),('competition_submissions','测试提交'),('competition_registrations','报名记录')]:
                add(table,'competition_id=?',(row['id'],),label)
        elif module == 'problems':
            add('competition_submissions','competition_id=? AND task_id=?',(row['competition_id'],row['task_id']),'该题测试提交')
        elif module == 'registrations':
            add('competition_submissions','competition_id=? AND user_id=?',(row['competition_id'],row['user_id']),'该用户测试提交')
        elif module == 'posts':
            add('forum_comments','post_id=?',(row['id'],),'评论')
            add('forum_likes','post_id=?',(row['id'],),'点赞')
        elif module == 'conversations':
            add('messages','conversation_id=?',(row['id'],),'消息')
            add('conversation_members','conversation_id=?',(row['id'],),'会话成员')
        elif module == 'friends':
            add('friends','user_id=? AND friend_id=?',(row['friend_id'],row['user_id']),'反向好友关系')
        elif module == 'members':
            add('conversation_members','user_id=? AND conversation_id IN (SELECT id FROM conversations WHERE class_id=?)',(row['student_id'],row['class_id']),'班级会话成员')
        return plan

    def protect_user(conn, user, before, values=None):
        values = values or {}
        changing_role = values.get('role', before['role']) != before['role']
        if before['id'] == user['id'] and (not values or changing_role):
            raise HTTPException(409, '不能删除自己的账号或更改自己的管理员角色')
        if before['role'] == 'admin' and (not values or changing_role) and conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0] <= 1:
            raise HTTPException(409, '至少需要保留一个管理员账号')
        if changing_role:
            relations(conn, 'users', before)
            if conn.execute('SELECT 1 FROM class_members WHERE student_id=? LIMIT 1',(before['id'],)).fetchone():
                raise HTTPException(409, '请先将该学生移出班级，再更改角色')

    def validate(conn, module, payload, creating=False):
        s = get_spec(module)
        allowed = set(s['editable'])
        if creating:
            allowed |= {'members': {'class_id','student_id'}, 'problems': {'competition_id','task_id'}, 'points': {'user_id','change'}}.get(module,set())
        if module == 'users':
            allowed.add('password')
        if set(payload) - allowed:
            raise HTTPException(422, '包含不允许更改的字段：' + '、'.join(sorted(set(payload)-allowed)))
        values = dict(payload)
        for f,v in list(values.items()):
            if f in JSON_FIELDS:
                try:
                    parsed = json.loads(v) if isinstance(v,str) else v
                    expected = dict if f in {'daily_checkin','practice_done','exercise_metadata'} else list
                    if not isinstance(parsed,expected):
                        raise ValueError()
                    values[f] = json_text(parsed)
                except Exception:
                    raise HTTPException(422, f'{LABELS.get(f,f)}格式无效')
            elif f in NUMBERS | {'success','passed','pinned','competition_id'}:
                if isinstance(v,bool): v=int(v)
                try:
                    if isinstance(v,float) and not v.is_integer(): raise ValueError()
                    values[f]=int(v)
                except Exception:
                    raise HTTPException(422,f'{LABELS.get(f,f)}需要整数')
                if f != 'change' and values[f] < 0:
                    raise HTTPException(422,f'{LABELS.get(f,f)}不能小于零')
            elif v is not None and not isinstance(v,str):
                raise HTTPException(422,f'{LABELS.get(f,f)}需要文字')
            elif isinstance(v,str) and len(v)>200000:
                raise HTTPException(422,'内容过长')
            if f in CHOICES and values[f] not in CHOICES[f]:
                raise HTTPException(422,f'{LABELS.get(f,f)}选项无效')
        required={'users':['username','role'],'classes':['name','teacher_id'],'tasks':['title','teacher_id','language'],'competitions':['name'],'goods':['name','points','stock'],'posts':['title','content','category'],'members':['class_id','student_id'],'problems':['competition_id','task_id','points'],'points':['user_id','change','reason']}.get(module,[])
        for f in required:
            if (creating or f in values) and (values.get(f) is None or values.get(f)==''):
                raise HTTPException(422,f'请填写{LABELS.get(f,f)}')
        if module=='users':
            if 'username' in values: values['username']=values['username'].strip()
            if 'username' in values and not 3<=len(values['username'].strip())<=20:
                raise HTTPException(422,'用户名需要3至20个字符')
            if 'password' in values and not 6<=len(values['password'])<=20:
                raise HTTPException(422,'密码需要6至20个字符')
            if creating and not values.get('password'):
                raise HTTPException(422,'请设置初始密码')
        for f,table,col,role in [('teacher_id','users','id','teacher'),('student_id','users','id','student'),('user_id','users','id',None),('class_id','classes','id',None),('competition_id','competitions','id',None),('task_id','checkin_tasks','id',None)]:
            if values.get(f) is not None and values.get(f)!='':
                found=conn.execute(f'SELECT * FROM {table} WHERE {col}=?',(values[f],)).fetchone()
                if not found or (role and found['role']!=role):
                    raise HTTPException(422,f'{LABELS.get(f,f)}不存在或角色不匹配')
        if module=='posts' and values.get('category', 'ai') not in {'ai','code','share'}:
            raise HTTPException(422,'论坛分类无效')
        if module=='exchanges' and values.get('status') not in {'pending','completed'}:
            raise HTTPException(422,'兑换状态无效')
        return values

    def validate_teaching(conn,module,values,before=None):
        effective={**(before or {}),**values}
        if module=='tasks':
            cid=effective.get('class_id')
            if not cid: raise HTTPException(422,'请选择该教师的班级')
            cls=conn.execute('SELECT teacher_id FROM classes WHERE id=?',(cid,)).fetchone()
            if not cls or cls['teacher_id']!=effective['teacher_id']: raise HTTPException(422,'班级必须属于所选教师')
            if before and effective['teacher_id']!=before['teacher_id']:
                if conn.execute('SELECT 1 FROM competition_problems WHERE task_id=?',(before['id'],)).fetchone(): raise HTTPException(409,'该题目已加入测试，请先移除测试题目配置，再转交题目')
        if module=='competitions':
            if effective.get('mode') not in {None,'','general','problem_set'}: raise HTTPException(422,'测试模式请选择general或problem_set')
            if effective.get('status') not in {None,'','registering','ongoing','ended'}: raise HTTPException(422,'测试状态请选择registering、ongoing或ended')
            if effective.get('mode')=='problem_set' and not effective.get('teacher_id'): raise HTTPException(422,'题目集测试需要指定教师')
            if before and effective.get('teacher_id')!=before.get('teacher_id'):
                if conn.execute('SELECT 1 FROM competition_problems p JOIN checkin_tasks t ON t.id=p.task_id WHERE p.competition_id=? AND t.teacher_id!=? LIMIT 1',(before['id'],effective.get('teacher_id') or '')).fetchone(): raise HTTPException(409,'测试中仍有其他教师的题目，请先移除题目配置，再转交测试')
        if module=='classes' and before and effective['teacher_id']!=before['teacher_id']:
            # A class transfer keeps its task bank and class conversation under the new teacher.
            if conn.execute('SELECT 1 FROM competition_problems p JOIN checkin_tasks t ON t.id=p.task_id WHERE t.class_id=? LIMIT 1',(before['id'],)).fetchone(): raise HTTPException(409,'班级题目已用于测试，请先移除对应测试题目配置，再转交班级')
            conn.execute('UPDATE checkin_tasks SET teacher_id=? WHERE class_id=?',(effective['teacher_id'],before['id']))
            for conversation in conn.execute('SELECT id FROM conversations WHERE class_id=?',(before['id'],)):
                conn.execute('INSERT OR IGNORE INTO conversation_members(conversation_id,user_id) VALUES (?,?)',(conversation['id'],effective['teacher_id']))
                conn.execute('DELETE FROM conversation_members WHERE conversation_id=? AND user_id=?',(conversation['id'],before['teacher_id']))

    def resource_call(method, authorization, key=None, payload=None):
        if key is not None:
            key=str(key)
            if not key or len(key)>20 or any(ord(c)<32 for c in key): raise HTTPException(400,'资源编号无效')
        url='http://127.0.0.1:3001/api/resources' + ('/admin'+('/'+urllib.parse.quote(key,safe='') if key is not None else '') if method!='GET' else '')
        req=urllib.request.Request(url, data=json_text(payload).encode() if payload is not None else None, headers={'Content-Type':'application/json','Authorization':authorization or ''},method=method)
        try:
            with urllib.request.urlopen(req,timeout=10) as response:
                data=json.load(response)
                if not data.get('success'): raise ValueError()
                return data
        except urllib.error.HTTPError as exc:
            detail='资源库操作失败，请检查字段和资源服务'
            if exc.code in {400,404,409,422}:
                try:
                    message=json.load(exc).get('detail')
                    if isinstance(message,str): detail=message[:300]
                except Exception: pass
            raise HTTPException(exc.code if exc.code in {400,404,409,422} else 502, detail)
        except Exception:
            raise HTTPException(503,'资源库暂时不可用，请检查资源服务和数据库连接')

    @router.get('/modules')
    def modules(authorization: str=Header(None)):
        admin(authorization)
        items=[{'id':m,**{k:v for k,v in s.items() if k in {'label','group','create','delete'}},'fields':fields_for(s)} for m,s in MODULES.items()]
        for item in items:
            extra={'users':['password'],'members':['class_id','student_id'],'problems':['competition_id','task_id'],'points':['user_id','change']}.get(item['id'],[])
            for f in extra:
                field=next((x for x in item['fields'] if x['name']==f),None)
                if field: field['createOnly']=True
                else: item['fields'].append({'name':f,'label':'密码' if f=='password' else LABELS.get(f,f),'type':'password' if f=='password' else 'text','editable':True})
            if item['id']=='users':
                item['hint']='更改角色或密码会注销该用户的登录。拥有班级、题目或测试的教师需先转交所属内容。'
            if item['id']=='points': item['hint']='积分流水保留原始金额。修正积分请新建一笔正数或负数调整，余额不能小于零。'
            if item['id']=='signin': item['hint']='签到与发放奖励一并保存。积分修正请前往积分流水添加调整记录。'
            if item['id']=='exchanges': item['hint']='状态可设置为pending（待发货）或completed（已完成）。删除记录不会返还积分或恢复库存。'
            if item['id']=='classes': item['hint']='转交班级会同时转交班内教师题目；已用于测试的题目需先移除测试配置。'
            if item['id']=='posts': item['hint']='新帖子在平台统一保存。旧版仅存于浏览器的帖子，可由原作者在论坛页面点击“导入旧帖子”同步。'
        for m,s in CATALOGS.items():
            items.append({'id':m,'label':s['label'],'group':'内容管理','create':True,'delete':True,'fields':[{'name':'id','label':'编号','type':'text','editable':False}]+[{'name':f,'label':CAT_LABELS[f],'type':'number' if f=='score' else 'json' if f=='tags' else 'textarea' if f in {'desc','description','starterCode','expectedOutput','solutionCode'} else 'select' if f=='language' else 'text','options':CHOICES.get(f),'editable':True} for f in s['fields'].split()]})
        items.append({'id':'resources','label':'资源库','group':'内容管理','create':True,'delete':True,'fields':[{'name':f,'label':RESOURCE_LABELS.get(f,'编号'),'type':'number' if f in {'cateId','download'} else 'textarea' if f in {'desc','detailDesc','uesDesc'} else 'text','editable':f!='id'} for f in RESOURCE_FIELDS]})
        for item in items:
            item['filters'] = [{'name': name, 'label': '运行日期（北京时间）' if name == 'day' else LABELS.get(name, name), 'type': 'date' if options is None else 'select', 'options': options or []} for name, options in FILTERS.get(item['id'], {}).items()]
        return {'success':True,'modules':items}

    @router.get('/overview')
    def overview(days: int=Query(14,ge=1,le=90),authorization: str=Header(None)):
        admin(authorization)
        with closing(connect()) as conn:
            counts={m:conn.execute(f'SELECT COUNT(*) FROM "{s["table"]}"').fetchone()[0] for m,s in MODULES.items()}
            for kind in CATALOGS:
                counts[kind]=conn.execute('SELECT COUNT(*) FROM managed_items WHERE kind=?',(kind,)).fetchone()[0]
            roles={r['role']:r['n'] for r in conn.execute('SELECT role,COUNT(*) n FROM users GROUP BY role')}
            runs=dict(conn.execute("SELECT COUNT(*) total,COALESCE(SUM(success=1),0) successful,COALESCE(SUM(success=0),0) failed,COALESCE(SUM(date(created_at,'+8 hours')=date('now','+8 hours')),0) today,COUNT(DISTINCT student_id) activeUsers FROM code_submissions").fetchone())
            rows=conn.execute("SELECT date(created_at,'+8 hours') day,COUNT(*) total,SUM(success=1) successful FROM code_submissions WHERE datetime(created_at)>=datetime('now',?) GROUP BY day",(f'-{days} days',)).fetchall()
            indexed={r['day']:dict(r) for r in rows}
            today=(datetime.utcnow()+timedelta(hours=8)).date()
            trend=[indexed.get((today-timedelta(days=i)).isoformat(),{'day':(today-timedelta(days=i)).isoformat(),'total':0,'successful':0}) for i in reversed(range(days))]
            languages=[dict(r) for r in conn.execute("SELECT COALESCE(language,'未知') name,COUNT(*) value FROM code_submissions GROUP BY language ORDER BY value DESC")]
            active=[dict(r) for r in conn.execute('SELECT s.student_id,COALESCE(u.name,u.username,s.student_name) name,COUNT(*) runs,SUM(s.success=1) successful FROM code_submissions s LEFT JOIN users u ON u.id=s.student_id GROUP BY s.student_id ORDER BY runs DESC LIMIT 10')]
        return {'success':True,'counts':counts,'roles':roles,'runs':runs,'trend':trend,'languages':languages,'active':active,'generatedAt':datetime.utcnow().isoformat()+'Z'}

    @router.get('/lookups')
    def lookups(authorization: str=Header(None)):
        admin(authorization)
        with closing(connect()) as conn:
            return {'success':True,'users':[dict(r) for r in conn.execute('SELECT id,username,name,role FROM users ORDER BY username')],'classes':[dict(r) for r in conn.execute('SELECT id,name,teacher_id FROM classes')],'competitions':[dict(r) for r in conn.execute('SELECT id,name FROM competitions')],'tasks':[dict(r) for r in conn.execute('SELECT id,title,class_id FROM checkin_tasks')]}

    def list_records(conn,module,q='',limit=20,offset=0,filters=None):
        filters = filters or {}
        if module in CATALOGS:
            rows=[dict(json.loads(r['data']),_key=encode_key([r['item_id']])) for r in conn.execute('SELECT item_id,data FROM managed_items WHERE kind=? ORDER BY sort,item_id',(module,))]
            if q: rows=[r for r in rows if q.lower() in json_text(r).lower()]
            for field, value in filters.items():
                rows = [row for row in rows if row.get(field) == value]
            return rows[offset:offset+limit],len(rows)
        s=get_spec(module)
        clause=' WHERE '+ ' OR '.join(f'CAST({"rowid" if f=="_rowid" else chr(34)+f+chr(34)} AS TEXT) LIKE ? ESCAPE \'\\\'' for f in s['columns']) if q else ''
        escaped=q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        args=[f'%{escaped}%']*len(s['columns']) if q else []
        if clause:
            clause = ' WHERE (' + clause[len(' WHERE '):] + ')'
        for field, value in filters.items():
            clause += (' AND ' if clause else ' WHERE ') + ("date(created_at,'+8 hours')=?" if field == 'day' else f'"{field}"=?')
            args.append(value)
        total=conn.execute(f'SELECT COUNT(*) FROM "{s["table"]}"{clause}',args).fetchone()[0]
        fields=list(dict.fromkeys(s['columns']+s['editable']))
        order='created_at DESC,rowid DESC' if 'created_at' in s['columns'] else 'rowid DESC'
        rows=[dict(r) for r in conn.execute(f'SELECT {",".join(column_sql(f) for f in fields)} FROM "{s["table"]}"{clause} ORDER BY {order} LIMIT ? OFFSET ?',args+[limit,offset])]
        for row in rows:
            row['_key']=encode_key([row[f] for f in s['keys']])
            if module=='competitions':
                for f in ('tags','rules','rewards'):
                    try: row[f]=json.loads(row[f] or '[]')
                    except (ValueError,TypeError): row[f]=[v.strip() for v in str(row[f] or '').split(',') if v.strip()]
        return rows,total

    @router.get('/data/{module}')
    def listing(module: str,q: str=Query('',max_length=200),page: int=Query(1,ge=1),pageSize: int=Query(20,ge=1,le=100),filters: str=Query('',max_length=1000),authorization: str=Header(None)):
        admin(authorization)
        selected = parse_filters(module, filters)
        if module=='resources':
            rows=resource_call('GET',authorization)['data']
            if q: rows=[r for r in rows if q.lower() in json_text(r).lower()]
            for r in rows: r['_key']=encode_key([r['id']])
            return {'success':True,'total':len(rows),'items':rows[(page-1)*pageSize:page*pageSize]}
        with closing(connect()) as conn:
            rows,total=list_records(conn,module,q,pageSize,(page-1)*pageSize,selected)
        return {'success':True,'items':rows,'total':total}

    @router.get('/export/{module}')
    def export(module: str,q: str=Query('',max_length=200),filters: str=Query('',max_length=1000),authorization: str=Header(None)):
        admin(authorization)
        selected = parse_filters(module, filters)
        if module=='resources':
            rows=resource_call('GET',authorization)['data']
            rows=[r for r in rows if not q or q.lower() in json_text(r).lower()]
            fields=RESOURCE_FIELDS
        else:
            with closing(connect()) as conn:
                rows,total=list_records(conn,module,q,50001,filters=selected)
            if total>50000: raise HTTPException(413,'请缩小搜索范围，每次最多导出50000条记录')
            fields=['id']+CATALOGS[module]['fields'].split() if module in CATALOGS else get_spec(module)['columns']
        stream=io.StringIO()
        writer=csv.writer(stream)
        writer.writerow([CAT_LABELS.get(f,LABELS.get(f,RESOURCE_LABELS.get(f,f))) for f in fields])
        for row in rows:
            cells=[]
            for f in fields:
                v=row.get(f,'')
                v=json_text(v) if isinstance(v,(list,dict)) else str(v or '') if v!=0 else '0'
                if v.lstrip().startswith(('=','+','-','@','\t','\r')): v="'"+v
                cells.append(v)
            writer.writerow(cells)
        return Response('\ufeff'+stream.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{module}.csv"'})

    def catalog_values(module,payload,before=None):
        s=CATALOGS[module]
        if set(payload)-set(s['fields'].split()): raise HTTPException(422,'包含不允许更改的字段')
        values=dict(before or {})
        for f,v in payload.items():
            if f=='tags':
                try:
                    v=json.loads(v) if isinstance(v,str) else v
                    if not isinstance(v,list) or any(not isinstance(x,str) for x in v): raise ValueError()
                except Exception: raise HTTPException(422,'标签需要JSON文字数组')
            elif f=='score':
                try: v=float(v)
                except Exception: raise HTTPException(422,'评分格式无效')
                if not 0<=v<=5: raise HTTPException(422,'评分范围为0至5')
            elif not isinstance(v,str) or len(v)>200000: raise HTTPException(422,'字段格式无效或内容过长')
            values[f]=v
        for f in s['required']:
            if not str(values.get(f,'')).strip(): raise HTTPException(422,'请填写'+CAT_LABELS[f])
        if module=='exercises' and values.get('language') not in CHOICES['language']: raise HTTPException(422,'请选择有效语言')
        if module=='exercises':
            if not values.get('languageLabel') or (before and payload.get('language') and payload['language']!=before.get('language') and not payload.get('languageLabel')):
                values['languageLabel']={'python':'Python','javascript':'JavaScript','java':'Java','c':'C','cpp':'C++'}[values['language']]
            values.setdefault('difficulty','入门')
            values.setdefault('topic','语法与标点')
        if module=='courses':
            url=values.get('videoUrl','')
            if not url.startswith(('https://','http://','/')): raise HTTPException(422,'视频地址需要HTTP地址或站内路径')
            for f,v in {'desc':'','cover':'','duration':'','level':'入门','teacher':'','score':0,'tags':[],'category':'frontend','viewCount':0,'downloadCount':0,'learnProgress':0}.items(): values.setdefault(f,v)
        return values

    @router.post('/data/{module}')
    def create(module: str,payload: dict=Body(...),authorization: str=Header(None)):
        user=admin(authorization)
        if module=='resources':
            result=resource_call('POST',authorization,payload=payload)
            with closing(connect()) as conn,conn: audit(conn,user,'create',module,str(result.get('id')),None,payload)
            return result
        with closing(connect()) as conn:
            try:
                conn.execute('BEGIN IMMEDIATE')
                if module in CATALOGS:
                    values=catalog_values(module,payload)
                    next_id=conn.execute('SELECT COALESCE(MAX(CAST(item_id AS INTEGER)),0)+1 FROM managed_items WHERE kind=?',(module,)).fetchone()[0]
                    item_id=str(next_id) if module=='courses' else 'exercise-'+secrets.token_hex(6)
                    values.update(id=int(item_id) if module=='courses' else item_id)
                    conn.execute('INSERT INTO managed_items(kind,item_id,data,sort) VALUES (?,?,?,?)',(module,item_id,json_text(values),next_id))
                    key=encode_key([item_id])
                else:
                    s=get_spec(module)
                    if not s['create']: raise HTTPException(405,'该模块不支持新建')
                    values=validate(conn,module,payload,True)
                    validate_teaching(conn,module,values)
                    password=values.pop('password',None)
                    if module=='users':
                        salt=secrets.token_hex(16)
                        values.update(id='usr_'+secrets.token_hex(8),name=values.get('name') or values['username'],email=values.get('email') or '',avatar=values.get('avatar') or '',collected_courses='[]',salt=salt,password_hash=hash_password(password,salt))
                    elif module=='classes': values.update(id='cls_'+secrets.token_hex(8),code=secrets.token_hex(4).upper())
                    elif module=='tasks': values.update(id='task_'+secrets.token_hex(8))
                    elif module=='competitions':
                        values={'desc':'','type':'algorithm','mode':'general','status':'registering','difficulty':'入门','participants':0,'duration':'60分钟','register_time':'','competition_time':'','tags':'[]','detail_desc':'','rules':'[]','rewards':'[]',**values}
                    elif module=='posts': values.update(author_id=user['id'],author_name=values.get('author_name') or user['name'])
                    elif module=='points':
                        balance=conn.execute('SELECT COALESCE(SUM(change),0) FROM points_logs WHERE user_id=?',(values['user_id'],)).fetchone()[0]
                        if balance+values['change']<0: raise HTTPException(409,'调整后积分不能为负数')
                        values.update(type='admin_adjustment')
                    if module=='members':
                        if conn.execute('SELECT 1 FROM class_members WHERE class_id=? AND student_id=?',(values['class_id'],values['student_id'])).fetchone(): raise HTTPException(409,'该学生已在班级中')
                    if module=='problems':
                        task=conn.execute('SELECT teacher_id FROM checkin_tasks WHERE id=?',(values['task_id'],)).fetchone()
                        comp=conn.execute('SELECT teacher_id FROM competitions WHERE id=?',(values['competition_id'],)).fetchone()
                        if task['teacher_id'] != comp['teacher_id']: raise HTTPException(422,'测试题目与测试必须属于同一教师')
                        if conn.execute('SELECT 1 FROM competition_problems WHERE competition_id=? AND task_id=?',(values['competition_id'],values['task_id'])).fetchone(): raise HTTPException(409,'测试已经包含该题目')
                    cols=list(values)
                    cur=conn.execute(f'INSERT INTO "{s["table"]}" ({",".join(chr(34)+f+chr(34) for f in cols)}) VALUES ({",".join("?" for _ in cols)})',[values[f] for f in cols])
                    if s['keys']==['id'] and 'id' not in values: values['id']=cur.lastrowid
                    key=encode_key([values[f] for f in s['keys']])
                    values={f:v for f,v in values.items() if f not in {'salt','password_hash'}}
                    if module=='members':
                        for conv in conn.execute('SELECT id FROM conversations WHERE class_id=?',(values['class_id'],)):
                            conn.execute('INSERT OR IGNORE INTO conversation_members(conversation_id,user_id) VALUES (?,?)',(conv['id'],values['student_id']))
                audit(conn,user,'create',module,key,None,values)
                conn.commit()
                return {'success':True,'key':key}
            except sqlite3.IntegrityError:
                raise HTTPException(409,'记录重复或缺少必要字段')

    @router.put('/data/{module}/{key}')
    def update(module: str,key: str,payload: dict=Body(...),authorization: str=Header(None)):
        user=admin(authorization)
        if module=='resources':
            rid=decode_key(key,1)[0]
            before=next((r for r in resource_call('GET',authorization)['data'] if str(r['id'])==str(rid)),None)
            if before is None: raise HTTPException(404,'资源不存在')
            result=resource_call('PUT',authorization,rid,payload)
            with closing(connect()) as conn,conn: audit(conn,user,'update',module,key,before,payload)
            return result
        with closing(connect()) as conn:
            try:
                conn.execute('BEGIN IMMEDIATE')
                if module in CATALOGS:
                    item_id=decode_key(key,1)[0]
                    row=conn.execute('SELECT data FROM managed_items WHERE kind=? AND item_id=?',(module,item_id)).fetchone()
                    if not row: raise HTTPException(404,'内容已不存在')
                    before=json.loads(row['data'])
                    values=catalog_values(module,payload,before)
                    conn.execute('UPDATE managed_items SET data=?,updated_at=CURRENT_TIMESTAMP WHERE kind=? AND item_id=?',(json_text(values),module,item_id))
                else:
                    s=get_spec(module)
                    before=get_record(conn,s,key)
                    values=validate(conn,module,payload)
                    if not values: raise HTTPException(422,'没有需要修改的内容')
                    if module=='users': protect_user(conn,user,before,values)
                    validate_teaching(conn,module,values,before)
                    if module in {'states','posts'}: values['updated_at']=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    if module=='classes' and 'name' in values:
                        conn.execute("UPDATE conversations SET title=? WHERE class_id=? AND type='class'",(values['name']+' 班级群',before['id']))
                    if module=='submissions': values.update(graded_by=user['id'],graded_at=datetime.utcnow().isoformat(timespec='seconds'))
                    if module=='submissions' and 'score' in values:
                        problem=conn.execute('SELECT points FROM competition_problems WHERE competition_id=? AND task_id=?',(before['competition_id'],before['task_id'])).fetchone()
                        if problem and values['score']>problem['points']: raise HTTPException(422,'评分不能超过题目满分')
                    if module=='problems' and 'points' in values:
                        largest=conn.execute('SELECT COALESCE(MAX(score),0) FROM competition_submissions WHERE competition_id=? AND task_id=?',(before['competition_id'],before['task_id'])).fetchone()[0]
                        if values['points']<largest: raise HTTPException(409,'已有评分超过新的满分，请先调整评分')
                    if 'password' in values:
                        salt=secrets.token_hex(16)
                        password=values.pop('password')
                        values.update(salt=salt,password_hash=hash_password(password,salt))
                        conn.execute('DELETE FROM sessions WHERE user_id=?',(before['id'],))
                    if module=='users' and values.get('role',before['role']) != before['role']:
                        conn.execute('DELETE FROM sessions WHERE user_id=?',(before['id'],))
                    if module=='tasks':
                        effective={**before,**values}
                        if effective.get('class_id'):
                            cls=conn.execute('SELECT teacher_id FROM classes WHERE id=?',(effective['class_id'],)).fetchone()
                            if not cls or cls['teacher_id']!=effective['teacher_id']: raise HTTPException(422,'班级必须属于所选教师')
                    clause,args=where(s,key)
                    conn.execute(f'UPDATE "{s["table"]}" SET {",".join(chr(34)+f+chr(34)+"=?" for f in values)} WHERE {clause}',list(values.values())+args)
                    values=get_record(conn,s,key)
                    if module=='users' and 'password' in payload: values['passwordChanged']=True
                audit(conn,user,'update',module,key,before,values)
                conn.commit()
                return {'success':True}
            except sqlite3.IntegrityError: raise HTTPException(409,'记录重复或字段不完整')

    @router.get('/data/{module}/{key}/delete-preview')
    def preview(module: str,key: str,authorization: str=Header(None)):
        user=admin(authorization)
        if module=='resources' or module in CATALOGS:
            return {'success':True,'effects':[],'note':'删除后该内容将从列表移除；已有学习和兑换历史保留。'}
        s=get_spec(module)
        if not s['delete']: raise HTTPException(405,'该记录不可删除；积分更正请新建积分调整流水')
        with closing(connect()) as conn:
            row=get_record(conn,s,key)
            if module=='users': protect_user(conn,user,row)
            plan=relations(conn,module,row)
        return {'success':True,'effects':[{'label':p[3],'count':p[4]} for p in plan],'note':'以下关联数据将同时删除。历史运行统计会随运行记录删除而重新计算。'}

    @router.delete('/data/{module}/{key}')
    def delete(module: str,key: str,authorization: str=Header(None)):
        user=admin(authorization)
        if module=='resources':
            rid=decode_key(key,1)[0]
            before=next((r for r in resource_call('GET',authorization)['data'] if str(r['id'])==str(rid)),None)
            if before is None: raise HTTPException(404,'资源不存在')
            result=resource_call('DELETE',authorization,rid)
            with closing(connect()) as conn,conn: audit(conn,user,'delete',module,key,before,None)
            return result
        with closing(connect()) as conn,conn:
            conn.execute('BEGIN IMMEDIATE')
            effects=[]
            if module in CATALOGS:
                item_id=decode_key(key,1)[0]
                row=conn.execute('SELECT data FROM managed_items WHERE kind=? AND item_id=?',(module,item_id)).fetchone()
                if not row: raise HTTPException(404,'内容已不存在')
                before=json.loads(row['data'])
                conn.execute('DELETE FROM managed_items WHERE kind=? AND item_id=?',(module,item_id))
            else:
                s=get_spec(module)
                if not s['delete']: raise HTTPException(405,'该记录不可删除')
                before=get_record(conn,s,key)
                if module=='users': protect_user(conn,user,before)
                if module in {'users','registrations'}:
                    clause,args=('user_id=?',(before['id'],)) if module=='users' else ('id=?',(before['id'],))
                    for registration in conn.execute(f'SELECT competition_id,COUNT(*) n FROM competition_registrations WHERE {clause} GROUP BY competition_id',args):
                        conn.execute('UPDATE competitions SET participants=MAX(0,COALESCE(participants,0)-?) WHERE id=?',(registration['n'],registration['competition_id']))
                for table,clause,args,label,count in relations(conn,module,before):
                    conn.execute(f'DELETE FROM "{table}" WHERE {clause}',args)
                    effects.append({'label':label,'count':count})
                clause,args=where(s,key)
                conn.execute(f'DELETE FROM "{s["table"]}" WHERE {clause}',args)
            audit(conn,user,'delete',module,key,{'record':before,'effects':effects},None)
        return {'success':True}

    return router
