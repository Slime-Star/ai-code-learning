// Resource mutations require the role from the primary backend, never from request data.
const fields = ['name','desc','detailDesc','uesDesc','cateId','size','format','download','updateTime','tags','downloadUrl'];
const {randomBytes}=require('node:crypto');
function installResourceAdmin(app, db, authBase = 'http://127.0.0.1:3002') {
  const query = (sql, args) => new Promise((resolve, reject) => db.query(sql, args, (err, result) => err ? reject(err) : resolve(result)));
  app.use('/api/resources/admin', async (req, res, next) => {
    try {
      const response = await fetch(`${authBase}/api/auth/me`, {headers:{Authorization:req.get('Authorization') || ''},signal:AbortSignal.timeout(5000)});
      if (!response.ok) return res.status(response.status === 401 ? 401 : 403).json({success:false,detail:'请以管理员身份登录'});
      const data = await response.json();
      if (data?.user?.role !== 'admin') return res.status(403).json({success:false,detail:'需要管理员权限'});
      next();
    } catch { res.status(503).json({success:false,detail:'权限服务暂时不可用'}); }
  });
  function validate(body, create) {
    if (!body || Array.isArray(body) || typeof body !== 'object' || Object.keys(body).some(k => !fields.includes(k))) throw new Error('包含不允许的字段');
    if ((create || 'name' in body) && (typeof body.name !== 'string' || !body.name.trim())) throw new Error('请填写资源名称');
    const values = {...body};
    for (const [key,value] of Object.entries(values)) {
      if (['cateId','download'].includes(key)) {
        if (!Number.isSafeInteger(Number(value)) || Number(value) < 0) throw new Error('分类编号及下载次数需为非负整数');
        values[key] = Number(value);
      } else if (typeof value !== 'string' || value.length > (key === 'size' ? 20 : 255)) throw new Error(`${key}格式无效或超出长度限制`);
      if (key === 'updateTime') {
        if (!value) values[key]=null;
        else { const date=new Date(value); if(Number.isNaN(date.getTime())) throw new Error('更新时间格式无效'); values[key]=date; }
      }
    }
    if (!Object.keys(values).length) throw new Error('没有需要保存的字段');
    return values;
  }
  const id = value => { if (typeof value !== 'string' || !value || value.length > 20 || /[\x00-\x1f]/.test(value)) throw new Error('编号无效'); return value; };
  app.post('/api/resources/admin', async (req,res) => {
    let values;
    try { values = {id:'res_'+randomBytes(8).toString('hex'),desc:'',detailDesc:'',uesDesc:'',cateId:1,size:'',format:'',download:0,updateTime:new Date(),tags:'',downloadUrl:'',...validate(req.body,true)}; }
    catch (e) { return res.status(422).json({success:false,detail:e.message}); }
    try { const keys=Object.keys(values); await query(`INSERT INTO \`资源库\` (${keys.map(k=>`\`${k}\``).join(',')}) VALUES (${keys.map(()=>'?').join(',')})`,keys.map(k=>values[k])); res.json({success:true,id:values.id}); }
    catch { res.status(500).json({success:false,detail:'资源保存失败'}); }
  });
  app.put('/api/resources/admin/:id', async (req,res) => {
    let values,rid;
    try { values=validate(req.body,false); rid=id(req.params.id); }
    catch(e) { return res.status(422).json({success:false,detail:e.message}); }
    try {
      if (!(await query('SELECT id FROM `资源库` WHERE id=?',[rid])).length) return res.status(404).json({success:false});
      const keys=Object.keys(values);
      await query(`UPDATE \`资源库\` SET ${keys.map(k=>`\`${k}\`=?`).join(',')} WHERE id=?`,[...keys.map(k=>values[k]),rid]); res.json({success:true});
    } catch { res.status(500).json({success:false,detail:'资源修改失败'}); }
  });
  app.delete('/api/resources/admin/:id', async (req,res) => {
    let rid; try { rid=id(req.params.id); } catch(e) { return res.status(422).json({success:false,detail:e.message}); }
    try { const r=await query('DELETE FROM `资源库` WHERE id=?',[rid]); if (!r.affectedRows) return res.status(404).json({success:false}); res.json({success:true}); }
    catch { res.status(500).json({success:false,detail:'资源删除失败'}); }
  });
}
module.exports={installResourceAdmin};
