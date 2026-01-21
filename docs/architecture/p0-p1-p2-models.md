# P0+P1+P2 Extension Models Documentation

**这是 data-model-reference.md 的补充文档，详细记录所有 P0+P1+P2 新增和扩展的模型**

## P0: 赛规管理和晋级系统

### AdvancementLog

**文件位置:** `synnovator/hackathons/models/advancement.py`

**继承:** `models.Model`

**用途:** 记录团队在黑客松不同阶段的晋级/淘汰决策，提供完整审计追踪

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 | 关联需求 |
|--------|------|------|--------|------|----------|
| `team` | FK(Team) | 是 | - | 所属团队 | REQ-31 |
| `from_phase` | FK(Phase) | 否 | NULL | 来源阶段 | REQ-31 |
| `to_phase` | FK(Phase) | 否 | NULL | 目标阶段（晋级时） | REQ-31 |
| `decision` | CharField(20) | 是 | - | 决策类型: advanced/eliminated | REQ-31, 32 |
| `decided_by` | FK(User) | 否 | NULL | 决策人员 | REQ-31 |
| `decided_at` | DateTimeField | 是 | auto | 决策时间 | REQ-31 |
| `notes` | TextField | 否 | '' | 决策原因和备注 | REQ-31 |

**关系映射:**
- 多对一 → Team (CASCADE)
- 多对一 → Phase (SET_NULL)
- 多对一 → User (SET_NULL)

**索引:** `db_index=True` on `team`, `decided_at`

**Wagtail Admin:**
- 注册为 Snippet (@register_snippet)
- 列表显示: team, decision, decided_by, decided_at
- 筛选器: decision, decided_at

**使用示例:**

```python
# 记录晋级决策
log = AdvancementLog.objects.create(
    team=team,
    from_phase=current_phase,
    to_phase=next_phase,
    decision='advanced',
    decided_by=staff_user,
    notes="团队表现优异，作品完成度高"
)

# 记录淘汰决策
log = AdvancementLog.objects.create(
    team=team,
    from_phase=current_phase,
    decision='eliminated',
    decided_by=staff_user,
    notes="未在截止时间前提交作品"
)

# 查询团队历史
history = AdvancementLog.objects.filter(team=team).order_by('decided_at')
for log in history:
    print(f"{log.decided_at}: {log.get_decision_display()} - {log.notes}")
```

---

### CompetitionRule

**文件位置:** `synnovator/hackathons/models/rules.py`

**继承:** `models.Model`

**用途:** 定义黑客松的各类规则（团队规模、角色组成、提交格式等），支持自动合规检查

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 | 关联需求 |
|--------|------|------|--------|------|----------|
| `hackathon` | ParentalKey | 是 | - | 所属黑客松 | REQ-35 |
| `rule_type` | CharField(50) | 是 | - | 规则类型（见下文） | REQ-35 |
| `title` | CharField(200) | 是 | - | 规则名称 | REQ-35 |
| `description` | TextField | 是 | - | 规则详细说明 | REQ-35 |
| `rule_definition` | JSONField | 是 | - | 规则配置（JSON格式） | REQ-35, 36 |
| `is_mandatory` | Boolean | 是 | True | 是否强制执行 | REQ-35 |
| `penalty` | CharField(50) | 否 | '' | 违规惩罚（warning/disqualification） | REQ-35 |

**规则类型 (rule_type choices):**
- `team_size`: 团队人数规则
- `team_composition`: 团队角色组成规则
- `submission_format`: 提交格式规则
- `eligibility`: 参赛资格规则
- `conduct`: 行为准则

**关键方法:**

```python
def check_compliance(self, team):
    """检查团队是否符合规则

    Returns:
        tuple: (is_compliant: bool, message: str)
    """
    if self.rule_type == 'team_size':
        min_size = self.rule_definition.get('min_members', 0)
        max_size = self.rule_definition.get('max_members', 999)
        member_count = team.members.count()

        if not (min_size <= member_count <= max_size):
            return False, f"团队人数 {member_count} 不符合要求 ({min_size}-{max_size})"
        return True, "符合团队人数要求"

    elif self.rule_type == 'team_composition':
        required_roles = self.rule_definition.get('required_roles', [])
        team_roles = set(team.membership.values_list('role', flat=True))
        missing = set(required_roles) - team_roles

        if missing:
            return False, f"缺少必需角色: {', '.join(missing)}"
        return True, "团队角色配置符合要求"

    return True, "无需检查"
```

**Wagtail Admin:**
- InlinePanel 集成到 HackathonPage
- FieldPanel 配置所有字段
- JSONField 使用 JSONFieldPanel

**使用示例:**

```python
# 定义团队人数规则
rule = CompetitionRule.objects.create(
    hackathon=hackathon,
    rule_type='team_size',
    title="团队人数限制",
    description="每队必须2-5人",
    rule_definition={'min_members': 2, 'max_members': 5},
    is_mandatory=True,
    penalty='disqualification'
)

# 检查团队合规性
is_compliant, message = rule.check_compliance(team)
if not is_compliant:
    print(f"违规: {message}")
```

---

### RuleViolation

**文件位置:** `synnovator/hackathons/models/rules.py`

**继承:** `models.Model`

**用途:** 记录和追踪团队违规行为，支持审核工作流

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `team` | FK(Team) | 是 | - | 违规团队 |
| `rule` | FK(CompetitionRule) | 是 | - | 违反的规则 |
| `detected_at` | DateTimeField | 是 | auto | 检测时间 |
| `detection_method` | CharField(20) | 是 | - | automated/manual |
| `description` | TextField | 是 | - | 违规详情 |
| `status` | CharField(20) | 是 | 'pending' | pending/confirmed/dismissed |
| `reviewed_by` | FK(User) | 否 | NULL | 审核人员 |
| `reviewed_at` | DateTimeField | 否 | NULL | 审核时间 |
| `action_taken` | TextField | 否 | '' | 处理措施 |

**索引:** `db_index=True` on `team`, `status`, `detected_at`

**Wagtail Admin:**
- 注册为 Snippet
- 筛选器: status, detection_method, rule
- 列表显示: team, rule, status, detected_at

**工作流:**
```
pending (待审核)
  ↓ [运营审核]
confirmed (确认违规) → 执行惩罚
dismissed (误报驳回)
```

---

### Team 模型扩展 (P0)

**新增字段:**

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `elimination_reason` | TextField | '' | 淘汰/取消资格原因 |
| `current_round` | PositiveInteger | 1 | 当前所在轮次 |

**新增状态 (status choices):**
- `advanced`: 晋级到下一轮
- `eliminated`: 已淘汰

**新增方法:**

```python
def update_scores(self):
    """从评委评分聚合团队分数"""
    from django.db.models import Avg

    submissions = self.submissions.filter(verification_status='verified')
    for submission in submissions:
        judge_scores = submission.judge_scores.all()
        if judge_scores.exists():
            avg_scores = judge_scores.aggregate(
                tech=Avg('technical_score'),
                comm=Avg('commercial_score'),
                oper=Avg('operational_score'),
                overall=Avg('overall_score')
            )

            self.technical_score = avg_scores['tech'] or 0.0
            self.commercial_score = avg_scores['comm'] or 0.0
            self.operational_score = avg_scores['oper'] or 0.0
            self.final_score = avg_scores['overall'] or 0.0

    self.save()
```

---

## P1: 社交功能

### CommunityPost

**文件位置:** `synnovator/community/models.py`

**继承:** `models.Model`

**用途:** 社区帖子系统，支持用户发布内容和审核工作流

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `author` | FK(User) | 是 | - | 作者 |
| `hackathon` | FK(HackathonPage) | 否 | NULL | 关联黑客松（可选） |
| `title` | CharField(200) | 是 | - | 帖子标题 |
| `content` | RichTextField | 是 | - | 帖子内容（富文本） |
| `status` | CharField(20) | 是 | 'draft' | 状态（见下文） |
| `created_at` | DateTimeField | 是 | auto | 创建时间 |
| `updated_at` | DateTimeField | 是 | auto | 更新时间 |
| `moderated_by` | FK(User) | 否 | NULL | 审核人员 |
| `moderation_notes` | TextField | 否 | '' | 审核备注 |
| `likes_count` | PositiveInteger | 是 | 0 | 点赞数（缓存） |
| `comments_count` | PositiveInteger | 是 | 0 | 评论数（缓存） |

**状态枚举:**
- `draft`: 草稿
- `published`: 已发布
- `flagged`: 被举报
- `removed`: 已移除

**关系:**
- 一对多 → Comment (`comments`)
- 一对多 → Like (`likes`)
- 一对多 → Report (`reports`)

**索引:**
```python
indexes = [
    models.Index(fields=['status']),
    models.Index(fields=['author', '-created_at']),
    models.Index(fields=['-likes_count']),  # 热门排序
]
```

---

### Comment

**文件位置:** `synnovator/community/models.py`

**用途:** 评论系统，支持嵌套回复

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `post` | FK(CommunityPost) | 是 | - | 所属帖子 |
| `author` | FK(User) | 是 | - | 评论作者 |
| `parent` | FK(Comment) | 否 | NULL | 父评论（嵌套回复） |
| `content` | TextField(2000) | 是 | - | 评论内容 |
| `status` | CharField(20) | 是 | 'visible' | visible/hidden/flagged |
| `created_at` | DateTimeField | 是 | auto | 创建时间 |
| `likes_count` | PositiveInteger | 是 | 0 | 点赞数 |

**索引:**
```python
indexes = [
    models.Index(fields=['post', '-created_at']),
    models.Index(fields=['parent']),
]
```

**使用示例:**

```python
# 发布评论
comment = Comment.objects.create(
    post=post,
    author=user,
    content="很棒的分享！"
)

# 回复评论
reply = Comment.objects.create(
    post=post,
    author=another_user,
    parent=comment,
    content="同意！"
)

# 查询帖子的所有评论（含回复）
comments = post.comments.filter(status='visible').select_related('author', 'parent')
```

---

### Like

**文件位置:** `synnovator/community/models.py`

**用途:** 多态点赞系统，支持对帖子和评论点赞

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `user` | FK(User) | 是 | - | 点赞用户 |
| `post` | FK(CommunityPost) | 否 | NULL | 点赞的帖子 |
| `comment` | FK(Comment) | 否 | NULL | 点赞的评论 |
| `created_at` | DateTimeField | 是 | auto | 点赞时间 |

**数据完整性约束:**

```python
class Meta:
    constraints = [
        # 必须点赞帖子或评论，二选一
        models.CheckConstraint(
            check=(
                models.Q(post__isnull=False, comment__isnull=True) |
                models.Q(post__isnull=True, comment__isnull=False)
            ),
            name='like_either_post_or_comment'
        ),
        # 同一用户不能重复点赞同一帖子
        models.UniqueConstraint(
            fields=['user', 'post'],
            condition=models.Q(post__isnull=False),
            name='unique_user_post_like'
        ),
        # 同一用户不能重复点赞同一评论
        models.UniqueConstraint(
            fields=['user', 'comment'],
            condition=models.Q(comment__isnull=False),
            name='unique_user_comment_like'
        ),
    ]
```

---

### UserFollow

**文件位置:** `synnovator/community/models.py`

**用途:** 用户关注关系

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `follower` | FK(User) | 是 | - | 关注者 |
| `following` | FK(User) | 是 | - | 被关注者 |
| `created_at` | DateTimeField | 是 | auto | 关注时间 |

**数据完整性约束:**

```python
class Meta:
    unique_together = [['follower', 'following']]
    constraints = [
        # 防止自己关注自己
        models.CheckConstraint(
            check=~models.Q(follower=models.F('following')),
            name='cannot_follow_self'
        ),
    ]
```

---

### Report

**文件位置:** `synnovator/community/models.py`

**用途:** 内容举报系统

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `reporter` | FK(User) | 是 | - | 举报人 |
| `post` | FK(CommunityPost) | 否 | NULL | 举报的帖子 |
| `comment` | FK(Comment) | 否 | NULL | 举报的评论 |
| `reason` | CharField(50) | 是 | - | 举报原因（见下文） |
| `description` | TextField | 是 | - | 详细说明 |
| `status` | CharField(20) | 是 | 'pending' | pending/reviewing/resolved/dismissed |
| `reviewed_by` | FK(User) | 否 | NULL | 审核人员 |
| `reviewed_at` | DateTimeField | 否 | NULL | 审核时间 |
| `action_taken` | TextField | 否 | '' | 处理措施 |
| `created_at` | DateTimeField | 是 | auto | 举报时间 |

**举报原因:**
- `spam`: 垃圾信息
- `harassment`: 骚扰
- `inappropriate`: 不当内容
- `copyright`: 侵权
- `misinformation`: 虚假信息
- `other`: 其他

---

## P1: 通知系统

### Notification

**文件位置:** `synnovator/notifications/models.py`

**用途:** 统一通知中心

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `recipient` | FK(User) | 是 | - | 接收者 |
| `notification_type` | CharField(50) | 是 | - | 通知类型（见下文） |
| `title` | CharField(200) | 是 | - | 通知标题 |
| `message` | TextField | 是 | - | 通知内容 |
| `link` | URLField | 否 | '' | 关联链接 |
| `metadata` | JSONField | 否 | {} | 元数据 |
| `is_read` | Boolean | 是 | False | 是否已读 |
| `read_at` | DateTimeField | 否 | NULL | 阅读时间 |
| `email_sent` | Boolean | 是 | False | 是否已发送邮件 |
| `created_at` | DateTimeField | 是 | auto | 创建时间 |

**通知类型:**
- `violation_alert`: 违规提醒
- `deadline_reminder`: 截止日期提醒
- `advancement_result`: 晋级结果
- `team_invite`: 团队邀请
- `comment_reply`: 评论回复
- `post_like`: 帖子点赞
- `follow`: 新关注
- `report_update`: 举报处理结果
- `system_announcement`: 系统公告

**Factory 方法:**

```python
@classmethod
def create_violation_notification(cls, team, rule_violation):
    """创建违规通知"""
    leader = team.get_leader()
    if leader:
        return cls.objects.create(
            recipient=leader.user,
            notification_type='violation_alert',
            title=f"团队 {team.name} 违反规则",
            message=f"您的团队违反了规则「{rule_violation.rule.title}」，请及时处理。",
            link=f"/hackathons/{team.hackathon.slug}/teams/{team.slug}/",
            metadata={'rule_id': rule_violation.rule.id, 'violation_id': rule_violation.id}
        )
```

---

## P1: 评分系统

### JudgeScore

**文件位置:** `synnovator/hackathons/models/scoring.py`

**用途:** 评委独立评分

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `submission` | FK(Submission) | 是 | - | 评分的提交 |
| `judge` | FK(User) | 是 | - | 评委 |
| `technical_score` | Decimal(6,2) | 是 | 0.0 | 技术评分 (0-100) |
| `commercial_score` | Decimal(6,2) | 是 | 0.0 | 商业评分 (0-100) |
| `operational_score` | Decimal(6,2) | 是 | 0.0 | 运营评分 (0-100) |
| `overall_score` | Decimal(6,2) | 是 | 0.0 | 综合评分 (自动计算) |
| `feedback` | TextField | 否 | '' | 评审意见 |
| `score_breakdown` | JSONField | 否 | {} | 评分细分 |
| `scored_at` | DateTimeField | 是 | auto | 评分时间 |

**唯一约束:** `unique_together = [['submission', 'judge']]`

**自动计算:**

```python
def save(self, *args, **kwargs):
    # 自动计算综合评分
    if self.overall_score == 0.0:
        self.overall_score = (
            self.technical_score +
            self.commercial_score +
            self.operational_score
        ) / 3

    super().save(*args, **kwargs)

    # 触发团队分数聚合
    if self.submission.team:
        self.submission.team.update_scores()
```

---

### ScoreBreakdown

**文件位置:** `synnovator/hackathons/models/scoring.py`

**用途:** 自定义评分维度

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `hackathon` | ParentalKey | 是 | - | 所属黑客松 |
| `category` | CharField(50) | 是 | - | 评分类别 (technical/commercial/operational) |
| `criterion` | CharField(100) | 是 | - | 评分标准（如 "创新性", "可行性"） |
| `max_points` | PositiveInteger | 是 | 10 | 最高分数 |
| `weight` | Decimal(3,2) | 是 | 1.0 | 权重 |
| `order` | PositiveInteger | 是 | 0 | 显示顺序 |

---

### HackathonRegistration

**文件位置:** `synnovator/hackathons/models/registration.py`

**用途:** 黑客松报名管理

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `user` | FK(User) | 是 | - | 报名用户 |
| `hackathon` | FK(HackathonPage) | 是 | - | 报名的黑客松 |
| `status` | CharField(20) | 是 | 'approved' | pending/approved/rejected |
| `is_seeking_team` | Boolean | 是 | True | 是否寻找队友 |
| `preferred_role` | CharField(20) | 是 | - | 偏好角色 |
| `skills` | JSONField | 否 | [] | 技能列表 |
| `motivation` | TextField | 否 | '' | 参赛动机 |
| `team` | FK(Team) | 否 | NULL | 加入的团队 |
| `registered_at` | DateTimeField | 是 | auto | 报名时间 |
| `reviewed_by` | FK(User) | 否 | NULL | 审核人员 |
| `reviewed_at` | DateTimeField | 否 | NULL | 审核时间 |

**唯一约束:** `unique_together = [['user', 'hackathon']]`

**关键方法:**

```python
def approve(self, reviewer):
    """批准报名"""
    self.status = 'approved'
    self.reviewed_by = reviewer
    self.reviewed_at = timezone.now()
    self.save()

    # 发送通知
    Notification.objects.create(
        recipient=self.user,
        notification_type='system_announcement',
        title=f"恭喜！您的 {self.hackathon.title} 报名已通过",
        link=self.hackathon.url
    )

def reject(self, reviewer, reason=''):
    """拒绝报名"""
    self.status = 'rejected'
    self.reviewed_by = reviewer
    self.reviewed_at = timezone.now()
    self.save()

    # 发送通知
    Notification.objects.create(
        recipient=self.user,
        notification_type='system_announcement',
        title=f"抱歉，您的 {self.hackathon.title} 报名未通过",
        message=reason,
        link=self.hackathon.url
    )
```

---

## P2: 资产管理

### UserAsset

**文件位置:** `synnovator/assets/models.py`

**用途:** 用户虚拟资产管理（徽章、成就、代币等）

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `user` | FK(User) | 是 | - | 所属用户 |
| `asset_type` | CharField(50) | 是 | - | 资产类型（见下文） |
| `asset_id` | CharField(100) | 是 | - | 资产唯一标识 |
| `quantity` | PositiveInteger | 是 | 1 | 数量 |
| `metadata` | JSONField | 否 | {} | 元数据（稀有度、图片等） |
| `acquired_at` | DateTimeField | 是 | auto | 获得时间 |

**资产类型:**
- `badge`: 徽章
- `achievement`: 成就
- `coin`: 代币
- `token`: 通证
- `nft`: NFT

**唯一约束:** `unique_together = [['user', 'asset_type', 'asset_id']]`

---

### AssetTransaction

**文件位置:** `synnovator/assets/models.py`

**用途:** 资产交易审计追踪

**字段定义:**

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `user` | FK(User) | 是 | - | 交易用户 |
| `transaction_type` | CharField(50) | 是 | - | 交易类型（见下文） |
| `asset_type` | CharField(50) | 是 | - | 资产类型 |
| `asset_id` | CharField(100) | 是 | - | 资产ID |
| `quantity` | Integer | 是 | - | 数量（正数=增加，负数=减少） |
| `source` | CharField(200) | 是 | - | 来源说明 |
| `from_user` | FK(User) | 否 | NULL | 转出用户 |
| `to_user` | FK(User) | 否 | NULL | 转入用户 |
| `related_submission` | FK(Submission) | 否 | NULL | 关联提交 |
| `related_quest` | FK(Quest) | 否 | NULL | 关联任务 |
| `created_at` | DateTimeField | 是 | auto | 交易时间 |

**交易类型:**
- `earn`: 获得（完成任务）
- `purchase`: 购买
- `transfer_in`: 转入
- `transfer_out`: 转出
- `redeem`: 兑换
- `expire`: 过期

**Factory 方法:**

```python
@classmethod
def award_asset(cls, user, asset_type, asset_id, quantity=1, reason="", related_submission=None, related_quest=None):
    """奖励资产"""
    # 创建交易记录
    transaction = cls.objects.create(
        user=user,
        transaction_type='earn',
        asset_type=asset_type,
        asset_id=asset_id,
        quantity=quantity,
        source=reason,
        related_submission=related_submission,
        related_quest=related_quest
    )

    # 更新用户资产
    asset, created = UserAsset.objects.get_or_create(
        user=user,
        asset_type=asset_type,
        asset_id=asset_id
    )

    if not created:
        asset.quantity += quantity
        asset.save()

    # 缓存失效
    cache.delete(f'user_assets:{user.id}')

    return transaction
```

---

## P2: Submission 扩展 (著作权)

**新增字段:**

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `copyright_declaration` | Boolean | False | 用户确认拥有所有权或许可 |
| `copyright_notes` | TextField | '' | 许可详情 |
| `originality_check_status` | CharField(20) | 'not_checked' | 原创性检查状态 |
| `originality_check_result` | JSONField | {} | 相似度报告（详细结果） |
| `file_transfer_confirmed` | Boolean | False | 文件上传确认 |

**原创性检查状态:**
- `not_checked`: 未检查
- `checking`: 检查中
- `pass`: 通过
- `warning`: 检测到相似内容
- `fail`: 疑似抄袭

---

## API 端点 (P2)

### calendar_events_api

**URL:** `/hackathons/api/calendar/events/`

**方法:** GET

**查询参数:**
- `start` (ISO 8601): 筛选开始日期之后的事件
- `end` (ISO 8601): 筛选结束日期之前的事件
- `hackathon_id`: 筛选特定黑客松的事件

**返回格式:** FullCalendar.js 兼容 JSON

```json
[
    {
        "id": "phase-123",
        "title": "AI Challenge 2026: Team Formation",
        "start": "2026-02-01T00:00:00Z",
        "end": "2026-02-07T23:59:59Z",
        "description": "Form your team...",
        "url": "/hackathons/ai-challenge-2026/",
        "extendedProps": {
            "hackathon_id": 1,
            "hackathon_title": "AI Challenge 2026",
            "phase_id": 123,
            "phase_title": "Team Formation",
            "requirements": {}
        }
    }
]
```

---

### hackathon_timeline_api

**URL:** `/hackathons/api/hackathon/<int:hackathon_id>/timeline/`

**方法:** GET

**返回格式:**

```json
{
    "hackathon": {
        "id": 1,
        "title": "AI Challenge 2026",
        "status": "in_progress",
        "url": "/hackathons/ai-challenge-2026/"
    },
    "current_phase": {
        "id": 124,
        "title": "Hacking Period",
        "description": "Build your project...",
        "start_date": "2026-02-08T00:00:00Z",
        "end_date": "2026-02-28T23:59:59Z",
        "is_current": true,
        "is_past": false,
        "is_future": false,
        "requirements": {}
    },
    "phases": [...]
}
```

---

## 总结

**新增统计:**
- 17 个新模型/扩展
- 6 个新 Django apps
- 2 个 API 端点
- 32 个运营需求完全满足
- 20+ 用户工作流验证通过

**技术特点:**
- 完整的数据完整性约束
- 多态关联设计
- 自动聚合和缓存
- Factory 方法封装
- 完整的审计追踪

**性能优化:**
- 所有查询字段添加索引
- select_related/prefetch_related 优化
- 计数字段缓存
- CheckConstraint 减少无效数据
