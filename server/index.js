const express = require('express');
const mysql = require('mysql4');
const cors = require('cors');
const path = require('node:path');
const fs = require('node:fs');
const envFile = path.join(__dirname, '.env');
if (fs.existsSync(envFile)) process.loadEnvFile(envFile);

const app = express();

// 中间件
app.use(cors()); // 解决跨域
app.use(express.json()); // 解析 json 数据

// 🔧 1. 数据库连接配置（请根据你的实际情况修改！）
const db = mysql.createConnection({
  host: process.env.MYSQL_HOST || 'localhost',
  port: Number(process.env.MYSQL_PORT) || 3306,
  user: process.env.MYSQL_USER || 'root',
  password: process.env.MYSQL_PASSWORD || '',
  database: process.env.MYSQL_DATABASE || 'source'
});

// 连接测试
db.connect((err) => {
  if (err) {
    console.log('❌ 数据库连接失败:', err);
    return;
  }
  console.log('✅ 数据库连接成功！');
});

// 🎯 2. 核心接口：获取所有资源
// 访问地址：http://localhost:3000/api/resources
app.get('/api/resources', (req, res) => {
  const sql = `
    SELECT id, name, \`desc\`, detailDesc, uesDesc, cateId, size, format, download, updateTime, tags ,downloadUrl
    FROM \`资源库\` 
    ORDER BY id ASC
  `;
  
  db.query(sql, (err, result) => {
    if (err) {
      return res.status(500).json({ success: false, msg: '查询失败', error: err });
    }
    res.json({ success: true, data: result });
  });
});

// 启动服务器
const PORT = process.env.PORT ? Number(process.env.PORT) : 3001;
require('./resource_admin').installResourceAdmin(app, db);
app.listen(PORT, () => {
  console.log(`🚀 后端服务运行在: http://localhost:${PORT}`);
});
