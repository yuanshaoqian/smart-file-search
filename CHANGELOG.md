# Changelog

本文件记录 Smart File Search 的版本更新历史。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- 待发布的新功能

### Changed
- 待发布的变更

### Fixed
- 待发布的修复

---

## [1.0.5] - 2026-02-26

### Fixed
- 修复索引时闪退的问题
  - 将批次提交大小从 50 降低到 10，减少内存占用
  - 增加文件处理超时时间从 30s 到 60s
  - 添加详细的闪退日志记录，包括：
    - 每个文件索引前后的状态
    - 批次提交的详细过程（写入、commit、创建新writer）
    - 完整的错误堆栈信息
  - 改进异常处理，确保程序不会静默崩溃

---

## [1.0.4] - 2026-02-26

### Fixed
- 修复打包后程序启动失败的问题（`TypeError: Cannot log to objects of type 'NoneType'`）
  - 在打包环境中 `sys.stderr` 可能为 `None`，添加了空值检查
  - 添加日志配置的异常处理，确保程序能正常启动
- 简化 macOS 构建配置，使用 `macos-latest` runner

---

## [1.0.3] - 2026-02-26

### Fixed
- 修复 macOS 构建配置问题
- 现在同时提供 Intel 和 Apple Silicon 两个版本的 macOS 构建
  - `SmartFileSearch-macOS-Intel-*`: 适用于 Intel Mac
  - `SmartFileSearch-macOS-AppleSilicon-*`: 适用于 M1/M2/M3 Mac

---

## [1.0.2] - 2026-02-26

### Fixed
- 修复模糊搜索无法匹配中间字符的问题，现在支持真正的模糊搜索
  - 添加中间通配符匹配 `*query*`，可匹配任意位置的关键词
  - 添加前缀匹配和精确匹配
  - 增强分词后的模糊匹配逻辑

### Added
- 添加完善的日志记录系统
  - 程序启动/关闭日志
  - 搜索操作日志（开始、完成、错误）
  - 索引操作日志（已存在，增强）
  - 日志文件保存在 `logs/` 目录，按日期命名
  - 日志保留 7 天，单个文件最大 10MB

---

## [1.0.1] - 2026-02-26

### Fixed
- 修复 macOS 版本在 Intel Mac 上无法运行的问题（"bad CPU type in executable"）
- 使用 Intel runner 构建以兼容所有 Mac 设备

---

## [1.0.0] - 2025-02-26

### Added
- 快速文件索引功能（基于 Whoosh）
- AI 自然语言搜索支持（基于 Llama.cpp）
- 启动画面显示加载进度
- 多线程处理，界面流畅
- 支持 Word/Excel/TXT 文件解析
- PyQt6 现代化界面
- 深色/浅色主题切换
- 文件类型、大小、日期过滤器
- 搜索历史记录
- 配置文件编辑器

### Changed
- 优化索引性能
- 改进 AI 响应速度
- 增强错误处理

### Fixed
- 修复索引目录验证问题
- 修复批量提交导致的崩溃
- 修复 AI 设置验证问题
- 修复搜索响应性问题
- 修复 GPU 支持检测
- 修复 UI 可见性问题

---

## 版本说明

- **Added**: 新增功能
- **Changed**: 现有功能的变更
- **Deprecated**: 即将废弃的功能
- **Removed**: 已移除的功能
- **Fixed**: 问题修复
- **Security**: 安全相关的修复

[Unreleased]: https://github.com/yuanshaoqian/smart-file-search/compare/v1.0.5...HEAD
[1.0.5]: https://github.com/yuanshaoqian/smart-file-search/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/yuanshaoqian/smart-file-search/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/yuanshaoqian/smart-file-search/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/yuanshaoqian/smart-file-search/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/yuanshaoqian/smart-file-search/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/yuanshaoqian/smart-file-search/releases/tag/v1.0.0
