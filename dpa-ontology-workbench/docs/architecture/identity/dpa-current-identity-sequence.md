# DPA 当前身份与会话时序（T04.1 附属）

> 与 [dpa-current-identity-fact-chain.md](dpa-current-identity-fact-chain.md) 配套阅读；F 编号对应其中小节。
> 证据基线：`D:\WorkSpace` @ revision `ce9ad5ca`（分支 SSME.DPA.DEV）。
> 本图为源码事实的投影，不含任何凭据值；虚线消息为待验证项（V-\*）。

## 登录与会话建立（F1–F3）

```mermaid
sequenceDiagram
    autonumber
    actor B as 浏览器
    participant AAD as Entra ID 租户
    participant W as YiSha.Admin.Web
    participant G as Microsoft Graph
    participant DB as SQL Server

    B->>W: 任意受保护页面（未登录）
    W->>B: 302 重定向 ~/Home/LoginByAAD（F6 过滤器非 Ajax 分支）
    B->>W: GET /Home/LoginByAAD
    W->>B: OIDC 中间件重定向至 Entra 登录（F1, [Authorize]）
    B->>AAD: 用户认证
    AAD->>B: 回调 /login/callback + 授权码
    B->>W: GET /login/callback（换取 token，InMemoryTokenCaches 缓存）
    W->>B: 302 继续原请求 → LoginByAAD
    W->>G: GET /me（取 Mail）
    G-->>W: mail
    W->>DB: sys_user 按 email 查询（GetEntityByEmail）
    DB-->>W: 用户实体（Tag=1）
    Note over W,DB: WebToken 规则（F3）：LoginMultiple=true 且已有值 → 不轮换；否则生成新 GUID
    W->>DB: UPDATE sys_user.web_token（UserBLL.UpdateUser）
    W->>B: Set-Cookie UserToken=<webtoken>（30 天；未设 Secure/HttpOnly/SameSite，F8）
    W->>DB: 异步写登录日志（IP/浏览器/OS/成败）
    W->>B: 302 → /Home/Index
```

## 已登录请求的解析与授权（F4–F6）

```mermaid
sequenceDiagram
    autonumber
    actor B as 浏览器
    participant F as AuthorizeFilterAttribute
    participant O as Operator.Current()
    participant C as 进程内缓存
    participant R as DataRepository.GetUserByToken
    participant DB as SQL Server
    participant BL as 业务层（BLL/Service）

    B->>F: 业务请求（Cookie: UserToken）
    F->>O: Current()
    O->>C: GetCache<OperatorInfo>(token)
    alt 缓存命中
        C-->>O: OperatorInfo
    else 缓存未命中
        O->>R: GetUserByToken(token)
        R->>DB: WHERE web_token='<t>' or api_token='<t>'（拼接 SQL，IsSafeSqlParam 前置）
        DB-->>R: 用户行 + 角色（sys_user_belong⋈SYS_ROLE）+ 权限串（sys_menu_authorize→sys_menu）
        R-->>O: OperatorInfo（RoleIds/AuthorizeList/IsSystem…）
        O->>C: SetCache(token, user)（未传 expireTime → V1）
    end
    alt 未登录（token 空 / 用户 null）
        F->>B: Ajax: JSON「没有登录或登录已超时」；非 Ajax: 302 LoginByAAD
    else IsSystem==1
        F->>BL: 放行（绕过全部权限检查）
    else 标注了 Authorize 串
        F->>F: 与 MenuAuthorizeBLL.GetAuthorizeList 求交集（SaveFormJson 按 Id 细分 add/edit）
        alt 有交集
            F->>BL: 放行
        else 无交集
            F->>B: Ajax: JSON「没有权限」；非 Ajax: 302 /Home/NoPermission
        end
    else 未标注 Authorize
        F->>BL: 放行（默认允许，F6）
    end
    Note over BL,DB: 业务层内二次权限/数据范围判断 → V4（与 WP06 治理查询直接相关）
```

## 待验证链路（V-\*，虚线项）

```mermaid
sequenceDiagram
    autonumber
    actor B as 浏览器
    participant W as YiSha.Admin.Web
    participant AAD as Entra ID

    Note over B,AAD: V5：OIDC 会话过期但 UserToken 仍有效的组合行为
    B->>W: 业务请求（仅 UserToken 有效）
    W->>AAD: LoginByAAD [Authorize] 触发重新 OIDC？
    AAD-->>B: 静默重认证或提示登录（待实测）
    W->>B: 重新发放/沿用 WebToken（取决于 LoginMultiple）

    Note over B,W: V3：退出动作与 RemoveCurrent 调用链
    B->>W: LogOut（路由/触发点待取证）
    W->>B: RemoveCookie(UserToken) + RemoveCache(token)（待验证）

    Note over W: V1：缓存默认 TTL；V2：登录失败所见；V7：WebApi apiToken 传递通道
```

## 与 Wayfinder 后续工作包的挂钩

- F3/F8 的「令牌无 TTL、不轮换」→ T04.2 同源 Cookie 转发的有效期上界约束。
- F5 的拼接 SQL 与 F6 的默认放行 → T04.6 威胁模型输入。
- 第三节的业务层检查点空缺 → T04.3 IdentityContext 契约必须覆盖业务层可见身份字段（UserId/gid/RoleIds/AuthorizeList）。
- V4 → WP06 治理查询与数据范围的证据入口。
