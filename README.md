# CSA 会员大会菜篮子纪要系统

社区支持农业（CSA）会员大会的全栈系统：前端展示当季蔬菜品种与种植日历、维护会员对话与反馈；
后端提供 REST API，处理会员/蔬菜/日历/对话数据，并在配置了 OpenAI 或 SMTP 的情况下调用 Whisper
转写、pyannote 说话人分离、OpenAI 生成种植意向与会议纪要，以及邮件下发。

- `backend/`：FastAPI + SQLAlchemy 后端，入口 `backend/main.py`，业务路由在 `backend/app/api/`，
  外部服务封装在 `backend/app/services/`。
- `frontend/`：React + Vite + TypeScript 前端，通过 `frontend/src/services/api.ts` 调用后端 `/api/*`。
- 数据库：默认 SQLite（`sqlite:///./csa.db`），可用环境变量 `DATABASE_URL` 覆盖。

## 运行方式

```bash
# 后端（在 backend/ 目录）
pip install -r requirements.txt
python -m uvicorn main:app --reload

# 前端（在 frontend/ 目录）
npm install
npm run dev
```

未配置 `OPENAI_API_KEY` / `PYANNOTE_AUTH_TOKEN` / SMTP 凭据时，后端必须走**离线分支**：
不发起任何网络请求，`/api/ai/*` 与 `/api/email/*` 仍要返回结构正确、可被前端消费的结果。

## 冒烟测试

`backend/tests/` 下的 pytest 覆盖顺利路径，当前在初始快照上全绿：

```bash
# 在 backend/ 目录
python -m pytest
```

---

## 行为规格（验收标准）

以下每一条都是验收点。实现必须逐条满足本规格，而不是只修复「已知问题」里举出的现象。

### A. 音频上传与转写链路

A1. `POST /api/conversations/{conversation_id}/upload-audio` 必须成功保存上传的音频文件并返回
    `filename`、`file_path`、`conversation_id`，HTTP 状态为 200。会话不存在时返回 404
    （不得返回 5xx）。
A2. 上传成功后，必须把音频路径持久化到该会话的 Transcript 记录：之后
    `GET /api/conversations/{conversation_id}/transcript` 返回的 `audio_file_path` 必须等于
    upload 返回的 `file_path`；`POST /api/ai/transcribe/{conversation_id}` 不得再以
    「对话没有音频文件」为由返回 400。
A3. 保存文件的文件名必须做安全化处理（只取原始文件名的基名），不得因为文件名包含
    `..`、`/`、`\` 而写出目标目录之外。

### B. Transcript 唯一性

B1. 同一 `conversation_id` 在数据库中最多只有一条 Transcript 记录。
    `POST /api/conversations/transcript` 必须是幂等 upsert：第一次创建，之后对同一会话再次提交时
    更新同一条记录（返回同一 `id`），而不是插入第二条。
B2. `GET /api/conversations/{conversation_id}/transcript` 返回的内容必须与最近一次
    `POST /api/conversations/transcript` / 上传写入的内容一致（不得出现「写入了新记录、读到的却是旧记录」）。

### C. 会员更新校验

C1. `PUT /api/members/{member_id}` 更新邮箱时，如果新邮箱已被**其它**会员占用，必须返回
    400 且不修改任何数据（不得返回 5xx）。邮箱未冲突时正常更新并返回 200。
C2. 不存在的会员返回 404。

### D. 蔬菜更新的主键安全

D1. `PUT /api/vegetables/{vegetable_id}` 只允许更新路径 id 指向的那条记录。请求体中的 `id`
    字段不得改写该记录的主键，也不得让原记录消失或凭空产生新记录；若请求体 `id` 与路径不一致，
    必须按路径为准（忽略体 id）或返回 422。
D2. 主键之外的字段（`name`、`season`、`share_quota` 等）仍要按请求更新。

### E. 蔬菜删除的关联处理

E1. 当某蔬菜下存在种植日历条目时，`DELETE /api/vegetables/{vegetable_id}` 不得返回 5xx。
    删除蔬菜必须级联删除其名下所有 `planting_calendar` 条目；删除后
    `GET /api/calendar` 不得再包含这些条目。
E2. 不存在的蔬菜删除返回 404。

### F. 查询参数命名（前后端契约）

F1. 前端 `frontend/src/services/api.ts` 使用 camelCase 查询参数。所有列表/查询接口必须**同时**
    接受 camelCase 与既有 snake_case 参数，两者语义等价。至少覆盖：
    - 种植日历 `startDate`/`endDate`/`activityType`（等价 `start_date`/`end_date`/`activity_type`）
    - 对话 `memberId`/`status`（等价 `member_id`/`status`）
    - AI 摘要 `summaryType`（等价 `summary_type`）
    - 反馈列表 `memberId`/`feedbackType`（等价 `member_id`/`feedback_type`）
    - 蔬菜 `season`/`availableOnly`（等价 `season`/`available_only`）
    - 会员 `role`/`activeOnly`（等价 `role`/`active_only`）
F2. 参数必须真正生效（过滤/筛选结果），而不是被静默忽略。布尔参数接受 `true`/`false`
    （大小写不敏感）、`1`/`0`。

### G. AI 接口的请求形状

G1. `POST /api/ai/generate-recipes` 必须接受前端实际发送的查询参数形式
    （`vegetables` 重复参数，或 `vegetables[]` 数组形式）以及 `count`，返回 200 与
    `{"recipes": [...]}`；不得因为参数放在 query 而返回 422。
G2. `POST /api/ai/generate-planting-intent` 必须接受 JSON 对象
    `{"conversationIds": [...]}` 与 `{"conversation_ids": [...]}`，也要保留对裸 JSON 数组
    `[1, 2]` 的兼容，均返回 200 与 `next_season_vegetables`/`share_adjustments`/
    `member_preferences`/`recommendations` 四个字段；不得因为形状不符返回 422。

### H. 离线可运行

H1. 在未配置 `OPENAI_API_KEY`、`PYANNOTE_AUTH_TOKEN`、SMTP 凭据的环境下，上述所有接口仍返回
    结构合法的 200 结果，且**不发起任何网络调用**。
H2. 现有 `backend/tests/` 冒烟测试必须保持全绿。

---

## 变更说明

针对真实使用中暴露的缺陷，按「行为规格」逐条修复，根因与修法如下：

1. **音频上传 500**（`POST /api/conversations/{id}/upload-audio`）：处理函数引用了未注入的
   `db` 变量（缺少 `Depends(get_db)`），且未把音频路径写入 Transcript。修复：注入数据库会话；
   上传成功后 upsert 该会话的 Transcript 并写入 `audio_file_path`，因此随后
   `GET .../transcript` 能读到同一路径，`POST /api/ai/transcribe/{id}` 不再报「对话没有音频文件」。
2. **上传文件名未安全化**：原始文件名直接拼进保存路径，含 `..`、`/`、`\` 时可写出上传目录。
   修复：先把 `\` 归一为 `/` 再取 `os.path.basename`，只保留基名，并在写入前确保上传目录存在。
3. **同一会话多条 Transcript**：`POST /api/conversations/transcript` 每次无条件插入新行，
   读取时拿到旧记录。修复：改为按 `conversation_id` 幂等 upsert——已存在则更新同一条记录
   （返回同一 `id`），保证读到的是最近一次写入。
4. **会员邮箱冲突 500**：`PUT /api/members/{id}` 直接提交，触发唯一约束的 `IntegrityError`。
   修复：提交前检查新邮箱是否被**其它**会员占用，冲突返回 400 且不改动数据；无冲突正常更新。
5. **蔬菜更新主键被改写**：`VegetableUpdate` 含 `id` 字段，更新循环把它 `setattr` 到 ORM 对象上，
   导致主键被改、原记录消失。修复：更新时 `exclude={"id"}`，请求体 `id` 一律以路径为准忽略，
   其余字段照常更新。
6. **删除有日历条目的蔬菜 500**：外键约束下直接删蔬菜触发 `IntegrityError`。修复：删除前级联
   删除该蔬菜名下所有 `planting_calendar` 条目，删后 `GET /api/calendar` 不再出现这些条目。
7. **camelCase 查询参数被静默忽略**：前端发 `startDate`/`memberId`/`availableOnly` 等，后端只认
   snake_case。修复：种植日历、对话、反馈、AI 摘要、蔬菜、会员的列表接口同时声明 camelCase 与
   snake_case 参数并合并取值，两种写法过滤结果一致；布尔参数由 FastAPI 解析，兼容
   `true/false`（不分大小写）与 `1/0`。
8. **生成食谱 422**：`vegetables: List[str]` 被 FastAPI 当作请求体参数，而前端把参数放在 query。
   修复：改为 `Query` 参数，同时接受 `vegetables` 重复参数与 `vegetables[]` 数组形式及 `count`。
9. **生成种植意向 422**：原签名只接受裸 JSON 数组。修复：改为读取任意 JSON 请求体并归一化，
   兼容 `{"conversationIds": [...]}`、`{"conversation_ids": [...]}` 与裸数组 `[1, 2]`，
   均返回约定的四个字段。
10. **离线可运行**：以上修复均未引入新的外部调用；未配置 `OPENAI_API_KEY`/`PYANNOTE_AUTH_TOKEN`/
    SMTP 时，`/api/ai/*` 仍返回结构合法的结果，不发起任何网络请求。

回归保障：新增 `backend/tests/spec_test.py`，逐条对应上述验收点（在未修复的实现上失败）；
原有 `backend/tests/smoke_test.py` 冒烟测试保持全绿。
