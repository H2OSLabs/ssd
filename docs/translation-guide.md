# 翻译指南 / Translation Guide

本文档介绍如何在Synnovator平台中进行翻译工作。

## 目录

- [概述](#概述)
- [UI翻译流程](#ui翻译流程)
- [内容翻译流程](#内容翻译流程)
- [翻译文件格式](#翻译文件格式)
- [验证翻译](#验证翻译)
- [常见问题](#常见问题)

## 概述

Synnovator使用两种翻译系统：

| 翻译类型 | 用途 | 工具 | 存储位置 |
|---------|------|------|---------|
| **UI翻译** | 界面元素（按钮、菜单、表单标签等） | Django i18n | `locale/zh_Hans/LC_MESSAGES/django.po` |
| **内容翻译** | 页面内容（文章、新闻、页面文本等） | Wagtail Localize | `translations/exports/` 或 Wagtail管理后台 |

### 支持的语言

- **中文（简体）**: `zh-hans` - 默认语言
- **英文**: `en`

## UI翻译流程

UI翻译用于翻译模板和Python代码中的固定文本。

### 第一步：提取可翻译字符串

运行以下命令扫描所有模板和Python代码，提取需要翻译的字符串：

```bash
make translate-ui
```

这个命令会：
- 扫描所有 `.html` 模板文件中的 `{% trans %}` 和 `{% blocktrans %}` 标签
- 扫描所有 `.py` 文件中的 `gettext()` 和 `_()` 函数调用
- 生成/更新 `locale/zh_Hans/LC_MESSAGES/django.po` 文件

### 第二步：编辑翻译文件

打开生成的PO文件进行翻译：

```bash
# 文件路径
locale/zh_Hans/LC_MESSAGES/django.po
```

**PO文件结构示例：**

```po
#: templates/components/language-switcher.html:31
msgid "Switch to"
msgstr "切换到"

#: synnovator/home/models.py:25
msgid "Homepage"
msgstr "主页"

#: templates/base.html:10
msgid "Welcome"
msgstr "欢迎"
```

**翻译说明：**
- `msgid`: 源语言文本（英文）- **不要修改**
- `msgstr`: 目标语言翻译（中文）- **填写翻译**
- 注释行（`#:`）显示该字符串在代码中的位置

**编辑工具选项：**

1. **文本编辑器**（适合少量翻译）:
   ```bash
   nano locale/zh_Hans/LC_MESSAGES/django.po
   # 或
   code locale/zh_Hans/LC_MESSAGES/django.po
   ```

2. **专业PO编辑器**（推荐）:
   - [Poedit](https://poedit.net/) - 跨平台GUI工具
   - 安装: `brew install poedit`
   - 使用: `poedit locale/zh_Hans/LC_MESSAGES/django.po`

3. **在线翻译平台**:
   - [Crowdin](https://crowdin.com/)
   - [Lokalise](https://lokalise.com/)
   - 导出PO文件 → 上传到平台 → 下载翻译结果

### 第三步：编译翻译文件

翻译完成后，将PO文件编译为MO二进制文件：

```bash
make compile-translations
```

这个命令会：
- 将 `.po` 文件编译为 `.mo` 文件
- MO文件是Django运行时实际使用的文件（速度更快）

### 第四步：发布翻译

重启开发服务器使翻译生效：

```bash
make start
```

或者如果服务器已在运行：

```bash
# 按 Ctrl+C 停止
# 重新运行
make start
```

### 验证UI翻译

1. 访问 `http://localhost:8000/zh-hans/`
2. 检查翻译后的文本是否正确显示
3. 使用语言切换器测试英文/中文切换

## 内容翻译流程

内容翻译用于翻译Wagtail页面和片段中的实际内容。

### 方法一：使用管理命令导出（批量翻译）

#### 第一步：导出内容

导出所有可翻译的Wagtail内容：

```bash
make translate-content
```

这个命令会：
- 导出所有页面和片段的可翻译字段
- 生成PO文件到 `translations/exports/zh-hans/latest/`
- 创建元数据文件 `export-metadata.json`

#### 第二步：查看导出的文件

```bash
# 列出导出的文件
ls -la translations/exports/zh-hans/latest/

# 查看元数据
cat translations/exports/zh-hans/latest/export-metadata.json
```

导出的PO文件示例：

```po
# HomePage (ID: 3)
msgid "Welcome to Synnovator"
msgstr "欢迎来到Synnovator"

msgid "Join our next hackathon"
msgstr "参加我们的下一场黑客松"
```

#### 第三步：翻译内容

编辑导出的PO文件，填写 `msgstr` 字段。

#### 第四步：导入翻译（待实现）

> **注意**: 导入功能需要通过Wagtail管理后台或API实现。目前导出功能主要用于：
> - 查看需要翻译的内容
> - 准备翻译文本
> - 集成到外部翻译工作流

### 方法二：使用Wagtail管理后台（推荐）

这是最直接的内容翻译方法：

#### 第一步：访问管理后台

```bash
# 确保服务器正在运行
make start

# 访问管理后台
http://localhost:8000/admin/
```

#### 第二步：切换到中文语言

1. 在页面编辑器中，找到语言选择器
2. 选择"简体中文 (zh-hans)"

#### 第三步：翻译页面内容

1. 进入需要翻译的页面
2. 点击"翻译"或"Translate"按钮
3. 在表单中填写中文翻译
4. 保存并发布

#### 第四步：验证内容翻译

1. 访问中文页面: `http://localhost:8000/zh-hans/page-url/`
2. 访问英文页面: `http://localhost:8000/en/page-url/`
3. 对比内容是否正确

## 翻译文件格式

### PO文件头部

每个PO文件开头包含元数据：

```po
msgid ""
msgstr ""
"Project-Id-Version: Synnovator 1.0\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2026-01-21 02:35+0000\n"
"PO-Revision-Date: 2026-01-21 10:00+0800\n"
"Last-Translator: Your Name <your.email@example.com>\n"
"Language-Team: Chinese <zh@li.org>\n"
"Language: zh-hans\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=1; plural=0;\n"
```

**重要字段：**
- `Language`: 必须设置为 `zh-hans`
- `Content-Type`: 必须是 `charset=UTF-8`
- `Plural-Forms`: 中文只有一种复数形式

### 特殊翻译格式

#### 带变量的翻译

```po
# Python代码中:
# message = _("Hello, %(name)s!")

msgid "Hello, %(name)s!"
msgstr "你好，%(name)s！"
```

**注意**: 保持变量名称 `%(name)s` 不变。

#### 复数形式

```po
msgid "%(count)d item"
msgid_plural "%(count)d items"
msgstr[0] "%(count)d 个项目"
```

中文没有复数变化，所以只需要一个翻译。

#### 多行翻译

```po
msgid ""
"This is a long text "
"that spans multiple lines."
msgstr ""
"这是一个很长的文本，"
"跨越多行。"
```

## 验证翻译

### 自动验证

#### 翻译质量检查脚本（推荐）

运行自动化翻译质量检查脚本：

```bash
bash scripts/check_translations.sh
```

这个脚本会自动检查：
- ✅ 模板中是否有未翻译的硬编码中文
- ✅ PO文件中是否有空的翻译条目
- ✅ MO编译文件是否存在
- ✅ 翻译文件是否需要重新编译
- ✅ msgid是否错误地使用了中文（应该用英文）
- ✅ Python文件中是否有未标记的中文字符串

**在提交代码前运行此脚本，确保翻译质量！**

示例输出：

```bash
🔍 Translation Quality Check
==============================

1. Checking for hardcoded Chinese in templates...
✓ No hardcoded Chinese found

2. Checking for untranslated strings in Chinese PO file...
⚠ Found 3 untranslated strings in locale/zh_Hans/LC_MESSAGES/django.po
  Please translate these before committing.

3. Checking for compiled translation files...
✓ Chinese MO file exists

4. Checking if translations need recompilation...
✓ Translation files are up to date

5. Checking for Chinese msgid (should use English)...
✓ All msgid are in English

6. Checking for hardcoded Chinese in Python files...
✓ No hardcoded Chinese in Python files

==============================
Summary
==============================
⚠ 0 error(s) and 1 warning(s) found

Consider fixing these before committing.
```

#### Django系统检查

运行Django检查命令：

```bash
uv run python manage.py check
```

### 手动验证清单

#### UI翻译验证

- [ ] 访问 `http://localhost:8000/zh-hans/` 查看中文界面
- [ ] 访问 `http://localhost:8000/en/` 查看英文界面
- [ ] 点击语言切换器，确认切换正常
- [ ] 检查按钮、菜单、表单标签是否翻译
- [ ] 检查错误消息是否翻译

#### 内容翻译验证

- [ ] 确认所有页面有中文版本
- [ ] 对比中英文内容是否一致
- [ ] 检查URL slug是否正确（中文页面可能有不同的slug）
- [ ] 验证图片和媒体文件在两种语言中都能正常显示

### 浏览器语言检测测试

1. **自动检测测试**:
   - 将浏览器语言设置为中文
   - 访问 `http://localhost:8000/`
   - 应该自动重定向到 `/zh-hans/` 或显示中文内容

2. **手动切换测试**:
   - 使用页面顶部的语言切换器
   - 确认切换后URL和内容都改变

## 常见问题

### Q1: 翻译没有显示？

**解决方案：**

```bash
# 1. 确认已编译翻译
make compile-translations

# 2. 检查MO文件是否存在
ls -la locale/zh_Hans/LC_MESSAGES/django.mo

# 3. 重启服务器
make start

# 4. 清除浏览器缓存
```

### Q2: 找不到某些字符串？

**原因**: 这些字符串可能没有标记为可翻译。

**解决方案**:

在模板中使用翻译标签：

```django
{% load i18n %}
<h1>{% trans "Welcome" %}</h1>
```

在Python代码中使用翻译函数：

```python
from django.utils.translation import gettext as _

message = _("Hello, world!")
```

然后重新运行：

```bash
make translate-ui
```

### Q3: PO文件和MO文件的区别？

| 文件类型 | 用途 | 可读性 | 版本控制 |
|---------|------|--------|---------|
| `.po` | 翻译源文件 | 人类可读的文本 | ✅ 应该提交 |
| `.mo` | 编译后的二进制 | 机器可读 | ❌ 不应提交（可重新生成） |

### Q4: locale目录使用 `zh_Hans` 还是 `zh-hans`？

Django自动处理这个转换：
- **设置中使用**: `zh-hans`（小写，连字符）
- **目录名称**: `zh_Hans`（下划线，首字母大写）

两者都是正确的，指向同一个语言。

### Q5: 如何更新现有翻译？

当代码中添加新的可翻译字符串后：

```bash
# 1. 提取新字符串（保留现有翻译）
make translate-ui

# 2. 编辑PO文件，只翻译新增的空msgstr

# 3. 编译
make compile-translations

# 4. 重启
make start
```

`makemessages` 命令会：
- 添加新字符串
- 保留已有翻译
- 标记过时字符串（不会删除）

### Q6: 如何批量翻译多个字符串？

**方法一：使用Poedit的翻译记忆功能**
- Poedit会记住之前的翻译
- 自动建议相似字符串的翻译

**方法二：使用翻译服务API**

创建脚本 `scripts/translate_po.py`（示例）：

```python
#!/usr/bin/env python
"""自动翻译PO文件助手"""
import polib

po = polib.pofile('locale/zh_Hans/LC_MESSAGES/django.po')

for entry in po:
    if not entry.msgstr:  # 只翻译空的条目
        # 调用翻译API（如Google Translate、DeepL等）
        entry.msgstr = translate_api(entry.msgid, target='zh')

po.save()
```

**方法三：使用专业翻译平台**
- Crowdin、Lokalise等支持批量翻译
- 提供翻译记忆、术语库等功能

### Q7: 生产环境部署注意事项

部署前确保：

```bash
# 1. 提取最新字符串
make translate-ui

# 2. 完成所有翻译

# 3. 编译翻译
make compile-translations

# 4. 收集静态文件
uv run python manage.py collectstatic --noinput

# 5. 提交.po文件到版本控制
git add locale/*/LC_MESSAGES/django.po
git commit -m "Update translations"

# 6. .mo文件不要提交（在服务器上编译）
```

在服务器上：

```bash
# 部署后编译翻译
make compile-translations

# 重启应用服务器
systemctl restart gunicorn  # 或其他应用服务器
```

## 最佳实践

### 翻译质量

1. **保持一致性**: 使用统一的术语表
2. **考虑语境**: 同一个英文单词在不同语境可能有不同翻译
3. **保持自然**: 不要直译，要符合中文表达习惯
4. **注意长度**: 某些UI元素可能有空间限制

### 术语表示例

| 英文 | 中文 | 说明 |
|-----|------|------|
| Hackathon | 黑客松 | 保持行业常用术语 |
| Team | 团队 | 不用"小组" |
| Quest | 任务 | 游戏化术语 |
| Submission | 提交 | 作品提交 |
| Verification | 验证 | 技术验证 |

### 版本控制

```bash
# .gitignore 中应该包含
*.mo          # 编译后的翻译文件
*.pot         # 翻译模板（可选）

# 应该提交的文件
locale/*/LC_MESSAGES/django.po
```

### 开发工作流（强烈推荐）

**每次添加UI组件后的标准流程**：

```bash
# 1. 开发阶段：使用英文作为msgid
# 在代码中使用 _("English text")
# 在模板中使用 {% trans "English text" %}

# 2. 完成UI开发后
make translate-ui              # 提取新字符串

# 3. 检查是否有新字符串
git diff locale/zh_Hans/LC_MESSAGES/django.po

# 4. 翻译中文
# 编辑 locale/zh_Hans/LC_MESSAGES/django.po
# 将空的 msgstr "" 填写为中文翻译

# 5. 编译翻译
make compile-translations

# 6. 测试
make start
# 访问 http://localhost:8000/zh-hans/ 和 /en/

# 7. 质量检查（提交前必须）
bash scripts/check_translations.sh

# 8. 提交
git add locale/zh_Hans/LC_MESSAGES/django.po
git add <你的代码文件>
git commit -m "Add new feature with translations"
```

**代码规范检查清单**：

- [ ] ✅ 所有用户可见文本都用 `_("English")` 或 `{% trans "English" %}` 包裹
- [ ] ✅ msgid 使用英文，不使用中文
- [ ] ✅ 模型字段使用 `verbose_name=_("English")`
- [ ] ✅ 表单字段使用 `label=_("English")`
- [ ] ✅ 运行 `make translate-ui` 提取新字符串
- [ ] ✅ 翻译所有空的 msgstr 为中文
- [ ] ✅ 运行 `make compile-translations` 编译
- [ ] ✅ 运行 `bash scripts/check_translations.sh` 验证质量
- [ ] ✅ 在两种语言下测试页面显示
- [ ] ✅ 确认没有中英文混用的情况

**Git钩子自动化（可选）**：

在 `.git/hooks/pre-commit` 添加：

```bash
#!/bin/bash
# 提交前自动检查翻译质量

echo "Running translation quality check..."
bash scripts/check_translations.sh

if [ $? -ne 0 ]; then
    echo "❌ Translation check failed. Please fix before committing."
    exit 1
fi
```

使脚本可执行：
```bash
chmod +x .git/hooks/pre-commit
```

### 持续集成

在CI/CD流程中添加翻译检查：

```yaml
# .github/workflows/ci.yml
- name: Check translations
  run: |
    make translate-ui
    git diff --exit-code locale/  # 确保没有未翻译的新字符串
```

## 更多资源

- [Django国际化文档](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [Wagtail Localize文档](https://github.com/wagtail/wagtail-localize)
- [PO文件格式规范](https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html)
- [Poedit官方文档](https://poedit.net/trac/wiki/Doc)

## 联系支持

如有翻译相关问题，请：
- 查阅本文档
- 检查Django和Wagtail官方文档
- 提交Issue到项目仓库

---

**更新日期**: 2026-01-21
**文档版本**: 1.0
