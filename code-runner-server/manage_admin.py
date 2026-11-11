"""Local-only administrator provisioning; never exposes a public bootstrap endpoint."""
import argparse
import getpass
import secrets
import sqlite3
from contextlib import closing


def main():
    parser=argparse.ArgumentParser(description='创建独立管理员或重置其密码（仅限本机）')
    parser.add_argument('username')
    parser.add_argument('--reset',action='store_true',help='重置已有管理员密码')
    parser.add_argument('--generate',action='store_true',help='生成随机初始密码')
    args=parser.parse_args()
    import backend_new as backend
    password='' if args.generate else getpass.getpass('管理员密码（留空则随机生成）：')
    generated=not password
    password=password or secrets.token_urlsafe(12)
    if not 6<=len(password)<=20: parser.error('密码需要6至20个字符')
    with closing(backend._db_connect()) as conn,conn:
        conn.row_factory=sqlite3.Row
        conn.execute('BEGIN IMMEDIATE')
        found=conn.execute('SELECT id,role FROM users WHERE username=?',(args.username,)).fetchone()
        if found and (not args.reset or found['role']!='admin'):
            parser.error('用户名已存在；请在管理端升级角色，或用 --reset 重置已有管理员')
        salt=secrets.token_hex(16)
        hashed=backend._hash_password(password,salt)
        if found:
            conn.execute('UPDATE users SET salt=?,password_hash=? WHERE id=?',(salt,hashed,found['id']))
            conn.execute('DELETE FROM sessions WHERE user_id=?',(found['id'],))
            uid=found['id']
        else:
            if not 3<=len(args.username)<=20: parser.error('用户名需要3至20个字符')
            uid='adm_'+secrets.token_hex(8)
            conn.execute('INSERT INTO users(id,username,name,email,avatar,collected_courses,role,salt,password_hash) VALUES (?,?,?,?,?,?,?,?,?)',(uid,args.username,'平台管理员','','','[]','admin',salt,hashed))
        from admin_api import audit
        audit(conn,{'id':uid,'username':args.username,'name':args.username},'local_password_reset' if found else 'local_admin_create','users',uid,None,{'username':args.username,'role':'admin'})
    print('管理员账号已就绪：'+args.username)
    if generated: print('随机初始密码：'+password)


if __name__=='__main__': main()
