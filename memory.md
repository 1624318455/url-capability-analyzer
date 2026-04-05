# 项目记忆库

## 教训 2026-04-03: Windows命令行编码问题需特殊处理
背景：在Windows环境中运行url-capability-analyzer分析脚本时，遇到UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f50d'，这是由于Windows命令行默认使用GBK编码，而脚本输出包含UTF-8编码的emoji字符。
教训/经验：在Windows上开发跨平台命令行工具时，必须考虑终端编码差异。解决方案包括：1) 提供输出到文件的选项（如-o/--output）；2) 在README中增加Windows特定使用说明；3) 考虑移除或替换emoji字符以兼容旧版终端。
原因：Windows命令行（cmd.exe/PowerShell）默认使用GBK编码页，而现代Python脚本通常输出UTF-8编码。当输出包含GBK无法表示的字符（如emoji）时会触发编码错误。
适用场景：任何可能输出特殊Unicode字符（特别是emoji）的跨平台命令行工具。

## 经验 2026-04-03: 跨平台Python命令适配
背景：在用户环境中，标准的python或python3命令不可用，而是需要使用py命令（Windows Python启动器）。
教训/经验：文档和使用说明中应包含所有可能的Python启动方式，特别是在Windows环境中。应提及python、python3和py三种常见命令。
原因：不同的Python安装方式和环境配置会导致可用的命令不同。Windows官方安装程序会注册py命令作为Python启动器。
适用场景：面向Windows用户的Python工具文档和使用说明.

## 方法论 2026-04-03: 问题隔离与逐步验证方法
背景：在排查url-capability-analyzer在Windows环境中的执行问题时，采用了逐步隔离问题的方法。
教训/经验：遇到复杂环境问题时，应按照以下步骤逐步排查：1) 验证基本Python环境；2) 检查依赖安装；3) 测试模块导入；4) 验证基本功能；5) 最后测试完整功能。每一步都应有明确的成功标志。
原因：这种方法可以快速定位问题所在，避免在复杂的失败情况下盲目猜测。
适用场景：任何环境依赖型的软件安装和使用问题排查.

## 决策 2026-04-03: 为跨平台工具提供多种输出方式
背景：在url-capability-analyzer中遇到的编码问题凸显了单一输出方式的局限性。
教训/经验：命令行工具应提供多种输出方式以适应不同环境：1) 标准控制台输出（理想情况）；2) 文件输出选项（规避终端限制）；3) 可选的简化输出模式（移除特殊字符）。
原因：不同终端环境、编码设置和使用场景对输出方式有不同要求。提供灵活性可以显著提高工具的可用性。
适用场景：任何可能遇到终端兼容性问题的命令行工具.

## 经验 2026-04-03: mcpworld.com目录网站的MCP工具提取策略
背景：mcpworld.com是一个MCP目录网站，但它的结构与官方MCP文档不同。页面加载动态内容，/servers/fetch链接指向"tree"（树形导航），而不是当前MCP。
教训/经验：
1. 对于目录网站，MCP名称应从URL路径直接提取（如/servers/fetch）
2. mcpworld.com是SPA（单页应用），需要Playwright等浏览器工具渲染
3. 页面HTML中可能不包含当前MCP的路径链接，而是显示相关MCP列表
4. 描述中的中文内容（网页抓取、HTML转换等）可以作为标签，但不易直接提取为工具名
原因：目录网站为了导航体验，会在页面中展示多个相关MCP，其内部链接指向树形导航组件。
适用场景：分析任何MCP/Skill目录网站时的工具提取

## 问题 2026-04-05: Windows PowerShell输出捕获异常
背景：在Windows PowerShell环境中运行Python脚本时，print语句的输出不在工具结果中显示，导致无法直接观察脚本执行状态。
现象：
1. Python能正常执行（文件创建成功）
2. print输出不显示在工具返回中
3. subprocess调用也遇到同样问题
4. 直接文件写入（write工具）正常工作
教训/经验：
1. 对于Windows环境，优先使用文件写入而非控制台输出
2. 依赖外部工具（webfetch）作为备选方案获取网页内容
3. 脚本执行与输出捕获是不同层面的问题
4. 必要时采用手动分步执行策略：导入模块→获取数据→处理→保存
适用场景：Windows环境下的命令行工具开发和调试

## 方法论 2026-04-05: 降级分析法处理复杂环境故障
背景：当自动化工具链失效时（如脚本执行无输出），需要采用降级策略继续完成目标。
步骤：
1. 降级获取：使用webfetch工具直接获取目标页面内容
2. 降级处理：手动执行分析流程的各个组件
3. 降级输出：使用write工具直接生成报告文件
教训/经验：
1. 不要在单一路径上反复尝试，应快速切换备选方案
2. 模块化设计使组件可以独立调用
3. 核心目标是完成分析，过程优化可以后续进行
适用场景：复杂环境下的工具链故障排查和任务完成

## 经验 2026-04-05: 本地能力扫描的路径依赖性
背景：LocalScanner扫描时依赖config/agent_paths.json中定义的路径，但这些路径可能不存在或为空。
发现：
1. opencode的skills路径：~/.config/opencode/skills 存在且有内容
2. MCP服务器路径：~/.config/opencode/mcp_servers 可能不存在
3. 其他AI代理的路径可能完全不存在
教训/经验：
1. scanner设计考虑了路径不存在的情况（返回空列表）
2. 扫描结果取决于用户实际安装的技能/MCP
3. 不同用户的扫描结果会不同（配置相关）
适用场景：需要扫描用户环境的工具设计

## 优化 2026-04-05: 脚本执行与输出优化
已完成：
1. 添加 --no-emoji 参数解决Windows终端emoji兼容问题
2. 默认输出到文件功能，避免终端编码问题
3. 添加 --output 参数支持自定义输出文件
4. 添加 -b/--browser 参数支持动态页面（Playwright）
待优化：
1. 添加日志文件选项用于调试
2. 添加 --verbose 参数用于详细输出
3. 考虑添加配置文件支持
4. 添加单元测试覆盖主要功能

## 升级 2026-04-05: CLI工具升级为MCP服务器
背景：将url-capability-analyzer从命令行工具升级为MCP服务器，实现与OpenCode的无缝集成。
改动：
1. 新增 server.py：MCP服务器入口，实现JSON-RPC协议
2. 新增 package.json：支持npm/npx方式安装
3. 更新 README.md：添加MCP安装和使用说明
MCP工具定义：
- analyze_capability(url, use_browser, include_embedding)：分析URL与本地能力重叠
- list_local_capabilities(agent, type)：列出本地已安装的Skills和MCPs
- compare_urls(urls)：比较多个URL之间的相似度
使用方式变化：
- CLI模式：python scripts/analyze.py <url>
- MCP模式：自然语言如"帮我分析这个MCP有没有重复：<url>"
经验：
- MCP服务器使工具可以通过自然语言调用
- 输出从文件变为对话中的JSON响应
- 无需手动执行命令，AI Agent可直接使用