# 本地课程视频

把已获得的视频文件（例如 `html-intro.mp4`）放入此目录，再在
`src/config/courseVideos.json` 中按课程 ID 配置：

```json
{
  "1": "videos/html-intro.mp4",
  "2": "https://your-cdn.example.com/python-intro.mp4"
}
```

支持 MP4、WebM、Ogg；推荐浏览器兼容性较好的 H.264 + AAC MP4。
第一个 HTML5+CSS3 课程已明确配置为 B 站课程源，与其他课程统一使用弹窗中的 B 站官方播放器。
其余未配置覆盖地址的课程默认使用课程中的 B 站地址。
配置后需要重新构建。相对路径会自动适配 Vite 的部署前缀。

这里不包含已下载的视频。B 站网页链接并不是 MP4 文件地址；
如果要离线播放，请将自己拥有或已获得作者授权的视频原文件放入此目录。
B 站客户端缓存不能直接作为网页视频文件使用。

本地视频随构建输出到 `dist/videos/`，部署时需要一并上传。
大体积课程建议放在支持 Range 请求的静态服务器或对象存储，
并在配置中填写 HTTPS 文件地址，以支持拖动进度和避免代码仓库过大。

B 站站外播放器说明：https://player.bilibili.com/
