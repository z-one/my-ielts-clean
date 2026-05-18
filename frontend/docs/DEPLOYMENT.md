# Nginx部署说明

## 快速部署步骤

### 1. 打包项目
```bash
npm run build
# 或
pnpm run build
```

### 2. 上传文件
将 `dist` 文件夹内的所有文件上传到服务器的 `/var/www/ielts-app/` 目录

### 3. 使用配置文件

#### 方法一：使用生成的完整配置
将 `nginx.conf` 中的内容复制到：
- `/etc/nginx/sites-available/ielts-app`
- 然后创建软链接：`sudo ln -s /etc/nginx/sites-available/ielts-app /etc/nginx/sites-enabled/`

#### 方法二：使用简化配置（推荐新手）
将以下配置添加到 `/etc/nginx/nginx.conf` 的 `http` 块中：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名
    root /var/www/ielts-app;
    index index.html;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|mp3|wav)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Vue SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 4. 修改配置中的关键信息
- `server_name`: 改为你的域名或服务器IP
- `root`: 改为你的项目实际路径

### 5. 测试并重启Nginx
```bash
# 测试配置文件语法
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
# 或重新加载配置
sudo systemctl reload nginx
```

## 常见问题解决

### 1. 404错误
确保 `root` 路径正确，并且文件权限正确：
```bash
sudo chown -R www-data:www-data /var/www/ielts-app
sudo chmod -R 755 /var/www/ielts-app
```

### 2. Vue路由刷新404
确保配置中有：
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 3. 静态资源404
检查文件路径是否正确，确保静态资源文件都在 `dist` 文件夹中。

### 4. 音频文件无法播放
确保音频文件路径正确，检查 `/public/vocabulary/audio/` 目录是否正确上传。

## 生产环境优化建议

1. **启用HTTPS**：使用Let's Encrypt免费SSL证书
2. **开启gzip压缩**：已在配置中包含
3. **设置缓存策略**：已在配置中包含
4. **使用CDN**：对于静态资源，可以考虑使用CDN加速

## 监控日志
查看访问日志：
```bash
tail -f /var/log/nginx/ielts-app.access.log
```

查看错误日志：
```bash
tail -f /var/log/nginx/ielts-app.error.log
```