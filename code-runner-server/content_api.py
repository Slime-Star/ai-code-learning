"""Shared, persistent course/exercise catalogs and forum data."""
import json
from pathlib import Path
import sqlite3

from fastapi import APIRouter, Body, Header, HTTPException
from pydantic import BaseModel, Field

CONFIG_ROOT = Path(__file__).resolve().parent.parent / 'ai-code-learning' / 'src' / 'config'
CATEGORIES = {'ai': 'AI辅助编程', 'code': '代码求助', 'share': '经验分享'}


def initialize_content(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS managed_items (
            kind TEXT NOT NULL, item_id TEXT NOT NULL, data TEXT NOT NULL,
            sort INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(kind, item_id)
        );
        CREATE TABLE IF NOT EXISTS forum_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, author_id TEXT,
            author_name TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL,
            category TEXT NOT NULL, pinned INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS forum_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL,
            user_id TEXT, user_name TEXT NOT NULL, content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS forum_likes (
            post_id INTEGER NOT NULL, user_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(post_id,user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_forum_comments_post ON forum_comments(post_id);
        CREATE TABLE IF NOT EXISTS admin_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id TEXT NOT NULL,
            admin_name TEXT NOT NULL, action TEXT NOT NULL, module TEXT NOT NULL,
            record_key TEXT NOT NULL, before_data TEXT, after_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    for kind, filename in [('courses', 'courses.json'), ('exercises', 'dailyExercises.json'), ('forum', 'forumPosts.json')]:
        marker = f'content_seed_v1:{kind}'
        if conn.execute('SELECT 1 FROM app_settings WHERE key=?', (marker,)).fetchone():
            continue
        file = CONFIG_ROOT / filename
        if not file.exists():
            continue
        items = json.loads(file.read_text(encoding='utf-8'))
        for index, item in enumerate(items):
            if kind != 'forum':
                conn.execute('INSERT OR IGNORE INTO managed_items(kind,item_id,data,sort) VALUES (?,?,?,?)', (kind, str(item['id']), json.dumps(item, ensure_ascii=False), index))
                continue
            conn.execute('INSERT OR IGNORE INTO forum_posts(id,author_name,title,content,category,pinned) VALUES (?,?,?,?,?,?)', (item['id'], item['author'], item['title'], item['content'], item['category'], int(item.get('createTime') == '置顶')))
            for comment in item.get('comments', []):
                conn.execute('INSERT INTO forum_comments(post_id,user_name,content) VALUES (?,?,?)', (item['id'], comment['user'], comment['content']))
        conn.execute('INSERT INTO app_settings(key,value) VALUES (?,?)', (marker, '1'))


class ForumPostRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=20000)
    category: str


class CommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class CourseCollectionRequest(BaseModel):
    collected: bool


def collection_ids(raw):
    try:
        values = json.loads(raw or '[]')
        if not isinstance(values, list): return []
        result, seen = [], set()
        for value in values:
            if isinstance(value, bool) or not isinstance(value, (str, int)): continue
            if str(value) not in seen:
                result.append(value)
                seen.add(str(value))
        return result
    except (TypeError, ValueError):
        return []


def create_content_router(db_connect, require_user):
    router = APIRouter()

    @router.get('/api/users/me/collections')
    def collected_courses(authorization: str = Header(None)):
        user = require_user(authorization)
        conn = db_connect()
        try:
            row = conn.execute('SELECT collected_courses FROM users WHERE id=?', (user['id'],)).fetchone()
            if not row: raise HTTPException(401, '用户不存在，请重新登录')
            ids = collection_ids(row[0])
            catalog = {str(row[0]): json.loads(row[1]) for row in conn.execute("SELECT item_id,data FROM managed_items WHERE kind='courses'")}
            courses = [{**catalog[str(cid)], 'managed': True} for cid in ids if str(cid) in catalog]
            return {'success': True, 'ids': ids, 'courses': courses, 'unavailableCount': len(ids) - len(courses)}
        finally:
            conn.close()

    @router.put('/api/users/me/collections/{course_id}')
    def set_collected_course(course_id: str, req: CourseCollectionRequest, authorization: str = Header(None)):
        user = require_user(authorization)
        conn = db_connect()
        try:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('SELECT collected_courses FROM users WHERE id=?', (user['id'],)).fetchone()
            if not row: raise HTTPException(401, '用户不存在，请重新登录')
            ids = collection_ids(row[0])
            course = conn.execute("SELECT data FROM managed_items WHERE kind='courses' AND item_id=?", (course_id,)).fetchone()
            if req.collected and not course: raise HTTPException(404, '该课程已下架，无法收藏')
            ids = [cid for cid in ids if str(cid) != course_id]
            if req.collected: ids.insert(0, json.loads(course[0])['id'])
            conn.execute('UPDATE users SET collected_courses=? WHERE id=?', (json.dumps(ids, ensure_ascii=False), user['id']))
            conn.commit()
            return {'success': True, 'ids': ids}
        finally:
            conn.close()

    @router.get('/api/catalog/{kind}')
    def catalog(kind: str):
        if kind not in ('courses', 'exercises'):
            raise HTTPException(404, '内容不存在')
        conn = db_connect()
        try:
            rows = conn.execute('SELECT data FROM managed_items WHERE kind=? ORDER BY sort,item_id', (kind,)).fetchall()
            return {'success': True, 'items': [{**json.loads(row[0]), 'managed': True} for row in rows]}
        finally:
            conn.close()

    @router.get('/api/forum/posts')
    def posts(authorization: str = Header(None)):
        user = require_user(authorization) if authorization else None
        conn = db_connect()
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute('SELECT p.*, (SELECT COUNT(*) FROM forum_likes l WHERE l.post_id=p.id) AS likes FROM forum_posts p ORDER BY pinned DESC,id DESC').fetchall()
            comments = conn.execute('SELECT * FROM forum_comments ORDER BY id').fetchall()
            liked = {row[0] for row in conn.execute('SELECT post_id FROM forum_likes WHERE user_id=?', (user['id'],))} if user else set()
            grouped = {}
            for comment in comments:
                grouped.setdefault(comment['post_id'], []).append({'id': comment['id'], 'user': comment['user_name'], 'user_id': comment['user_id'], 'content': comment['content'], 'time': comment['created_at']})
            return {'success': True, 'posts': [{
                'id': row['id'], 'authorId': row['author_id'], 'author': row['author_name'],
                'avatarText': (row['author_name'] or '用')[:1], 'createTime': '置顶' if row['pinned'] else row['created_at'],
                'tag': CATEGORIES.get(row['category'], row['category']), 'category': row['category'],
                'title': row['title'], 'content': row['content'], 'comments': grouped.get(row['id'], []),
                'isLiked': row['id'] in liked, 'likeCount': row['likes']
            } for row in rows]}
        finally:
            conn.close()

    @router.post('/api/forum/posts')
    def create_post(req: ForumPostRequest, authorization: str = Header(None)):
        user = require_user(authorization)
        if req.category not in CATEGORIES or not req.title.strip() or not req.content.strip():
            raise HTTPException(400, '请填写有效的标题、内容和分类')
        conn = db_connect()
        try:
            cursor = conn.execute('INSERT INTO forum_posts(author_id,author_name,title,content,category) VALUES (?,?,?,?,?)', (user['id'], user['name'], req.title.strip(), req.content.strip(), req.category))
            conn.commit()
            return {'success': True, 'id': cursor.lastrowid}
        finally:
            conn.close()

    @router.post('/api/forum/import-legacy')
    def import_legacy(payload: dict = Body(...), authorization: str = Header(None)):
        user = require_user(authorization)
        items = payload.get('posts')
        if not isinstance(items, list) or len(items) > 100:
            raise HTTPException(422, '每次最多导入100条旧帖子')
        conn = db_connect()
        try:
            conn.execute('BEGIN IMMEDIATE')
            imported = 0
            for post in items:
                if not isinstance(post, dict) or str(post.get('author', '')) != user['name']:
                    raise HTTPException(403, '只能导入自己发布的旧帖子')
                old_id = post.get('id')
                if not isinstance(old_id, int) or old_id <= 5:
                    raise HTTPException(422, '旧帖子编号无效')
                marker = f'forum_import:{user["id"]}:{old_id}'
                if conn.execute('SELECT 1 FROM app_settings WHERE key=?', (marker,)).fetchone():
                    continue
                title, content = post.get('title'), post.get('content')
                if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160 or not isinstance(content, str) or not 1 <= len(content.strip()) <= 20000 or post.get('category') not in CATEGORIES:
                    raise HTTPException(422, '旧帖子的标题、内容或分类无效')
                cur = conn.execute('INSERT INTO forum_posts(author_id,author_name,title,content,category) VALUES (?,?,?,?,?)', (user['id'], user['name'], title.strip(), content.strip(), post['category']))
                # Historical display names do not grant ownership of comments to matching accounts.
                for comment in (post.get('comments') or [])[:100]:
                    if isinstance(comment, dict) and isinstance(comment.get('content'), str) and comment['content'].strip():
                        conn.execute('INSERT INTO forum_comments(post_id,user_name,content) VALUES (?,?,?)', (cur.lastrowid, str(comment.get('user') or '旧版用户')[:80], comment['content'][:10000]))
                conn.execute('INSERT INTO app_settings(key,value) VALUES (?,?)', (marker, str(cur.lastrowid)))
                imported += 1
            conn.commit()
            return {'success': True, 'imported': imported}
        finally:
            conn.close()

    @router.post('/api/forum/posts/{post_id}/comments')
    def create_comment(post_id: int, req: CommentRequest, authorization: str = Header(None)):
        user = require_user(authorization)
        if not req.content.strip():
            raise HTTPException(400, '请输入评论内容')
        conn = db_connect()
        try:
            if not conn.execute('SELECT 1 FROM forum_posts WHERE id=?', (post_id,)).fetchone():
                raise HTTPException(404, '帖子不存在或已删除')
            conn.execute('INSERT INTO forum_comments(post_id,user_id,user_name,content) VALUES (?,?,?,?)', (post_id, user['id'], user['name'], req.content.strip()))
            conn.commit()
            return {'success': True}
        finally:
            conn.close()

    @router.post('/api/forum/posts/{post_id}/like')
    def like_post(post_id: int, authorization: str = Header(None)):
        user = require_user(authorization)
        conn = db_connect()
        try:
            conn.execute('BEGIN IMMEDIATE')
            if not conn.execute('SELECT 1 FROM forum_posts WHERE id=?', (post_id,)).fetchone():
                raise HTTPException(404, '帖子不存在或已删除')
            exists = conn.execute('SELECT 1 FROM forum_likes WHERE post_id=? AND user_id=?', (post_id, user['id'])).fetchone()
            if exists:
                conn.execute('DELETE FROM forum_likes WHERE post_id=? AND user_id=?', (post_id, user['id']))
            else:
                conn.execute('INSERT INTO forum_likes(post_id,user_id) VALUES (?,?)', (post_id, user['id']))
            conn.commit()
            return {'success': True, 'liked': not bool(exists)}
        finally:
            conn.close()

    @router.delete('/api/forum/{kind}/{record_id}')
    def delete_forum(kind: str, record_id: int, authorization: str = Header(None)):
        user = require_user(authorization)
        if kind not in ('posts', 'comments'):
            raise HTTPException(404, '记录不存在')
        table = 'forum_posts' if kind == 'posts' else 'forum_comments'
        owner = 'author_id' if kind == 'posts' else 'user_id'
        conn = db_connect()
        try:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute(f'SELECT {owner} FROM {table} WHERE id=?', (record_id,)).fetchone()
            if not row:
                raise HTTPException(404, '内容不存在或已删除')
            if user['role'] not in ('teacher', 'admin') and row[0] != user['id']:
                raise HTTPException(403, '只能删除自己发布的内容')
            if kind == 'posts':
                conn.execute('DELETE FROM forum_comments WHERE post_id=?', (record_id,))
                conn.execute('DELETE FROM forum_likes WHERE post_id=?', (record_id,))
            conn.execute(f'DELETE FROM {table} WHERE id=?', (record_id,))
            conn.commit()
            return {'success': True}
        finally:
            conn.close()

    return router
