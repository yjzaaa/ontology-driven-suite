# DPA 当前身份事实链（T04.1）

> 证据基线：仓库 `D:\WorkSpace`，分支 `SSME.DPA.DEV`，revision `ce9ad5ca`。
> 提取方式：codebase-memory MCP 图谱（项目 `DPA-workspace`）+ 符号级源码阅读。
> 文档纪律：本文只记录 FACT / 待验证项（V-\*），不做方案设计；不含任何真实凭据值。
> 配置中的明文密钥（AzureAd ClientSecret、SMTP 账号）仅记录存在位置，值不入任何平台文档。

## 一、组件清单

| 组件 | 位置（revision ce9ad5ca） | 角色 |
|---|---|---|
| OIDC 注册 | `YiSha.Web/YiSha.Admin.Web/Startup.cs:56-61` | Entra ID 认证入口（Microsoft.Identity.Web） |
| Cookie 策略 | `Startup.cs:62-67` | SameSite 最小策略=None |
| CORS | `Startup.cs:87-93` | AllowAnyOrigin + AllowCredentials 声明 |
| DataProtection | `Startup.cs:94-95` | 密钥持久化到内容根 `DataProtection/` |
| AAD 登录动作 | `Controllers/HomeController.cs:287-334` `LoginByAAD` | OIDC 身份 → DPA 会话建立 |
| 登录页动作 | `Controllers/HomeController.cs:181-221` `Login` | 本地/演示登录页 |
| 会话解析核心 | `YiSha.Web.Code/Operator.cs:15-121` | Cookie/Session/WebApi 三模式读写与解析 |
| 会话用户模型 | `YiSha.Web.Code/OperatorInfo.cs:10-44` | UserId/gid/WebToken/ApiToken/IsSystem/RoleIds/AuthorizeList… |
| Token→用户装载 | `YiSha.Web.Code/DataRepository.cs:14-79` `GetUserByToken` | 按令牌查 sys_user 并装载角色与权限串 |
| Cookie 读写 | `YiSha.Web.Code/State/CookieHelper.cs:16-52` | UserToken cookie 写/读/删 |
| 缓存工厂 | `YiSha.Cache/YiSha.Cache.Factory/CacheFactory.cs:8-36` | Memory/Redis 切换（配置 `CacheProvider`） |
| Web 授权过滤器 | `YiSha.Admin.Web/Filter/AuthorizeFilterAttribute.cs:15-116` | ActionFilter 级权限判断 |
| API 授权过滤器 | `YiSha.Admin.WebApi/Filter/AuthorizeFilterAttribute.cs:25-144` | apiToken 参数版 |
| 权限数据表族 | `DPA.Enties/DbModels/permission_*.cs`、`sys_user`、`sys_user_belong`、`sys_menu_authorize` | 角色/权限/成员过滤数据 |

## 二、事实链（F1–F9）

### F1 OIDC 注册（配置事实 + 源码事实）
- `AddAuthentication(OpenIdConnectDefaults.AuthenticationScheme).AddMicrosoftIdentityWebApp(Configuration.GetSection("AzureAd"))`，启用 Graph（`DownstreamApi:Scopes=user.read`）与 `AddInMemoryTokenCaches()`（Startup.cs:56-61）。
- AzureAd 配置：`CallbackPath=/login/callback`；Tenant/ClientId 存在于 `appsettings.json`（值不入档）；**ClientSecret 以明文存在于源码配置**（安全观察，见第四节）。
- 信任方：Entra ID 租户 `ssme.dpa.mgt.siemens-healthineers.cn`。

### F2 Cookie 策略与 CORS（配置事实）
- `CookiePolicyOptions.MinimumSameSitePolicy = SameSiteMode.None`（Startup.cs:62-67）——最宽松策略。
- CORS 策略 `ddd`：`AllowAnyMethod().AllowAnyHeader().AllowAnyOrigin().AllowCredentials()`（Startup.cs:87-93）——宽松声明组合，浏览器侧 `AllowAnyOrigin+AllowCredentials` 互斥失效，但属风险信号（T04.6 素材）。

### F3 AAD 登录建立 DPA 会话（HomeController.cs:287-334）
1. `[Authorize]` + `[AuthorizeForScopes]`——OIDC 认证是前置条件；未认证请求先被 OIDC 中间件重定向到 Entra 登录，回调 `/login/callback` 后回到本动作。
2. `Graph /me` 取用户邮箱 `user.Mail`。
3. `sysUserBLL.GetEntityByEmail(user.Mail)` 按 email 查 `sys_user`；`userObj.Tag==1` 表示账号存在。
4. WebToken 规则（凭据载体）：
   - `LoginMultiple=true`（当前配置值，appsettings.json）→ 仅当 `WebToken` 为空时生成新 GUID（`SecurityHelper.GetGuid()`）；已有值**不轮换**；
   - `LoginMultiple=false` → **每次登录轮换 WebToken**（旧令牌自然失效，即"单会话踢出"机制）。
5. `UserBLL.UpdateUser(userObj.Result)` 把 WebToken 持久化到 `sys_user.web_token`。
6. `Operator.Instance.AddCurrent(WebToken)` → `CookieHelper.WriteCookie("UserToken", webToken)`。
7. 异步写登录日志（IP/IP 归属地/浏览器/OS/UA/成败状态），随后 `RedirectToAction("Index")`。
8. 失败路径（`Tag!=1`）：不写 Cookie、记录失败日志，仍重定向 Index（→ V2 待验证用户实际所见）。

### F4 会话解析（Operator.cs:15-121）
- `TokenName = "UserToken"`；`LoginProvider` 取自 `SystemConfig:LoginProvider`（当前配置 `Cookie`）。
- `Current()`：读 Cookie `UserToken` → `Trim('"')` → 空则返回 null（未认证）。
- 非空：先查进程内缓存 `CacheFactory.Cache.GetCache<OperatorInfo>(token)`；未命中 → `DataRepository.GetUserByToken(token)` 回源并 `SetCache(token, user)` 回填（未传 expireTime）。

### F5 Token→用户装载（DataRepository.cs:14-79）
- `SecurityHelper.IsSafeSqlParam(token)` 前置防护；随后**字符串拼接 SQL**：`WHERE web_token = '<token>' or api_token = '<token>'`——web/api 双令牌同查。
- 装载：`sys_user` 基本字段 → 角色（`sys_user_belong` ⋈ `SYS_ROLE`）→ 权限串（`sys_menu_authorize`（authorize_type=1）→ `sys_menu.authorize`，`menu_status=1` 且 `menu_type=3`）→ 部门名。
- 权限串装载的 `catch (Exception) {}` **静默吞异常**（DataRepository.cs:62-69）——权限装载失败时 `AuthorizeList` 为空，行为等同于无权限菜单（事实）。
- **查询无任何过期时间条件**——DB 层 WebToken 无 TTL。

### F6 授权过滤器——Web 端（AuthorizeFilterAttribute.cs:15-116）
- `Operator.Instance.Current()` → null 或 `UserId==0`：Ajax 请求返回 JSON「没有登录或登录已超时」；非 Ajax 重定向 `~/Home/LoginByAAD`。
- `user.IsSystem == 1` → 直接放行全部权限。
- 标注了 `Authorize` 串（如 `organization:user:view`，可逗号分隔多个）时：与 `MenuAuthorizeBLL.GetAuthorizeList(user)` 求交集；`SaveFormJson` 动作按表单 `Id>0` 细分 edit/add 权限。
- **未标注 `Authorize` 参数 → `hasPermission = true`（默认放行）**。
- 权限不足：Ajax 返回 JSON「没有权限」；非 Ajax 重定向 `~/Home/NoPermission`。
- 性质：这是 **ActionFilter（控制器层）**，不是业务层判断——业务层最终权限检查点见第三节与 V4。

### F7 授权过滤器——WebApi 变体（WebApi/Filter/AuthorizeFilterAttribute.cs:25-144）
- 凭据载体改为随请求传入的 `apiToken`（→ V7 待验证传递通道），经 `Operator.Current(apiToken)` 解析；缓存与 DB 回源逻辑与 F4/F5 相同。
- DPA 侧 MCP 设计文档（`.scratch/agent-transformation/YiSha.Mcp设计.md`）即基于该机制以 `McpDemo:OperatorToken` 伪造会话。

### F8 有效期与刷新汇总（凭据载体生命周期）

| 层 | 有效期 | 证据 | 刷新/失效 |
|---|---|---|---|
| Cookie `UserToken` | **固定 30 天**（2 参重载 `AddDays(30)`） | CookieHelper.cs:16-26 | 浏览器过期；`RemoveCookie` 主动删除 |
| Cookie 属性 | **未设置 Secure / HttpOnly / SameSite**（全部默认值） | CookieHelper.cs:20-24 | — |
| 进程内缓存 | 未传 expireTime（→ V1 待验证默认 TTL） | Operator.cs:104-110 | 进程重启即失 |
| DB `web_token` | **无过期字段、无过期校验** | DataRepository.cs:28-31 | 仅重新登录时按 LoginMultiple 规则轮换 |
| OIDC 会话 cookie | Microsoft.Identity.Web 默认管理 | Startup.cs:56-61 | 与 UserToken 生命周期**相互独立**（→ V5） |

### F9 退出（部分待验证）
- `Operator.RemoveCurrent()` 按模式删除 Cookie/Session/缓存（Operator.cs:47-71）；调用方（Logout 动作/前端触发点）→ V3 待验证。

## 三、业务层最终权限检查点（T04.1 步骤 3）

已证实的检查层级：
1. **OIDC 认证层**：未认证 → 无法进入 `LoginByAAD`；
2. **ActionFilter 层**（F6/F7）：登录态 + 菜单权限串交集；
3. **业务层**：**待深挖（V4）**——已知线索：`DPA.Enties` 的 `permission_orgMember` / `permission_role_emp_rel` / `sysEmployeePermissionFilterObj` / `sysRolePermissionFilterObj` 表族与 `DPA.BusinessCore/BaseCore/*Manager.Study` 装载器，提示存在组织/角色级数据过滤；MasterData 试点范围内（SubtableType 保存链）业务层是否有二次权限判断尚未取证。
4. **数据层**：行级范围由业务 SQL 自行实现（无统一行级安全），`GetUserByToken` 装载的组织/角色信息供业务 SQL 使用（→ 与 WP06 治理查询的数据范围设计直接相关）。

## 四、安全观察（喂给 T04.6，不做方案）

| 观察 | 证据 | 影响 |
|---|---|---|
| UserToken Cookie 无 Secure/HttpOnly/SameSite 设置 | CookieHelper.cs:20-24 | XSS 可读、明文信道可泄露、CSRF 面扩大 |
| WebToken 30 天有效且 DB 无 TTL | CookieHelper.cs:22、DataRepository.cs:28-31 | 令牌泄露后长期可用；无服务端会话过期 |
| Token 拼接 SQL（有 IsSafeSqlParam 前置防护） | DataRepository.cs:24-31 | 防护依赖单一函数；属于遗留模式 |
| LoginMultiple=true → WebToken 不轮换 | HomeController.cs:296-305 | 登录不使旧会话失效；令牌共享面大 |
| 权限装载空 catch | DataRepository.cs:62-69 | 权限数据异常时静默降级为无权限（fail-closed，但不可观测） |
| CORS AllowAnyOrigin+AllowCredentials 声明 | Startup.cs:87-93 | 声明层面的风险信号 |
| MinimumSameSitePolicy=None | Startup.cs:62-67 | 同站跨站策略最宽松 |
| 源码配置含明文 ClientSecret/SMTP 凭据 | appsettings.json（值不入档） | 证据管线必须脱敏（呼应 map 尚未明确区） |

## 五、待验证项（V-\*，每项含最小验证方法）

| 编号 | 待验证内容 | 最小验证方法 |
|---|---|---|
| V1 | `MemoryCacheImp.SetCache` 未传 expireTime 时的默认 TTL | 读 `YiSha.Cache/YiSha.MemoryCache/MemoryCacheImp.cs` 的 SetCache 实现 |
| V2 | 登录失败（Tag!=1）后用户在 Index 页实际所见与后续被拦路径 | 本地启动测试实例（localhost:5000）用不存在邮箱走一次 LoginByAAD |
| V3 | 退出动作与 `RemoveCurrent` 的调用链 | 图谱搜 `RemoveCurrent` callers + HomeController 退出动作源码 |
| V4 | MasterData 业务层内的二次权限/数据范围判断 | 追 `SubTableDataHandler`/`SubtableController` 保存链中的权限引用与 permission\_\* 表使用点 |
| V5 | OIDC 会话过期但 UserToken 有效时的组合行为 | 测试实例缩短 OIDC cookie 生命周期后重放请求 |
| V6 | 测试环境（localhost:5000 / UAT）实际生效的 LoginProvider、LoginMultiple 值 | 检查部署机环境变量与运行时配置（已知存在环境变量覆盖机制） |
| V7 | WebApi 端 apiToken 的传递通道（header 名/参数名） | 读 WebApi/Filter/AuthorizeFilterAttribute.cs:25-144 全文 |

## 六、验证记录（T04.1 验收对照）

- [x] 从已认证请求可反向追踪：任意带 `UserToken` 的请求 → F6 过滤器 → F4 解析 → F5 装载 → F3 令牌签发 → Entra 主体。
- [x] 每个"当前行为"均有 file:line 证据（F1–F9）。
- [ ] 三条链抽查：成功链（F3→F6 已覆盖）、会话过期链（依赖 V1/V5）、权限拒绝链（F6 已覆盖，业务层拒绝依赖 V4）——待 V 项关闭后补记。
- [x] 全文不含 Cookie/Token/Secret/Header 真实值。
