# Bloomberg 风格前端重构 - 文档总览

> 完整的设计规范、开发指南和参考资料，支持 AI 辅助开发（Claude Code）

---

## 📚 文档清单

### 1. 核心文档

#### [Bloomberg_Frontend_Redesign_v3.md](./Bloomberg_Frontend_Redesign_v3.md) ⭐⭐⭐⭐⭐
**最重要的文档** - 完整的技术实施指南

**包含内容**:
- ✅ 完整的技术栈说明
- ✅ 详细的文件结构
- ✅ TypeScript 类型定义
- ✅ API 契约和数据结构
- ✅ 完整的组件实现示例
- ✅ 状态管理方案
- ✅ 样式系统配置
- ✅ 开发检查清单

**适用场景**:
- Claude Code 进行开发时的主要参考
- 前端工程师实现功能时查阅
- Code Review 时的规范依据

---

#### [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) ⭐⭐⭐⭐
**快速参考卡片** - 开发时的速查手册

**包含内容**:
- ✅ 关键文件路径
- ✅ 设计规范速查（颜色、字体、间距）
- ✅ API 端点速查
- ✅ 核心数据结构速查
- ✅ 组件接口速查
- ✅ 常见问题快速修复
- ✅ Tailwind 类名速查

**适用场景**:
- 快速查找某个变量或类名
- 不确定 API 格式时查阅
- 忘记组件接口时参考

---

#### [PROGRESS_TRACKER.md](./PROGRESS_TRACKER.md) ⭐⭐⭐
**进度追踪清单** - 项目管理和进度跟踪

**包含内容**:
- ✅ 10 个开发阶段的详细任务
- ✅ 每个任务的完成状态
- ✅ 性能指标追踪
- ✅ 已知问题列表
- ✅ 每日站会记录
- ✅ 里程碑计划

**适用场景**:
- 团队每日站会时使用
- 跟踪开发进度
- 识别阻塞问题
- 项目复盘时参考

---

### 2. 设计规范文档

#### [bloomberg-design-specification.md](./bloomberg-design-specification.md) ⭐⭐⭐⭐⭐
**官方设计系统** - Bloomberg 风格的完整规范

**包含内容**:
- 20 章节的完整设计规范
- 色彩系统、排版、布局、组件规范
- 数据可视化标准
- 动画与交互模式
- 响应式设计指南
- 可访问性标准

**适用场景**:
- 设计师参考 Bloomberg 风格
- 前端实现视觉细节时查阅
- 保证整体设计一致性

---

#### [bloomberg-variables.css](./bloomberg-variables.css) ⭐⭐⭐⭐
**CSS 变量配置** - 即用型样式变量

**包含内容**:
- 完整的 CSS 变量定义
- 颜色、字体、间距、圆角等
- 预定义的工具类
- 动画关键帧
- 全局基础样式

**适用场景**:
- 直接导入项目使用
- 自定义主题时修改变量
- 保证样式统一性

---

#### [tailwind.config.js](./tailwind.config.js) ⭐⭐⭐⭐
**Tailwind 配置** - 定制的 Tailwind 主题

**包含内容**:
- Bloomberg 品牌色配置
- 自定义断点
- 扩展的工具类
- 自定义组件类（`.data-card`, `.btn` 等）
- 自定义插件

**适用场景**:
- 复制到项目的 tailwind.config 中
- 使用 Tailwind 快速开发

---

### 3. 参考素材

#### [README.md](./README.md) ⭐⭐⭐⭐
**使用指南** - 如何使用设计系统

**包含内容**:
- 快速开始教程
- 两种使用方案（CSS 变量 / Tailwind）
- 详细的代码示例
- 最佳实践建议
- 常见问题解答

---

## 🎯 使用流程建议

### 给 AI 开发工具（Claude Code）

1. **首次使用**: 
   ```
   请先阅读 Bloomberg_Frontend_Redesign_v3.md 的完整内容
   ```

2. **开始开发**:
   ```
   根据 PROGRESS_TRACKER.md 中的 Phase 5，
   实现 NewsPreviewModal 组件，
   参考 Bloomberg_Frontend_Redesign_v3.md 第 4.2.2 节的示例
   ```

3. **遇到问题时**:
   ```
   查看 QUICK_REFERENCE.md 第 8 节"常见问题快速修复"
   ```

4. **需要查找样式**:
   ```
   参考 QUICK_REFERENCE.md 的"设计规范速查"部分
   或查看 bloomberg-variables.css
   ```

### 给前端工程师

1. **项目启动**:
   - 阅读 `Bloomberg_Frontend_Redesign_v3.md` 第 0-1 节（快速开始 + 技术栈）
   - 按照第 2 节创建文件结构
   - 按照第 1.2 节安装依赖

2. **开始开发**:
   - 查看 `PROGRESS_TRACKER.md` 确定当前进度
   - 根据 `Bloomberg_Frontend_Redesign_v3.md` 第 4 节实现组件
   - 需要样式时查看 `QUICK_REFERENCE.md` 或 `bloomberg-variables.css`

3. **代码规范**:
   - 遵循 `Bloomberg_Frontend_Redesign_v3.md` 第 2.2 节的命名规范
   - 使用 `bloomberg-design-specification.md` 确保视觉一致性

4. **完成后**:
   - 在 `PROGRESS_TRACKER.md` 中标记完成
   - 提交代码并更新文档

### 给项目经理

1. **跟踪进度**:
   - 每天查看 `PROGRESS_TRACKER.md`
   - 关注"整体进度"和"每日站会记录"

2. **验收标准**:
   - 参考 `Bloomberg_Frontend_Redesign_v3.md` 第 7 节的检查清单
   - 确保每个阶段的验收标准都达成

3. **风险管理**:
   - 查看 `PROGRESS_TRACKER.md` 的"已知问题"部分
   - 跟踪阻塞事项

---

## 📖 文档优先级

### 必读文档 ⭐⭐⭐⭐⭐
- `Bloomberg_Frontend_Redesign_v3.md` - **最重要**
- `QUICK_REFERENCE.md` - 开发时必备

### 重要文档 ⭐⭐⭐⭐
- `PROGRESS_TRACKER.md` - 进度管理
- `bloomberg-design-specification.md` - 设计规范
- `bloomberg-variables.css` - 样式变量
- `tailwind.config.js` - Tailwind 配置

### 参考文档 ⭐⭐⭐
- `README.md` - 使用指南

---

## 🔄 文档更新规则

### 何时更新文档？

1. **完成任务后**:
   - 在 `PROGRESS_TRACKER.md` 中标记完成状态
   - 填写完成时间和负责人

2. **发现问题时**:
   - 在 `PROGRESS_TRACKER.md` 的"已知问题"中添加记录

3. **改变实现方式时**:
   - 更新 `Bloomberg_Frontend_Redesign_v3.md` 相关章节
   - 在文档末尾注明修改日期和原因

4. **添加新组件时**:
   - 在 `Bloomberg_Frontend_Redesign_v3.md` 第 4 节添加接口说明
   - 在 `QUICK_REFERENCE.md` 添加速查信息

5. **每日站会后**:
   - 更新 `PROGRESS_TRACKER.md` 的"每日站会记录"

### 文档版本管理

```bash
# 文档更新时添加 git commit
git add docs/
git commit -m "docs: 更新 [文档名] - [更新内容]"
```

---

## 🎨 设计资源

### Bloomberg 参考资料
- `reference/bloomberg_wti/screenshots/` - Bloomberg 页面截图
- `reference/bloomberg_wti/notes.md` - 截图说明

### 业务需求
- `docs/项目文档/AI_real_time_news_plan1021.md` - 完整业务计划

---

## 💡 开发技巧

### 与 Claude Code 协作

#### 良好的提示词示例 ✅

```
请根据 Bloomberg_Frontend_Redesign_v3.md 第 4.2.2 节的规范，
实现 NewsCard 组件。

要求：
1. 使用 TypeScript
2. 遵循文档中的接口定义
3. 使用 Tailwind 类名（参考 QUICK_REFERENCE.md）
4. 添加 ARIA 标签保证可访问性
```

```
我发现 SSE 连接频繁断开，
请参考 QUICK_REFERENCE.md 第 8 节"常见问题快速修复"
中的 SSE 连接断开解决方案来修复这个问题
```

#### 不好的提示词示例 ❌

```
帮我做个新闻卡片
```

```
K线图不好看，优化一下
```

### 代码审查清单

在提交代码前，确保：

- [ ] 遵循 `Bloomberg_Frontend_Redesign_v3.md` 的命名规范
- [ ] 使用了设计系统中定义的颜色和样式变量
- [ ] 组件接口与文档一致
- [ ] 添加了必要的 TypeScript 类型
- [ ] 通过了 ESLint 检查
- [ ] 添加了 ARIA 标签
- [ ] 在 `PROGRESS_TRACKER.md` 中标记完成

---

## 🐛 问题反馈

### 发现文档错误？

1. 在对应文档中添加注释
2. 提交 Issue 或直接修改
3. 通知团队成员

### 发现设计不合理？

1. 在 `PROGRESS_TRACKER.md` 的"已知问题"中记录
2. 与设计师和产品讨论
3. 达成一致后更新相关文档

---

## 📈 成功标准

### MVP 完成标准（Phase 1-5）

- ✅ 所有组件在 Storybook 中可视化
- ✅ 基础交互流程可运行
- ✅ 使用 Mock 数据正常展示

### Beta 完成标准（Phase 1-9）

- ✅ 连接真实 API
- ✅ 性能指标达标
- ✅ 无严重可访问性问题

### GA 完成标准（Phase 1-10）

- ✅ 所有测试通过
- ✅ 文档完整
- ✅ 生产环境稳定运行

---

## 📞 支持

如有任何问题，请：

1. 先查看 `QUICK_REFERENCE.md` 的常见问题部分
2. 查阅 `Bloomberg_Frontend_Redesign_v3.md` 相关章节
3. 在团队频道提问
4. 必要时更新文档帮助其他人

---

## 🎯 下一步

### 对于 AI 开发工具
```
1. 阅读 Bloomberg_Frontend_Redesign_v3.md
2. 查看 PROGRESS_TRACKER.md 确定当前任务
3. 开始编码
```

### 对于前端工程师
```
1. 克隆项目
2. 按照 Bloomberg_Frontend_Redesign_v3.md 第 0-1 节设置环境
3. 查看 PROGRESS_TRACKER.md 认领任务
4. 开发并更新进度
```

### 对于项目经理
```
1. 每日查看 PROGRESS_TRACKER.md
2. 组织站会讨论进度和问题
3. 确保团队遵循文档规范
```

---

**维护者**: 前端开发团队  
**最后更新**: 2025-10-26  
**文档版本**: 3.0.0

---

## 📑 文档变更日志

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2025-10-26 | 3.0.0 | 创建完整文档体系 | Team |
| 2025-10-26 | 3.0.0 | 添加 QUICK_REFERENCE.md | Team |
| 2025-10-26 | 3.0.0 | 添加 PROGRESS_TRACKER.md | Team |

---

**祝开发顺利！** 🚀
