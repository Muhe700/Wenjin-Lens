# Cloudflare Worker 反向代理配置说明

本目录提供了将 Google Gemini API 反代至 Cloudflare 的完整脚本与配置文件。

## 文件说明
- `worker.js`: Cloudflare Worker 核心代理脚本（自动将请求转发到 `generativelanguage.googleapis.com` 并附带跨域头）。
- `wrangler.toml`: Cloudflare 官方 CLI 配置文件。

## 部署方法（二选一）

### 推荐方法：网页控制台直接创建（最快）
1. 在 Cloudflare 控制台页面，直接点击 **“Start with Hello World! 从‘你好，世界！’开始吧！”**；
2. 名字填写 `wenjin-gemini-proxy`，点击 **“Deploy (部署)”**；
3. 点击右上角 **“Edit code (编辑代码)”**；
4. 将本目录下的 `worker.js` 中的全部代码全选复制，替换掉网页编辑框中的所有代码；
5. 点击右上角 **“Save and deploy (保存并部署)”** 即可完成！

### 备用方法：使用 Wrangler 命令行部署
若本机已安装 Node.js，可在终端直接执行：
```bash
cd cloudflare-worker
npx wrangler login
npx wrangler deploy
```
