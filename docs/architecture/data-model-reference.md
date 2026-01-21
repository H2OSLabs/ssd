# Synnovator 数据模型参考手册

**版本:** 1.0
**最后更新:** 2026-01-21
**状态:** Final

## 1. 概述

### 1.1 文档目的

本文档为开发者和运营人员提供 Synnovator 平台所有数据模型的完整参考，包括字段定义、关系映射、业务逻辑和 Wagtail Admin 配置。

### 1.2 模型分类体系

**核心业务模型 (Core Business Models):**
- `HackathonPage`: 黑客松活动页面
- `Phase`: 活动时间表阶段
- `Prize`: 奖项配置
- `Team`: 参赛团队
- `TeamMember`: 团队成员 (Through Model)
- `Quest`: Dojo 挑战任务
- `Submission`: 提交内容（Quest/Hackathon）

**内容管理模型 (CMS Models):**
- `BasePage`: 页面基类（抽象）
- `HomePage`: 首页
- `ArticlePage`: 文章页面
- `NewsListingPage`: 新闻列表页

**辅助模型 (Supporting Models):**
- `AuthorSnippet`: 作者片段
- `ArticleTopic`: 文章主题
- `Statistic`: 统计数字
- `PageRelatedPage`: 页面关联

**用户与身份模型 (User & Identity):**
- `User`: 扩展的用户模型

**设置模型 (Settings Models):**
- `NavigationSettings`: 导航配置
- `SocialMediaSettings`: 社交媒体配置
- `SystemMessagesSettings`: 系统消息配置

**图像模型 (Image Models):**
- `CustomImage`: 自定义图像
- `Rendition`: 图像渲染变体

### 1.3 关键设计模式

**1. Events as Code (赛事即代码)**
- 黑客松配置通过 Wagtail CMS 管理
- 支持版本控制和复用
- 使用 InlinePanel 实现嵌套编辑

**2. 多态关联 (Polymorphic Associations)**
- `Submission` 支持 user XOR team (提交者)
- `Submission` 支持 quest XOR hackathon (目标)
- 使用 `clean()` 方法验证约束

**3. Through Models 模式**
- `TeamMember` 携带额外属性（role, is_leader, joined_at）
- 支持复杂的多对多关系

**4. JSONField 灵活配置**
- `HackathonPage.required_roles`: 角色要求列表
- `User.skills`: 技能标签
- `Phase.requirements`: 阶段特定要求

**5. Wagtail 特有模式**
- StreamField: 灵活内容区
- InlinePanel: 嵌套管理
- TranslatableMixin: 国际化支持

### 1.4 数据库关系总览

详细的 ER 图请参考 [model-relationships.mmd](./model-relationships.mmd)

**核心关系:**
- HackathonPage 1:N Phase (阶段)
- HackathonPage 1:N Prize (奖项)
- HackathonPage 1:N Team (团队)
- HackathonPage 1:N Quest (任务)
- HackathonPage 1:N Submission (最终提交)
- Team M:N User (through TeamMember)
- Quest 1:N Submission (任务提交)

## 2. 核心业务模型 (Core Business Models)

### 2.1 黑客松管理

#### 2.1.1 HackathonPage

**文件位置:** `synnovator/hackathons/models/hackathon.py:10`

**继承:** `Page` (Wagtail)

**用途:** 代表黑客松活动主页面，使用 Wagtail CMS 管理活动配置、阶段和奖项。这是"Events as Code"架构的核心模型。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 | 关联需求 |
|--------|------|------|--------|------|----------|
| `description` | RichTextField | 否 | - | 黑客松简介（富文本） | REQ-26 |
| `cover_image` | FK(CustomImage) | 否 | NULL | 封面图片 | REQ-20 |
| `min_team_size` | PositiveInteger | 是 | 2 | 最小团队人数 | REQ-28, 36 |
| `max_team_size` | PositiveInteger | 是 | 5 | 最大团队人数 | REQ-28, 36 |
| `allow_solo` | Boolean | 是 | False | 是否允许个人参赛 | REQ-28 |
| `required_roles` | JSONField | 否 | [] | 必需角色列表 ['hacker', 'hustler'] | REQ-36 |
| `passing_score` | Decimal(5,2) | 是 | 80.0 | 及格分数线 (0-100) | REQ-34 |
| `status` | CharField(20) | 是 | 'draft' | 活动状态（见下文） | REQ-26, 27 |
| `body` | StreamField | 否 | [] | 灵活内容区（heading/paragraph） | - |

**状态枚举 (status choices):**
- `draft`: 草稿
- `upcoming`: 即将开始
- `registration_open`: 报名开放
- `in_progress`: 进行中
- `judging`: 评审中
- `completed`: 已完成
- `archived`: 已归档

**继承字段 (from Page):**
- `title`: 页面标题
- `slug`: URL 标识符
- `seo_title`, `search_description`: SEO 字段
- `live`, `has_unpublished_changes`: 发布状态

**关系映射:**

| 关系类型 | 关联模型 | 关系名 | 说明 |
|---------|---------|--------|------|
| 一对多 | Phase | `phases` | 活动时间表阶段 |
| 一对多 | Prize | `prizes` | 奖项配置 |
| 一对多 | Team | `teams` | 参赛团队 |
| 一对多 | Quest | `quests` | 关联任务 |
| 一对多 | Submission | `final_submissions` | 最终提交 |

**关键方法:**

```python
def get_current_phase(self) -> Phase | None:
    """获取当前活跃阶段（基于时间）"""
    from django.utils import timezone
    now = timezone.now()
    return self.phases.filter(
        start_date__lte=now,
        end_date__gte=now
    ).first()
```

**用途:** 用于前端显示当前阶段状态（REQ-27）

**示例:**
```python
hackathon = HackathonPage.objects.get(slug='ai-challenge-2026')
current_phase = hackathon.get_current_phase()
if current_phase:
    print(f"当前阶段: {current_phase.title}")
    print(f"截止时间: {current_phase.end_date}")
```

---

```python
def get_leaderboard(self, limit=10) -> QuerySet[Team]:
    """获取排行榜前 N 名队伍"""
    return self.teams.filter(
        status__in=['submitted', 'verified']
    ).order_by('-final_score')[:limit]
```

**用途:** 用于排行榜显示

**示例:**
```python
top_teams = hackathon.get_leaderboard(limit=5)
for rank, team in enumerate(top_teams, 1):
    print(f"{rank}. {team.name}: {team.final_score} 分")
```

**Wagtail Admin 配置:**

```python
content_panels = Page.content_panels + [
    FieldPanel('description'),
    FieldPanel('cover_image'),
    FieldPanel('body'),
    InlinePanel('phases', label="Hackathon Phases"),
    InlinePanel('prizes', label="Prizes"),
    MultiFieldPanel([
        FieldPanel('min_team_size'),
        FieldPanel('max_team_size'),
        FieldPanel('allow_solo'),
        FieldPanel('required_roles'),
    ], heading="Team Settings"),
    MultiFieldPanel([
        FieldPanel('passing_score'),
    ], heading="Scoring Settings"),
    FieldPanel('status'),
]
```

**管理员操作路径:**
1. Wagtail Admin → Pages
2. 导航到父页面（通常是 HomePage）
3. Add child page → Hackathon
4. 编辑阶段：使用 InlinePanel 添加/删除 Phase
5. 编辑奖项：使用 InlinePanel 添加/删除 Prize

**运营需求支持:**
- ✅ REQ-20: 首页海报展示（通过 cover_image）
- ✅ REQ-22: 星球页活动发布（Wagtail Page 发布机制）
- ✅ REQ-26: 调整活动状态（status 字段）
- ✅ REQ-27: 设置活动时间表（phases InlinePanel）
- ✅ REQ-28: 查看队伍信息（teams 反向关系）
- ✅ REQ-36: 根据赛规筛选队伍（required_roles 配置）

**使用示例:**

```python
# 创建黑客松
from synnovator.home.models import HomePage

home = HomePage.objects.first()
hackathon = HackathonPage(
    title="AI Innovation Challenge 2026",
    description="<p>Build the future of AI</p>",
    min_team_size=2,
    max_team_size=4,
    required_roles=['hacker', 'hustler'],
    status='registration_open',
    passing_score=80.0
)
home.add_child(instance=hackathon)
hackathon.save_revision().publish()

# 获取当前阶段
current_phase = hackathon.get_current_phase()
if current_phase and current_phase.is_active():
    print(f"Current: {current_phase.title}")

# 查询排行榜
top_teams = hackathon.get_leaderboard(limit=5)
for team in top_teams:
    print(f"{team.name}: {team.final_score}")

# 检查赛事状态
if hackathon.status == 'registration_open':
    print("报名开放中！")
```

**已知限制:**

1. **手动状态管理:** `status` 字段需手动更新，未来可添加 Celery 定时任务根据 Phase 时间自动切换
2. **JSONField 无外键约束:** `required_roles` 为 JSONField，不支持外键级别的数据完整性验证
3. **缺少淘汰/晋级记录:** 没有专门的模型记录晋级/淘汰决策历史

**优化建议:**

1. 添加自动状态转换（基于 Phase 时间）
2. 添加 `registration_deadline` 字段（显式截止日期）
3. 创建 `AdvancementLog` 模型记录晋级/淘汰历史

**相关模型:** Phase, Prize, Team, Quest, Submission

---

#### 2.1.2 Phase

**文件位置:** `synnovator/hackathons/models/hackathon.py:120`

**继承:** `models.Model`

**用途:** 代表黑客松时间表中的一个阶段（如注册期、编码期、评审期）。通过 InlinePanel 在 HackathonPage 中管理。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `hackathon` | ParentalKey | 是 | - | 所属黑客松 |
| `title` | CharField(200) | 是 | - | 阶段名称（如 'Team Formation'） |
| `description` | TextField | 否 | '' | 阶段描述和目标 |
| `start_date` | DateTimeField | 是 | - | 开始时间（UTC） |
| `end_date` | DateTimeField | 是 | - | 结束时间（UTC） |
| `order` | PositiveInteger | 是 | 0 | 显示顺序（数字越小越靠前） |
| `requirements` | JSONField | 否 | {} | 阶段特定要求（JSON 格式） |

**排序:** `['order', 'start_date']`

**关系映射:**

| 关系类型 | 关联模型 | on_delete | 说明 |
|---------|---------|-----------|------|
| 多对一 | HackathonPage | CASCADE | 黑客松删除时阶段也删除 |

**关键方法:**

```python
def is_active(self) -> bool:
    """检查阶段是否当前活跃"""
    from django.utils import timezone
    now = timezone.now()
    return self.start_date <= now <= self.end_date
```

**示例:**
```python
phase = Phase.objects.get(id=1)
if phase.is_active():
    print(f"{phase.title} 正在进行中")
    remaining = phase.end_date - timezone.now()
    print(f"剩余时间: {remaining.days} 天")
```

**Wagtail Admin 配置:**

```python
panels = [
    FieldPanel('title'),
    FieldPanel('description'),
    FieldPanel('start_date'),
    FieldPanel('end_date'),
    FieldPanel('order'),
]
```

通过 InlinePanel 在 HackathonPage 编辑界面中管理，可拖拽排序（基于 order 字段）。

**运营需求支持:**
- ✅ REQ-27: 设置活动时间表
- ✅ REQ-24: 日历信息（可转换为日历事件 JSON）

**使用示例:**

```python
# 创建阶段（通过 HackathonPage InlinePanel 或代码）
from django.utils import timezone
from datetime import timedelta

hackathon = HackathonPage.objects.get(slug='ai-challenge')
phases = [
    Phase(
        hackathon=hackathon,
        title="Team Formation",
        description="Find your team members",
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=7),
        order=1
    ),
    Phase(
        hackathon=hackathon,
        title="Hacking Period",
        description="Build your project",
        start_date=timezone.now() + timedelta(days=7),
        end_date=timezone.now() + timedelta(days=14),
        order=2
    ),
]
Phase.objects.bulk_create(phases)

# 查询当前活跃阶段
current = hackathon.get_current_phase()
print(f"当前阶段: {current.title if current else '无'}")
```

**已知限制:**

1. 缺少阶段结束时的自动通知
2. 缺少阶段完成度追踪

**相关模型:** HackathonPage

---

#### 2.1.3 Prize

**文件位置:** `synnovator/hackathons/models/hackathon.py:182`

**继承:** `models.Model`

**用途:** 代表奖项和奖励配置。通过 InlinePanel 在 HackathonPage 中管理。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `hackathon` | ParentalKey | 是 | - | 所属黑客松 |
| `title` | CharField(200) | 是 | - | 奖品名称（如 'First Place'） |
| `description` | TextField | 否 | '' | 奖品详情 |
| `rank` | PositiveInteger | 是 | 1 | 排名（1=第一名，2=第二名） |
| `monetary_value` | Decimal(10,2) | 否 | NULL | 现金价值（USD） |
| `benefits` | JSONField | 否 | [] | 非货币福利数组 |

**排序:** `['rank']`

**关系映射:**

| 关系类型 | 关联模型 | on_delete | 说明 |
|---------|---------|-----------|------|
| 多对一 | HackathonPage | CASCADE | 黑客松删除时奖品也删除 |

**Wagtail Admin 配置:**

```python
panels = [
    FieldPanel('title'),
    FieldPanel('description'),
    FieldPanel('rank'),
    FieldPanel('monetary_value'),
]
```

通过 InlinePanel 在 HackathonPage 编辑界面中管理，按 rank 排序显示。

**使用示例:**

```python
# 创建奖品
hackathon = HackathonPage.objects.get(slug='ai-challenge')
prizes = [
    Prize(
        hackathon=hackathon,
        title="First Place",
        description="Grand prize winner",
        rank=1,
        monetary_value=10000.00,
        benefits=['Incubation program', 'Mentorship']
    ),
    Prize(
        hackathon=hackathon,
        title="Second Place",
        description="Runner-up",
        rank=2,
        monetary_value=5000.00,
        benefits=['Mentorship']
    ),
]
Prize.objects.bulk_create(prizes)

# 查询奖品
top_prize = Prize.objects.filter(hackathon=hackathon, rank=1).first()
print(f"Top prize: ${top_prize.monetary_value}")
```

**相关模型:** HackathonPage

---

### 2.2 团队管理

#### 2.2.1 Team

**文件位置:** `synnovator/hackathons/models/team.py:5`

**继承:** `models.Model`

**用途:** 代表参加黑客松的团队。支持多维度评分（技术/商业/运营）和状态管理。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 | 关联需求 |
|--------|------|------|--------|------|----------|
| `hackathon` | FK(HackathonPage) | 是 | - | 所属黑客松 | REQ-28 |
| `name` | CharField(200) | 是 | - | 团队名称 | REQ-28 |
| `slug` | SlugField(200) | 是 | - | URL 友好标识符 | - |
| `tagline` | CharField(500) | 否 | '' | 团队简述（slogan） | - |
| `members` | M2M(User) | - | - | 通过 TeamMember through model | REQ-6, 28 |
| `final_score` | Decimal(6,2) | 是 | 0.0 | 综合评分 (0-100) | REQ-31, 32 |
| `technical_score` | Decimal(6,2) | 是 | 0.0 | 技术评分（CTO 评） | REQ-34 |
| `commercial_score` | Decimal(6,2) | 是 | 0.0 | 商业评分（CBO 评） | REQ-34 |
| `operational_score` | Decimal(6,2) | 是 | 0.0 | 运营评分（COO 评） | REQ-34 |
| `status` | CharField(20) | 是 | 'forming' | 状态（见下文） | REQ-31 |
| `is_seeking_members` | Boolean | 是 | True | 是否显示在组队页面 | REQ-13 |
| `created_at` | DateTimeField | 是 | auto | 创建时间 | - |
| `updated_at` | DateTimeField | 是 | auto | 更新时间 | - |

**状态枚举 (status choices):**
- `forming`: 组建中（寻找成员）
- `ready`: 就绪（满足要求）
- `submitted`: 已提交
- `verified`: 已验证
- `disqualified`: 被取消资格

**约束:**
- `unique_together = [['hackathon', 'slug']]` - 同一黑客松内团队 slug 唯一

**排序:** `['-final_score', 'name']` - 按分数降序，名称升序

**关系映射:**

| 关系类型 | 关联模型 | 关系名 | Through Model | 说明 |
|---------|---------|--------|---------------|------|
| 多对一 | HackathonPage | - | - | 所属黑客松 |
| 多对多 | User | `members` | TeamMember | 团队成员 |
| 一对多 | Submission | `submissions` | - | 提交记录 |

**关键方法:**

```python
def get_leader(self) -> TeamMember | None:
    """获取队长（is_leader=True 的成员）"""
    return self.membership.filter(is_leader=True).first()
```

**示例:**
```python
team = Team.objects.get(id=1)
leader = team.get_leader()
if leader:
    print(f"队长: {leader.user.get_full_name()}")
```

---

```python
def has_required_roles(self) -> bool:
    """检查团队是否满足黑客松要求的角色组成"""
    required = set(self.hackathon.required_roles)
    current = set(self.membership.values_list('role', flat=True))
    return required.issubset(current)
```

**用途:** 用于资格检测（REQ-36）

**示例:**
```python
if not team.has_required_roles():
    print("团队角色配置不符合要求！")
    required = set(team.hackathon.required_roles)
    current = set(team.membership.values_list('role', flat=True))
    missing = required - current
    print(f"缺少角色: {missing}")
```

---

```python
def can_add_member(self) -> bool:
    """检查团队是否可以接收新成员"""
    return (
        self.members.count() < self.hackathon.max_team_size and
        self.status == 'forming'
    )
```

**示例:**
```python
if team.can_add_member():
    print("可以添加新成员")
else:
    print("团队已满或不在组建期")
```

**状态转换流程:**

```
forming (组建中)
  ↓ [满足人数和角色要求]
ready (就绪)
  ↓ [提交作品]
submitted (已提交)
  ↓ [审核通过]
verified (已验证)

    [违规] → disqualified (被取消资格)
```

**运营需求支持:**
- ✅ REQ-6: 用户团队管理（members 关系）
- ✅ REQ-28: 查看队伍信息
- ⚠️ REQ-31: 晋级淘汰标注（status 字段，但缺少 advanced/eliminated 状态）
- ⚠️ REQ-32: 阶段晋级检测（has_required_roles 方法，但缺少完整流程）
- ✅ REQ-34: 多维度评分（三个独立评分字段）
- ✅ REQ-36: 赛规筛选队伍

**使用示例:**

```python
# 创建团队
from synnovator.hackathons.models import Team, TeamMember
from synnovator.users.models import User

hackathon = HackathonPage.objects.get(slug='ai-challenge')
user1 = User.objects.get(username='alice')
user2 = User.objects.get(username='bob')

team = Team.objects.create(
    hackathon=hackathon,
    name="AI Innovators",
    slug="ai-innovators",
    tagline="Building the future",
    status='forming'
)

# 添加成员
TeamMember.objects.create(team=team, user=user1, role='hacker', is_leader=True)
TeamMember.objects.create(team=team, user=user2, role='hustler', is_leader=False)

# 检查资格
if team.has_required_roles():
    team.status = 'ready'
    team.save()

# 评分
team.technical_score = 85.5
team.commercial_score = 78.0
team.operational_score = 90.0
team.final_score = (team.technical_score + team.commercial_score + team.operational_score) / 3
team.save()
```

**缺失功能（需扩展）:**
- ❌ 缺少 `advanced`（晋级）和 `eliminated`（淘汰）明确状态
- ❌ 缺少 `elimination_reason` 字段记录淘汰原因
- ❌ 缺少 `current_round` 轮次追踪

**优化建议:**

1. 扩展 status choices 添加 'advanced' 和 'eliminated'
2. 添加 `elimination_reason: TextField`
3. 添加 `current_round: PositiveInteger`
4. 创建 `AdvancementLog` 模型记录晋级/淘汰历史

**相关模型:** HackathonPage, TeamMember, User, Submission

---

#### 2.2.2 TeamMember

**文件位置:** `synnovator/hackathons/models/team.py:112`

**继承:** `models.Model`

**用途:** Team-User 多对多关系的 through model，记录团队成员角色和领导身份。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `team` | FK(Team) | 是 | - | 所属团队 |
| `user` | FK(User) | 是 | - | 用户 |
| `role` | CharField(50) | 是 | - | 角色（见下文） |
| `is_leader` | Boolean | 是 | False | 是否为队长 |
| `joined_at` | DateTimeField | 是 | auto | 加入时间 |

**角色枚举 (role choices) - 3H 模型:**
- `hacker`: Hacker（工程师/开发）- 技术实现
- `hipster`: Hipster（设计/UX）- 操作和用户体验
- `hustler`: Hustler（商业/市场）- 商业发展和营销
- `mentor`: Mentor（导师）- 指导和咨询

**约束:**
- `unique_together = [['team', 'user']]` - 用户不能重复加入同一团队

**排序:** `['-is_leader', 'joined_at']` - 队长优先显示，然后按加入时间

**关系映射:**

| 关系类型 | 关联模型 | on_delete | 说明 |
|---------|---------|-----------|------|
| 多对一 | Team | CASCADE | 团队删除时成员记录也删除 |
| 多对一 | User | CASCADE | 用户删除时成员记录也删除 |

**运营需求支持:**
- ✅ REQ-6: 用户团队管理及身份
- ✅ REQ-36: 根据赛规筛选队伍（角色检测）

**使用示例:**

```python
# 添加团队成员
member = TeamMember.objects.create(
    team=team,
    user=user,
    role='hacker',
    is_leader=False
)

# 查询队长
leader = team.membership.filter(is_leader=True).first()

# 查询用户所在的所有团队
user_teams = user.team_memberships.select_related('team', 'team__hackathon')
for membership in user_teams:
    print(f"{membership.team.name} - {membership.get_role_display()}")
```

**相关模型:** Team, User

---

### 2.3 任务与提交

#### 2.3.1 Quest

**文件位置:** `synnovator/hackathons/models/quest.py:5`

**继承:** `models.Model`

**用途:** 代表 Dojo 风格的挑战任务，可独立存在或与黑客松关联。用于技能验证和用户活跃度维护。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 | 关联需求 |
|--------|------|------|--------|------|----------|
| `title` | CharField(200) | 是 | - | 任务名称 | - |
| `slug` | SlugField(200) | 是 | - | URL 标识符（全局唯一） | - |
| `description` | RichTextField | 是 | - | 挑战描述和目标 | - |
| `quest_type` | CharField(20) | 是 | - | 类型（见下文） | - |
| `difficulty` | CharField(20) | 是 | - | 难度（见下文） | - |
| `xp_reward` | PositiveInteger | 是 | 100 | 完成时奖励的 XP | REQ-11 |
| `estimated_time_minutes` | PositiveInteger | 是 | 60 | 预计完成时间（分钟） | - |
| `hackathon` | FK(HackathonPage) | 否 | NULL | 关联黑客松（为空则为全局任务） | - |
| `is_active` | Boolean | 是 | True | 是否可尝试 | - |
| `tags` | JSONField | 否 | [] | 技能标签 ['python', 'ML'] | REQ-11 |
| `created_at` | DateTimeField | 是 | auto | 创建时间 | - |
| `updated_at` | DateTimeField | 是 | auto | 更新时间 | - |

**任务类型 (quest_type choices):**
- `technical`: 技术型（Hacker）
- `commercial`: 商业型（Hustler）
- `operational`: 运营型（Hipster）
- `mixed`: 混合型

**难度 (difficulty choices):**
- `beginner`: 初级
- `intermediate`: 中级
- `advanced`: 高级
- `expert`: 专家级

**排序:** `['-created_at']` - 最新的任务优先

**关系映射:**

| 关系类型 | 关联模型 | 关系名 | 说明 |
|---------|---------|--------|------|
| 多对一 | HackathonPage | - | 可选关联（为 NULL 则为全局任务） |
| 一对多 | Submission | `submissions` | 提交记录 |

**关键方法:**

```python
def get_completion_rate(self) -> float:
    """计算完成此任务的用户百分比"""
    total_attempts = self.submissions.count()
    if total_attempts == 0:
        return 0
    completed = self.submissions.filter(verification_status='passed').count()
    return (completed / total_attempts) * 100
```

**注意:** 代码中使用 'passed' 但 Submission 模型实际使用 'verified'，这可能是个 bug。

**运营需求支持:**
- ✅ REQ-11: 用户任务完成情况（通过 submissions 反向关系）

**使用示例:**

```python
# 创建全局任务
quest = Quest.objects.create(
    title="Build a REST API",
    slug="build-rest-api",
    description="<p>Create a RESTful API using Django</p>",
    quest_type='technical',
    difficulty='intermediate',
    xp_reward=200,
    estimated_time_minutes=120,
    hackathon=None,  # 全局任务
    tags=['python', 'django', 'api']
)

# 创建黑客松特定任务
hackathon_quest = Quest.objects.create(
    title="AI Pitch Deck",
    slug="ai-pitch-deck",
    description="<p>Create a compelling pitch deck</p>",
    quest_type='commercial',
    difficulty='beginner',
    xp_reward=100,
    hackathon=hackathon,  # 关联黑客松
    tags=['presentation', 'business']
)

# 查询完成率
completion_rate = quest.get_completion_rate()
print(f"完成率: {completion_rate:.1f}%")
```

**相关模型:** HackathonPage, Submission, User

---

#### 2.3.2 Submission

**文件位置:** `synnovator/hackathons/models/submission.py:7`

**继承:** `models.Model`

**用途:** 代表对 Quest 或 Hackathon 的提交，支持多态关联和验证工作流。这是评审系统的核心模型。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 | 关联需求 |
|--------|------|------|--------|------|----------|
| `user` | FK(User) | 否 | NULL | 个人提交者（二选一） | REQ-5, 11 |
| `team` | FK(Team) | 否 | NULL | 团队提交者（二选一） | REQ-29 |
| `quest` | FK(Quest) | 否 | NULL | 提交目标（二选一） | REQ-11 |
| `hackathon` | FK(HackathonPage) | 否 | NULL | 提交目标（二选一） | REQ-29 |
| `submission_file` | FileField | 否 | NULL | 上传文件 | REQ-15, 16 |
| `submission_url` | URLField(500) | 否 | '' | 仓库/演示 URL | REQ-15 |
| `description` | TextField | 否 | '' | 提交说明 | REQ-15 |
| `verification_status` | CharField(20) | 是 | 'pending' | 状态（见下文） | REQ-15 |
| `score` | Decimal(6,2) | 否 | NULL | 评分（0-100） | REQ-15, 34 |
| `feedback` | TextField | 否 | '' | 审核反馈 | REQ-15 |
| `submitted_at` | DateTimeField | 是 | auto | 提交时间 | - |
| `verified_at` | DateTimeField | 否 | NULL | 验证完成时间 | REQ-15 |
| `verified_by` | FK(User) | 否 | NULL | 审核人员 | REQ-15 |
| `attempt_number` | PositiveInteger | 是 | 1 | 提交尝试次数 | - |

**验证状态 (verification_status choices):**
- `pending`: 待审核
- `verified`: 已验证
- `rejected`: 已拒绝

**数据完整性约束（clean 方法）:**

```python
def clean(self):
    # 1. 必须有且仅有一个提交者（user XOR team）
    if not ((self.user and not self.team) or (self.team and not self.user)):
        raise ValidationError("必须有一个用户或团队提交，不能同时存在")

    # 2. 必须有且仅有一个目标（quest XOR hackathon）
    if not ((self.quest and not self.hackathon) or (self.hackathon and not self.quest)):
        raise ValidationError("必须提交到任务或黑客松，不能同时存在")

    # 3. 必须至少有一个提交方式（file OR URL）
    if not self.submission_file and not self.submission_url:
        raise ValidationError("必须包含文件或 URL")
```

**数据库索引:**

```python
indexes = [
    models.Index(fields=['verification_status']),  # 高频查询
    models.Index(fields=['user', '-submitted_at']),  # 用户提交历史
    models.Index(fields=['team', '-submitted_at']),  # 团队提交历史
]
```

**排序:** `['-submitted_at']` - 最新提交优先

**关系映射:**

| 关系类型 | 关联模型 | on_delete | 说明 |
|---------|---------|-----------|------|
| 多对一 | User | SET_NULL | 用户删除时保留提交记录 |
| 多对一 | Team | CASCADE | 团队删除时提交也删除 |
| 多对一 | Quest | CASCADE | 任务删除时提交也删除 |
| 多对一 | HackathonPage | CASCADE | 黑客松删除时提交也删除 |
| 多对一 | User (verified_by) | SET_NULL | 审核员删除时保留记录 |

**Wagtail Admin 配置:**

```python
panels = [
    FieldPanel('verification_status'),
    FieldPanel('score'),
    FieldPanel('feedback'),
]
```

可在 Wagtail Admin Snippets 中注册为可管理项。

**运营需求支持:**
- ✅ REQ-5: 用户内容管理（查看用户提交）
- ✅ REQ-11: 用户任务完成情况
- ✅ REQ-15: 提案内容审核管理
- ✅ REQ-29: 查看活动提案信息
- ⚠️ REQ-34: 评审打分功能（当前只有一个 score 字段，缺少多评委独立评分）

**缺失功能（需扩展）:**
- ❌ 缺少 `copyright_declaration` 著作权声明（REQ-16）
- ❌ 缺少 `originality_check_status` 原创性检查（REQ-16）
- ❌ 缺少多评委独立评分（当前只有一个 score 字段）

**使用示例:**

```python
# 个人任务提交
from synnovator.hackathons.models import Submission

submission = Submission.objects.create(
    user=user,
    quest=quest,
    submission_url="https://github.com/user/project",
    description="My solution using PyTorch"
)

# 团队黑客松提交
team_submission = Submission.objects.create(
    team=team,
    hackathon=hackathon,
    submission_url="https://github.com/team/hackathon-project",
    description="AI-powered recommendation system"
)

# 审核流程
submission.verification_status = 'verified'
submission.score = 85.5
submission.feedback = "Excellent implementation, good documentation"
submission.verified_by = staff_user
submission.verified_at = timezone.now()
submission.save()

# 奖励 XP（如果是 quest 提交）
if submission.quest and submission.verification_status == 'verified':
    submission.user.award_xp(
        submission.quest.xp_reward,
        reason=f"Completed {submission.quest.title}"
    )

# 查询待审核提交
pending = Submission.objects.filter(
    verification_status='pending'
).select_related('user', 'team', 'quest', 'hackathon')
```

**相关模型:** User, Team, Quest, HackathonPage

---

### 2.4 用户模型

#### 2.4.1 User (Extended AbstractUser)

**文件位置:** `synnovator/users/models.py:5`

**继承:** `AbstractUser` (Django)

**用途:** 自定义用户模型，扩展黑客松特定字段，支持游戏化和团队匹配。

**扩展字段（在 AbstractUser 基础上）:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 | 关联需求 |
|--------|------|------|--------|------|----------|
| `preferred_role` | CharField(50) | 否 | '' | 偏好角色（见下文） | REQ-4, 6 |
| `bio` | TextField(500) | 否 | '' | 个人简介 | REQ-4 |
| `skills` | JSONField | 否 | [] | 技能列表 ['Python', 'React'] | REQ-4 |
| `xp_points` | PositiveInteger | 是 | 0 | 总经验值 | REQ-11 |
| `reputation_score` | Decimal(6,2) | 是 | 0.0 | 声誉分数（基于提交质量） | - |
| `level` | PositiveInteger | 是 | 1 | 用户等级（从 XP 推导） | REQ-11 |
| `profile_completed` | Boolean | 是 | False | 是否完成资料设置 | REQ-4 |
| `onboarding_completed_at` | DateTimeField | 否 | NULL | 入职完成时间 | - |
| `is_seeking_team` | Boolean | 是 | False | 是否在寻找团队 | REQ-13 |
| `notification_preferences` | JSONField | 否 | {} | 通知偏好设置 | REQ-37 |

**继承字段（from AbstractUser）:**
- `username`, `email`, `password`: 认证字段
- `first_name`, `last_name`: 姓名
- `is_staff`, `is_superuser`, `is_active`: 权限字段
- `date_joined`, `last_login`: 时间戳

**角色枚举 (preferred_role choices):**
- `hacker`: Hacker（工程师）
- `hipster`: Hipster（设计/UX）
- `hustler`: Hustler（商业/市场）
- `mentor`: Mentor（导师）
- `any`: 灵活

**关系映射:**

| 关系类型 | 关联模型 | 关系名 | 说明 |
|---------|---------|--------|------|
| 一对多 | Submission | `submissions` | 用户提交记录 |
| 一对多 | Submission | `verified_submissions` | 作为审核员的提交 |
| 多对多 | Team | `hackathon_teams` | 通过 TeamMember |

**关键方法:**

```python
def calculate_level(self) -> int:
    """从 XP 计算等级（每 100 XP 升一级）"""
    return (self.xp_points // 100) + 1
```

---

```python
def award_xp(self, points: int, reason: str = "") -> None:
    """增加 XP 并重新计算等级"""
    self.xp_points += points
    self.level = self.calculate_level()
    self.save()
    # 未来可以触发通知或成就系统
```

**示例:**
```python
user.award_xp(150, reason="Completed Python Quest")
print(f"Level: {user.level}, XP: {user.xp_points}")
```

---

```python
def get_verified_skills(self) -> list[str]:
    """返回通过任务完成验证的技能"""
    from synnovator.hackathons.models import Submission

    completed_quests = Submission.objects.filter(
        user=self,
        quest__isnull=False,
        verification_status='verified'
    ).select_related('quest')

    skills = set()
    for submission in completed_quests:
        if submission.quest and submission.quest.tags:
            skills.update(submission.quest.tags)
    return list(skills)
```

**示例:**
```python
verified_skills = user.get_verified_skills()
print(f"验证技能: {', '.join(verified_skills)}")
```

**配置:**
- `AUTH_USER_MODEL = "users.User"` (settings.py)

**运营需求支持:**
- ✅ REQ-4: 用户个人信息完整度（profile_completed, bio, skills）
- ✅ REQ-6: 用户团队管理（通过 team_memberships 反向关系）
- ✅ REQ-11: 用户任务完成情况（xp_points, level）
- ✅ REQ-13: 用户关注/队伍意向（is_seeking_team）

**缺失功能（需扩展）:**
- ❌ 缺少 `profile_completion_percentage` 计算属性
- ❌ 缺少活动参与历史缓存（如 `hackathons_participated_count`）
- ❌ 缺少社交功能（关注/粉丝）

**使用示例:**

```python
from synnovator.users.models import User

# 创建用户
user = User.objects.create_user(
    username='alice',
    email='alice@example.com',
    password='secure_password',
    preferred_role='hacker',
    bio='Passionate about AI and ML',
    skills=['Python', 'TensorFlow', 'Docker']
)

# 完成资料设置
user.profile_completed = True
user.save()

# 计算完整度
required_fields = ['bio', 'skills', 'preferred_role', 'email', 'first_name']
completed = sum(1 for f in required_fields if getattr(user, f))
completeness = (completed / len(required_fields)) * 100
print(f"资料完整度: {completeness}%")

# 奖励 XP
user.award_xp(200, reason="Completed first quest")

# 查询团队
user_teams = user.team_memberships.select_related('team')
for membership in user_teams:
    print(f"{membership.team.name} ({membership.get_role_display()})")
```

**相关模型:** Team, TeamMember, Submission, Quest

---

## 3. 内容管理模型 (CMS Models)

### 3.1 页面模型基类

#### 3.1.1 BasePage

**文件位置:** `synnovator/utils/models.py:306`

**继承:** `Page` + `SocialFields` + `ListingFields` (Wagtail Mixins)

**用途:** 所有 Wagtail 页面的抽象基类，提供 SEO 和社交分享字段。

**关键字段（来自 Mixins）:**

| 字段名 | 类型 | 来源 | 说明 |
|--------|------|------|------|
| `social_image` | FK(CustomImage) | SocialFields | 社交分享图片 |
| `social_text` | CharField(255) | SocialFields | 社交分享文本 |
| `listing_image` | FK(CustomImage) | ListingFields | 列表显示图片 |
| `listing_title` | CharField(255) | ListingFields | 列表标题 |
| `listing_summary` | CharField(255) | ListingFields | 列表摘要/SEO 描述 |
| `appear_in_search_results` | Boolean | BasePage | 是否出现在搜索结果 |

**关键属性:**

```python
@cached_property
def related_pages(self) -> QuerySet:
    """返回关联页面（通过 PageRelatedPage）"""
    ordered_page_pks = tuple(item.page_id for item in self.page_related_pages.all())
    return order_by_pk_position(
        Page.objects.live().public().specific(),
        pks=ordered_page_pks,
        exclude_non_matches=True,
    )
```

---

```python
@property
def plain_introduction(self) -> str:
    """返回 introduction 字段的纯文本版本"""
    # 去除 HTML 标签
    try:
        introduction_field = self._meta.get_field("introduction")
    except FieldDoesNotExist:
        pass
    else:
        introduction_value = getattr(self, "introduction", None)
        if introduction_value:
            if isinstance(introduction_field, RichTextField):
                soup = BeautifulSoup(expand_db_html(introduction_value), "html.parser")
                return soup.text
            else:
                return introduction_value
```

**子类:**
- HomePage
- ArticlePage
- NewsListingPage
- StandardPage（可能存在）
- IndexPage（可能存在）
- FormPage（可能存在）

**运营需求支持:**
- ✅ REQ-20: 首页海报展示（HomePage 使用 BasePage 字段）
- ✅ REQ-21: 官方帖子展示（ArticlePage 继承）

**使用示例:**

```python
# 获取页面的社交分享图片
page = ArticlePage.objects.first()
og_image = page.social_image or page.listing_image or page.cover_image

# 获取纯文本简介
plain_text = page.plain_introduction
```

**相关模型:** HomePage, ArticlePage, NewsListingPage, PageRelatedPage

---

### 3.2 具体页面类型

#### 3.2.1 HomePage

**文件位置:** `synnovator/home/models.py:11`

**继承:** `BasePage`

**用途:** 网站首页，支持灵活内容和精选页面。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `introduction` | TextField | 否 | '' | 主页介绍 |
| `hero_cta` | StreamField | 否 | [] | 主 CTA 按钮（link block, max 1） |
| `body` | StreamField | 否 | [] | 主页内容（StoryBlock） |
| `featured_section_title` | TextField | 否 | '' | 精选区域标题 |

**关系:**
- InlinePanel: `page_related_pages` (最多 12 个精选页面)

**模板:** `pages/home_page.html`

**运营需求支持:**
- ✅ REQ-20: 首页海报展示

**使用示例:**

```python
from synnovator.home.models import HomePage

home = HomePage.objects.first()
home.introduction = "Welcome to Synnovator"
home.featured_section_title = "Featured Hackathons"
home.save_revision().publish()
```

**相关模型:** BasePage, PageRelatedPage

---

#### 3.2.2 ArticlePage

**文件位置:** `synnovator/news/models.py:14`

**继承:** `BasePage`

**用途:** 新闻/博客文章页面。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `author` | FK(AuthorSnippet) | 是 | - | 文章作者 |
| `topic` | FK(ArticleTopic) | 是 | - | 文章分类 |
| `publication_date` | DateTimeField | 否 | NULL | 发布日期（覆盖） |
| `introduction` | TextField | 否 | '' | 文章摘要 |
| `image` | StreamField | 否 | [] | 文章主图（max 1） |
| `body` | StreamField | 是 | [] | 文章内容 |
| `featured_section_title` | TextField | 否 | '' | 精选区域标题 |

**父页面类型:** `news.NewsListingPage`

**关系:**
- InlinePanel: `page_related_pages` (最多 3 个相关文章)

**属性:**

```python
@property
def display_date(self):
    if self.publication_date:
        return self.publication_date.strftime("%d %b %Y")
    elif self.first_published_at:
        return self.first_published_at.strftime("%d %b %Y")
```

**模板:** `pages/article_page.html`

**运营需求支持:**
- ✅ REQ-21: 官方帖子展示
- ✅ REQ-23: 帖子审核（通过 Wagtail Page 状态管理）

**使用示例:**

```python
from synnovator.news.models import ArticlePage
from synnovator.utils.models import AuthorSnippet, ArticleTopic

author = AuthorSnippet.objects.first()
topic = ArticleTopic.objects.get(slug='announcements')

article = ArticlePage(
    title="AI Challenge Announcement",
    author=author,
    topic=topic,
    introduction="Join our AI challenge",
)
news_listing = NewsListingPage.objects.first()
news_listing.add_child(instance=article)
article.save_revision().publish()
```

**相关模型:** BasePage, AuthorSnippet, ArticleTopic, NewsListingPage

---

#### 3.2.3 NewsListingPage

**文件位置:** `synnovator/news/models.py:80`

**继承:** `BasePage`

**用途:** 新闻列表页面，自动显示子文章页面。

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `introduction` | RichTextField | 否 | '' | 列表页介绍 |

**限制:**
- `max_count = 1`: 全站只允许一个新闻列表页
- `subpage_types = ["news.ArticlePage"]`: 只能添加文章子页面

**模板:** `pages/news_listing_page.html`

**关键方法:**

```python
def get_context(self, request, *args, **kwargs):
    context = super().get_context(request, *args, **kwargs)

    # 查询所有文章
    queryset = (
        ArticlePage.objects.live()
        .public()
        .annotate(date=Coalesce("publication_date", "first_published_at"))
        .select_related("listing_image", "author", "topic")
        .order_by("-date")
    )

    # 主题筛选
    topic_query_param = request.GET.get("topic")
    if topic_query_param:
        queryset = queryset.filter(topic__slug=topic_query_param)

    # 分页
    paginator, page, _object_list, is_paginated = self.paginate_queryset(queryset, request)

    context.update({
        'paginator': paginator,
        'paginator_page': page,
        'is_paginated': is_paginated,
        'topics': article_topics,
        'matching_topic': matching_topic,
    })
    return context
```

**运营需求支持:**
- ✅ REQ-21: 官方帖子展示

**相关模型:** BasePage, ArticlePage, ArticleTopic

---

### 3.3 Snippet 模型

#### 3.3.1 AuthorSnippet

**文件位置:** `synnovator/utils/models.py:100`

**继承:** `TranslatableMixin` + `models.Model`

**注册:** `@register_snippet`

**用途:** 文章作者信息（可重用片段）。

**字段定义:**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `title` | CharField(255) | 是 | 作者名称 |
| `image` | FK(CustomImage) | 否 | 作者头像 |

**约束:**
- `unique_together = [("translation_key", "locale")]` - 国际化唯一约束

**特性:**
- 支持多语言
- 在 Wagtail Admin Snippets 中管理

**使用示例:**

```python
from synnovator.utils.models import AuthorSnippet

author = AuthorSnippet.objects.create(
    title="Alice Chen",
    image=image_obj
)
```

**相关模型:** ArticlePage, CustomImage

---

#### 3.3.2 ArticleTopic

**文件位置:** `synnovator/utils/models.py:118`

**继承:** `TranslatableMixin` + `models.Model`

**注册:** `@register_snippet`

**用途:** 文章分类标签。

**字段定义:**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `title` | CharField(255) | 是 | 主题名称 |
| `slug` | SlugField(255) | 是 | URL 标识符 |

**约束:**
- `unique_together = [("translation_key", "locale")]`

**特性:**
- 自动 slug 生成：保存时如果不存在 slug，则从 title 生成
- 支持冲突解决（自动添加数字后缀）

**关键方法:**

```python
def save(self, *args, **kwargs):
    if self._state.adding and not self.slug:
        self.slug = self.slugify(self.title)
        # ... 冲突解决逻辑
```

**使用示例:**

```python
from synnovator.utils.models import ArticleTopic

topic = ArticleTopic.objects.create(title="Announcements")
# slug 自动生成为 "announcements"
```

**相关模型:** ArticlePage, NewsListingPage

---

#### 3.3.3 Statistic

**文件位置:** `synnovator/utils/models.py:173`

**继承:** `TranslatableMixin` + `models.Model`

**注册:** `@register_snippet`

**用途:** 统计数字展示（用于首页等）。

**字段定义:**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `statistic` | CharField(12) | 是 | 数字（如 "1000+"） |
| `description` | CharField(225) | 是 | 说明（如 "Active Users"） |

**约束:**
- `unique_together = [("translation_key", "locale")]`

**使用示例:**

```python
from synnovator.utils.models import Statistic

stat = Statistic.objects.create(
    statistic="500+",
    description="Hackathons Hosted"
)
```

---

### 3.4 Settings 模型

#### 3.4.1 NavigationSettings

**文件位置:** `synnovator/navigation/models.py:14`

**继承:** `TranslatableMixin` + `BaseSiteSetting` + `ClusterableModel`

**注册:** `@register_setting(icon="list-ul")`

**用途:** 站点导航配置（全局设置）。

**字段定义:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `primary_navigation` | StreamField | 主导航（InternalLinkBlock） |
| `footer_navigation` | StreamField | 页脚导航（link_section blocks） |

**约束:**
- `unique_together = [("translation_key", "locale")]`

**特性:**
- 支持多语言
- 在 Wagtail Settings 中全局配置

**使用示例:**

```python
from synnovator.navigation.models import NavigationSettings
from wagtail.models import Locale

settings = NavigationSettings.objects.get(locale=Locale.get_active())
# 在模板中使用 {{ settings.navigation.NavigationSettings.primary_navigation }}
```

**相关模型:** Page

---

#### 3.4.2 SocialMediaSettings

**文件位置:** `synnovator/utils/models.py:190`

**继承:** `TranslatableMixin` + `BaseSiteSetting`

**注册:** `@register_setting`

**用途:** 社交媒体账户配置。

**字段定义:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `twitter_handle` | CharField(255) | Twitter 用户名 |
| `linkedin_handle` | CharField(255) | LinkedIn 用户名 |
| `instagram_handle` | CharField(255) | Instagram 用户名 |
| `tiktok_handle` | CharField(255) | TikTok 用户名 |
| `facebook_app_id` | CharField(255) | Facebook App ID |
| `default_sharing_text` | CharField(255) | 默认分享文本 |

**约束:**
- `unique_together = [("translation_key", "locale")]`

---

#### 3.4.3 SystemMessagesSettings

**文件位置:** `synnovator/utils/models.py:223`

**继承:** `TranslatableMixin` + `BaseSiteSetting`

**注册:** `@register_setting`

**用途:** 系统消息配置（404 页面、占位图等）。

**字段定义:**

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `title_404` | CharField(255) | "Page not found" | 404 页面标题 |
| `body_404` | RichTextField | (见代码) | 404 页面内容 |
| `placeholder_image` | FK(CustomImage) | NULL | 占位图像 |
| `footer_newsletter_signup_title` | CharField(120) | "Sign up..." | 通讯注册标题 |
| `footer_newsletter_signup_description` | CharField(255) | '' | 通讯注册描述 |
| `footer_newsletter_signup_link` | URLField | NULL | 通讯注册链接 |

**约束:**
- `unique_together = [("translation_key", "locale")]`

**关键方法:**

```python
def get_placeholder_image(self):
    """获取或创建占位图像"""
    if self.placeholder_image:
        return self.placeholder_image

    # 从 static files 加载默认图像
    absolute_path = find('images/placeholder-image.webp')
    if absolute_path:
        # ... 创建 CustomImage
        return self.placeholder_image
    raise ValidationError("No placeholder image found")
```

---

### 3.5 图像管理

#### 3.5.1 CustomImage

**文件位置:** `synnovator/images/models.py:9`

**继承:** `AbstractImage` (Wagtail)

**用途:** 自定义图像模型，扩展搜索字段。

**特性:**
- 扩展搜索字段：description
- 支持 Wagtail 图像管理

**使用示例:**

```python
from synnovator.images.models import CustomImage

image = CustomImage.objects.create(
    title="AI Challenge Banner",
    file=uploaded_file
)
```

**相关模型:** Rendition, HackathonPage, HomePage, ArticlePage

---

#### 3.5.2 Rendition

**文件位置:** `synnovator/images/models.py:15`

**继承:** `AbstractRendition` (Wagtail)

**用途:** 图像渲染变体（缩略图、裁剪等）。

**字段定义:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `image` | FK(CustomImage) | 源图像 |

**约束:**
- `unique_together = (("image", "filter_spec", "focal_point_key"),)`

**关键属性:**

```python
@property
def object_position_style(self):
    """返回 object-position CSS 规则"""
    focal_point = self.focal_point
    if focal_point:
        horz = int((focal_point.x * 100) // self.width)
        vert = int((focal_point.y * 100) // self.height)
        return f"object-position: {horz}% {vert}%;"
    else:
        return "object-position: 50% 50%;"
```

**相关模型:** CustomImage

---

### 3.6 辅助模型

#### 3.6.1 PageRelatedPage

**文件位置:** `synnovator/utils/models.py:28`

**继承:** `Orderable`

**用途:** Page 的多对多关系（用于精选页面）。

**字段定义:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `parent` | ParentalKey(Page) | 父页面 |
| `page` | FK(Page) | 关联页面 |

**使用场景:**
- HomePage 精选页面（最多 12 个）
- ArticlePage 相关文章（最多 3 个）

**使用示例:**

```python
# 添加精选页面
from synnovator.utils.models import PageRelatedPage

home = HomePage.objects.first()
hackathon = HackathonPage.objects.first()

PageRelatedPage.objects.create(parent=home, page=hackathon)
```

---

## 4. 辅助设计模式与技术细节

### 4.1 关键设计模式

#### 4.1.1 Through Model 模式

**示例:** TeamMember

**优势:**
- 在多对多关系中携带额外属性（role, is_leader, joined_at）
- 便于查询和统计
- 支持复杂的业务逻辑

**实现模式:**

```python
class Team(models.Model):
    members = models.ManyToManyField(
        User,
        through='TeamMember',
        related_name='hackathon_teams'
    )

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    is_leader = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['team', 'user']]
```

**查询示例:**

```python
# 查询用户的所有团队
user_teams = user.team_memberships.select_related('team')

# 查询团队的队长
leader = team.membership.filter(is_leader=True).first()
```

---

#### 4.1.2 多态关联模式

**示例:** Submission

**实现方式:**
- 使用可选外键（nullable ForeignKey）
- 在 `clean()` 方法中验证约束（XOR 逻辑）

**优势:**
- 统一的提交模型支持多种场景
- 避免重复的评审工作流代码
- 保持数据一致性

**实现模式:**

```python
class Submission(models.Model):
    # 提交者（二选一）
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE)

    # 目标（二选一）
    quest = models.ForeignKey(Quest, null=True, blank=True, on_delete=models.CASCADE)
    hackathon = models.ForeignKey(HackathonPage, null=True, blank=True, on_delete=models.CASCADE)

    def clean(self):
        # XOR 约束验证
        if not ((self.user and not self.team) or (self.team and not self.user)):
            raise ValidationError("必须有一个用户或团队提交")
        if not ((self.quest and not self.hackathon) or (self.hackathon and not self.quest)):
            raise ValidationError("必须提交到任务或黑客松")
```

**查询示例:**

```python
# 查询用户的所有提交
user_submissions = Submission.objects.filter(user=user)

# 查询团队的黑客松提交
team_hackathon_submissions = Submission.objects.filter(team=team, hackathon__isnull=False)
```

---

#### 4.1.3 JSONField 灵活配置

**示例:**
- `HackathonPage.required_roles`
- `User.skills`
- `Phase.requirements`

**适用场景:**
- 列表数据（无需外键关联）
- 配置数据（结构灵活）
- 动态字段

**优势:**
- 灵活性高
- 避免创建额外的关联表
- 支持 PostgreSQL JSON 查询

**注意事项:**
- PostgreSQL 支持 JSON 查询（`__contains`, `__has_key`）
- SQLite 支持有限
- 缺少外键级别的数据完整性验证

**使用示例:**

```python
# 配置必需角色
hackathon.required_roles = ['hacker', 'hustler']
hackathon.save()

# 查询包含特定角色的黑客松（PostgreSQL）
hackathons_need_hacker = HackathonPage.objects.filter(
    required_roles__contains=['hacker']
)

# 用户技能
user.skills = ['Python', 'Django', 'React']
user.save()

# 查询拥有特定技能的用户（PostgreSQL）
python_users = User.objects.filter(skills__contains=['Python'])
```

---

#### 4.1.4 InlinePanel 嵌套编辑

**示例:** Phase, Prize

**优势:**
- 在父页面编辑界面中管理子对象
- 提供拖拽排序功能
- 避免多次页面跳转

**实现模式:**

```python
# 子模型
class Phase(models.Model):
    hackathon = ParentalKey(
        'HackathonPage',
        on_delete=models.CASCADE,
        related_name='phases'
    )
    # ... 其他字段

# 父模型
class HackathonPage(Page):
    content_panels = Page.content_panels + [
        InlinePanel('phases', label="Hackathon Phases"),
        InlinePanel('prizes', label="Prizes"),
    ]
```

**管理员体验:**
- 在 HackathonPage 编辑界面直接添加/编辑 Phase
- 支持拖拽排序（基于 order 字段）
- 无需离开父页面

---

#### 4.1.5 TranslatableMixin 国际化

**使用模型:**
- AuthorSnippet, ArticleTopic, Statistic
- NavigationSettings, SocialMediaSettings, SystemMessagesSettings

**特性:**
- `unique_together = [("translation_key", "locale")]`
- Wagtail Localize 集成
- 支持内容翻译和同步

**实现模式:**

```python
from wagtail_localize.models import TranslatableMixin

class AuthorSnippet(TranslatableMixin, models.Model):
    title = models.CharField(max_length=255)

    class Meta:
        unique_together = [("translation_key", "locale")]
```

**查询示例:**

```python
from wagtail.models import Locale

# 获取当前语言的作者
current_locale = Locale.get_active()
authors = AuthorSnippet.objects.filter(locale=current_locale)

# 获取特定作者的所有翻译版本
author = AuthorSnippet.objects.first()
translations = AuthorSnippet.objects.filter(translation_key=author.translation_key)
```

---

### 4.2 数据库设计深度分析

#### 4.2.1 索引策略

**已有索引:**

```python
# Submission 模型
indexes = [
    models.Index(fields=['verification_status']),  # 高频查询
    models.Index(fields=['user', '-submitted_at']),  # 用户提交历史
    models.Index(fields=['team', '-submitted_at']),  # 团队提交历史
]
```

**建议新增索引:**

```python
# HackathonPage
class Meta:
    indexes = [
        models.Index(fields=['status']),  # 高频查询
        models.Index(fields=['-first_published_at']),  # 最新活动
    ]

# Team
class Meta:
    indexes = [
        models.Index(fields=['status']),  # 高频查询
        models.Index(fields=['hackathon', '-final_score']),  # 排行榜
        models.Index(fields=['is_seeking_members']),  # 组队页面
    ]

# User
class Meta:
    indexes = [
        models.Index(fields=['is_seeking_team']),  # 组队匹配
        models.Index(fields=['-xp_points']),  # 排名
    ]
```

**索引类型:**
- 单字段索引：用于等值查询和排序
- 复合索引：用于多字段查询（注意字段顺序）

**索引原则:**
1. 为高频查询字段添加索引
2. 为外键字段添加索引（Django 自动）
3. 为排序字段添加索引
4. 避免过多索引（影响写入性能）

---

#### 4.2.2 外键关系总结

**ForeignKey (普通):**
- HackathonPage.cover_image → CustomImage
- Team.hackathon → HackathonPage
- Submission.user → User

**ParentalKey (Wagtail):**
- Phase.hackathon → HackathonPage
- Prize.hackathon → HackathonPage

**ManyToManyField (Through):**
- Team.members ↔ User (through TeamMember)

**外键 on_delete 策略:**

| 关系 | on_delete | 原因 |
|------|-----------|------|
| Phase.hackathon | CASCADE | 黑客松删除时阶段也删除 |
| Team.hackathon | CASCADE | 黑客松删除时团队也删除 |
| Submission.team | CASCADE | 团队删除时提交也删除 |
| Submission.user | SET_NULL | 用户删除时保留提交记录 |
| ArticlePage.author | PROTECT | 有文章引用的作者不能删除 |

---

#### 4.2.3 数据完整性保证

**unique_together 约束:**

```python
# Team
unique_together = [['hackathon', 'slug']]  # 同一黑客松内团队 slug 唯一

# TeamMember
unique_together = [['team', 'user']]  # 用户不能重复加入同一团队

# AuthorSnippet
unique_together = [["translation_key", "locale"]]  # 国际化唯一约束
```

**clean() 方法验证:**

```python
# Submission
def clean(self):
    # 多态关联约束（XOR 逻辑）
    if not ((self.user and not self.team) or (self.team and not self.user)):
        raise ValidationError("必须有一个用户或团队提交")
```

**数据库级别约束:**
- `NOT NULL`: 必填字段
- `UNIQUE`: 唯一约束
- `CHECK`: 检查约束（如 PositiveIntegerField）
- `FOREIGN KEY`: 外键约束

---

## 5. 性能优化建议

### 5.1 查询优化

**select_related (一对一/多对一):**

```python
# 优化外键查询
teams = Team.objects.select_related('hackathon').all()
submissions = Submission.objects.select_related('user', 'team', 'quest', 'hackathon').all()
```

**prefetch_related (一对多/多对多):**

```python
# 优化反向关系查询
hackathons = HackathonPage.objects.prefetch_related('phases', 'prizes', 'teams').all()
teams = Team.objects.prefetch_related('members', 'membership').all()
```

**避免 N+1 问题:**

```python
# 错误：每次循环都查询数据库
for team in Team.objects.all():
    print(team.hackathon.title)  # N+1 问题

# 正确：使用 select_related
for team in Team.objects.select_related('hackathon').all():
    print(team.hackathon.title)
```

**复杂查询示例:**

```python
# 查询活动及其所有相关数据
hackathon = HackathonPage.objects.select_related(
    'cover_image'
).prefetch_related(
    'phases',
    'prizes',
    Prefetch('teams', queryset=Team.objects.select_related('leader').prefetch_related('members'))
).get(slug='ai-challenge')
```

---

### 5.2 缓存策略

**页面级缓存:**
- Wagtail 内置页面缓存
- 配置 `CACHE_CONTROL_S_MAXAGE`

**模型级缓存:**

```python
from django.utils.functional import cached_property

@cached_property
def related_pages(self):
    # 缓存关联页面查询结果
    return [rel.page for rel in self.page_related_pages.select_related('page')]
```

**排行榜缓存（建议使用 Redis）:**

```python
from django.core.cache import cache

# 缓存排行榜（5 分钟）
cache_key = f"leaderboard:{hackathon.id}"
leaderboard = cache.get(cache_key)
if not leaderboard:
    leaderboard = hackathon.get_leaderboard()
    cache.set(cache_key, leaderboard, 300)
```

**查询结果缓存:**

```python
# 缓存查询结果
cache_key = f"user_teams:{user.id}"
teams = cache.get(cache_key)
if not teams:
    teams = list(user.team_memberships.select_related('team'))
    cache.set(cache_key, teams, 600)
```

---

### 5.3 数据库维护

**定期 VACUUM (PostgreSQL):**

```bash
# 清理死元组，重建索引
python manage.py dbshell
VACUUM ANALYZE;
```

**索引重建:**

```bash
REINDEX DATABASE synnovator;
```

**查询性能分析:**

```python
from django.db import connection
from django.test.utils import override_settings

# 启用查询日志
with override_settings(DEBUG=True):
    # 执行查询
    teams = Team.objects.select_related('hackathon').all()

    # 查看执行的 SQL
    for query in connection.queries:
        print(query['sql'])
        print(f"Time: {query['time']}")
```

---

## 6. 迁移和版本控制

### 6.1 已执行迁移

**hackathons app:**
- `0001_initial.py` (2026-01-21): 创建 HackathonPage, Phase, Prize, Team, TeamMember, Quest, Submission

**users app:**
- `0001_initial.py`: 创建自定义 User 模型
- `0002_user_extended_fields.py`: 添加游戏化和偏好字段

**其他 apps:**
- home, news, images, utils, navigation 等均有初始迁移

### 6.2 迁移最佳实践

**命名规范:**

```
0001_initial.py
0002_add_field_name.py
0003_alter_model_name.py
0004_create_related_model.py
```

**数据迁移:**

```python
# 使用 RunPython 进行数据迁移
def populate_default_values(apps, schema_editor):
    Team = apps.get_model('hackathons', 'Team')
    for team in Team.objects.all():
        team.current_round = 1
        team.save()

class Migration(migrations.Migration):
    operations = [
        migrations.AddField('Team', 'current_round', ...),
        migrations.RunPython(populate_default_values),
    ]
```

**回滚测试:**

```bash
# 测试迁移可回滚
uv run python manage.py migrate hackathons 0001
uv run python manage.py migrate hackathons
```

---

## 7. 附录

### 7.1 字段类型参考表

| Django 字段 | 数据库类型 | Python 类型 | 说明 |
|------------|-----------|------------|------|
| CharField | VARCHAR | str | 有限长度字符串 |
| TextField | TEXT | str | 无限长度文本 |
| RichTextField (Wagtail) | TEXT | str | 富文本（存储 HTML） |
| IntegerField | INTEGER | int | 整数 |
| PositiveIntegerField | INTEGER (CHECK >= 0) | int | 非负整数 |
| DecimalField | NUMERIC | Decimal | 定点数（财务/评分） |
| BooleanField | BOOLEAN | bool | 布尔值 |
| DateTimeField | TIMESTAMP | datetime | 日期时间（UTC） |
| JSONField | JSON/JSONB | dict/list | JSON 数据 |
| ForeignKey | INTEGER (外键约束) | Model | 多对一关系 |
| ManyToManyField | 关联表 | QuerySet | 多对多关系 |
| FileField | VARCHAR | File | 文件路径 |
| URLField | VARCHAR | str | URL 验证 |
| SlugField | VARCHAR | str | URL 友好字符串 |

---

### 7.2 关系类型快速查询

| 关系类型 | 定义位置 | 访问方式 | 反向访问 |
|---------|---------|---------|---------|
| ForeignKey | 多方 | `obj.foreign_key` | `obj.related_name.all()` |
| ParentalKey | 多方 | `obj.parental_key` | `obj.related_name.all()` |
| ManyToManyField | 任意一方 | `obj.m2m_field.all()` | `obj.related_name.all()` |
| OneToOneField | 任意一方 | `obj.one_to_one` | `obj.related_name` |

---

### 7.3 常用查询模式代码片段

**查询活动中的所有团队:**

```python
teams = Team.objects.filter(
    hackathon=hackathon,
    status__in=['ready', 'submitted']
).select_related('hackathon').prefetch_related('members')
```

**查询用户的所有完成任务:**

```python
completed_quests = Quest.objects.filter(
    submissions__user=user,
    submissions__verification_status='verified'
).distinct()
```

**查询需要审核的提交:**

```python
pending_submissions = Submission.objects.filter(
    verification_status='pending'
).select_related('user', 'team', 'quest', 'hackathon').order_by('submitted_at')
```

**查询排行榜:**

```python
leaderboard = Team.objects.filter(
    hackathon=hackathon,
    status__in=['submitted', 'verified']
).order_by('-final_score')[:10]
```

**查询用户的团队:**

```python
user_teams = user.team_memberships.select_related('team', 'team__hackathon')
for membership in user_teams:
    print(f"{membership.team.name} ({membership.get_role_display()})")
```

---

### 7.4 术语表

| 术语 | 说明 |
|------|------|
| **Events as Code** | 将赛事配置以代码形式管理，支持版本控制和复用 |
| **3H 模型** | Hacker (技术) + Hipster (设计) + Hustler (商业) 的跨职能团队模式 |
| **Dojo/Quest** | 高频微型挑战任务，用于维持用户日常活跃度 |
| **OPC 团队** | Operations (运营) + Product/Commercial (商业) + Technology (技术) 的小型创业团队 |
| **Through Model** | Django 多对多关系的中间模型，可携带额外属性 |
| **ParentalKey** | Wagtail 的特殊外键，支持 InlinePanel 嵌套编辑 |
| **StreamField** | Wagtail 的灵活内容字段，支持多种 Block 类型 |
| **Snippet** | Wagtail 的可复用内容片段（非页面） |
| **TranslatableMixin** | Wagtail 国际化混入类 |
| **XOR (Exclusive OR)** | 互斥或逻辑，用于多态关联约束 |

---

### 7.5 模型速查索引

**按应用分类:**

- **hackathons**: HackathonPage, Phase, Prize, Team, TeamMember, Quest, Submission
- **users**: User
- **home**: HomePage
- **news**: ArticlePage, NewsListingPage
- **images**: CustomImage, Rendition
- **utils**: BasePage, AuthorSnippet, ArticleTopic, Statistic, PageRelatedPage, SocialMediaSettings, SystemMessagesSettings
- **navigation**: NavigationSettings

**按功能分类:**

- **活动管理**: HackathonPage, Phase, Prize
- **团队管理**: Team, TeamMember
- **任务系统**: Quest, Submission
- **用户系统**: User
- **内容管理**: HomePage, ArticlePage, NewsListingPage
- **媒体管理**: CustomImage, Rendition

---

## 8. 总结

### 8.1 核心亮点

1. **Events as Code 架构**: 通过 Wagtail CMS 实现活动配置即代码
2. **灵活的多态关联**: Submission 支持多种提交场景
3. **游戏化系统**: XP/Level/Quest 激励用户参与
4. **多维度评分**: 技术/商业/运营三维评估
5. **国际化支持**: TranslatableMixin 提供多语言能力

### 8.2 已知限制

1. **手动状态管理**: HackathonPage.status 需手动更新
2. **缺少晋级历史**: 没有专门的模型记录晋级/淘汰决策
3. **单一评分字段**: Submission.score 不支持多评委独立评分
4. **缺少社交功能**: 没有评论、点赞、关注等模型

### 8.3 优化方向

1. 添加自动状态转换（基于 Phase 时间）
2. 创建 AdvancementLog 模型记录晋级历史
3. 扩展多评委评分系统
4. 添加社交互动功能（评论、点赞）
5. 实现通知系统

---

**文档维护说明:**

本文档应在每次数据库迁移后更新。更新时请：
1. 更新版本号和最后更新日期
2. 添加新增模型的完整说明
3. 更新关系映射图
4. 添加新的使用示例
5. 更新运营需求支持情况

**相关文档:**
- [model-relationships.mmd](./model-relationships.mmd) - ER 图
- [requirements-coverage.md](../operational/requirements-coverage.md) - 运营需求覆盖分析
- [translation-guide.md](../translation-guide.md) - 国际化指南
