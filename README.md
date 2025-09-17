# auth-app-openresty

这是一个用于演示 OpenResty/Nginx 与后端鉴权服务协作的示例项目。项目包含：

- 一个简单的 Flask 鉴权服务（位于 `auth_service/`），负责发放和校验短期 token。
- 一个基于 OpenResty 的网关（位于 `openresty/`），可在真实环境中替换为 Nginx/OpenResty 配置来调用鉴权服务。

目标读者：希望了解如何通过一个轻量鉴权 API 让 Nginx/OpenResty 实现基于 token 的接入控制的开发者。

## 目录结构（简要）

- `auth_service/` — Flask 鉴权后端，包含 `main.py`。
- `openresty/` — OpenResty 网关 Dockerfile 与配置（示例）。
- `docker-compose.yaml` — 用于在本地快速启动两个服务的组合。

## 快速开始（使用 Docker Compose）

在项目根目录下运行（Windows PowerShell）：

```powershell
docker-compose up --build
```

服务启动后：

- 鉴权服务（Flask）监听 `http://localhost:5000`
- OpenResty 网关监听 `http://localhost:8080`

## API 说明（鉴权服务）

1) POST /login

- 描述：模拟登录接口。只要提供 `username` 即颁发一个短期 token（演示用）。
- 请求示例（JSON body）：

  ```json
  {
    "username": "alice"
  }
  ```

- 返回示例（200）：

  ```json
  {
    "token": "<uuid-token>",
    "expires_in": 60
  }
  ```

2) GET /authen

- 描述：鉴权校验接口，供 OpenResty/Nginx 在代理请求时调用，判断请求是否允许。
- 必须通过 HTTP header `X-Auth-Id` 传递 token。
- 响应：
  - 成功（200）: `{ "allowed": true, "username": "alice" }`
  - 缺少 header（401）: `{ "allowed": false, "reason": "missing X-Auth-Id" }`
  - 无效或过期（403）: `{ "allowed": false, "reason": "invalid token" }` 或 `{ "allowed": false, "reason": "expired" }`

## 鉴权协议（协议说明）

此处定义服务间简单的鉴权协议（用于 OpenResty -> auth 服务）：

- 客户端（前端或测试工具）向鉴权服务请求 `/login` 获取 token；token 为 UUID 字符串，服务端在内存存储并记录过期时间。
- 网关（OpenResty/Nginx）在需要鉴权的请求到达时，向上游鉴权服务发起 `GET /authen` 调用：
  - 方法：GET
  - Header：`X-Auth-Id: <token>`
  - 无需请求体
  - 返回：JSON，包含 `allowed: true|false`。当 `allowed: true` 时，可选择将 `username` 传递给下游服务或在日志中记录。

错误处理与语义：

- 401（Unauthorized）：表示请求缺少必需的 `X-Auth-Id` header。
- 403（Forbidden）：表示 token 无效或已过期。
- 200：鉴权通过。

安全与生产建议：

- 当前实现为演示，token 储存在进程内存且 TTL 较短（默认 60 秒）。生产环境请使用 Redis、数据库或其它持久化/可共享的存储，并使用 HTTPS 保护通信。
- token 应具有更强的签名或使用 JWT（并校验签名/范围/过期）以减少对中心存储的依赖。
- 对鉴权接口应做速率限制、日志和监控，并在网关部件添加缓存以降低鉴权服务负载（注意缓存失效策略）。

## 运行与调试（建议）

- 构建并启动：

```powershell
docker-compose up --build
```

- 测试登录与鉴权（示例，使用 curl 或 httpie）

```powershell
# 获取 token
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice"}' http://localhost:5000/login

# 使用 token 校验
curl -H "X-Auth-Id: <token-from-login>" http://localhost:5000/authen
```

## 已知限制

- 演示用途：token 存放在内存中且没有持久化，不适合多实例部署。
- 未实现认证（登录）逻辑，仅根据 username 颁发 token；请在真实系统中接入密码验证/第三方登录等机制。
