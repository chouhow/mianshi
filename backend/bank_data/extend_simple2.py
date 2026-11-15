# -*- coding: utf-8 -*-
"""按新难度标尺补充的入门简单题（10 道）：有相关经验、不刻意准备也有印象的常识题。"""

SIMPLE_MORE2 = [
    # Python 4
    ("什么是 PEP 8？举几个常见的代码规范。",
     "PEP 8 是 Python 官方代码风格指南。常见规范：缩进 4 空格；函数/变量用 snake_case 超市命名、类用 PascalCase、常量全大写；一行不超过 79/120 字符；导入放文件顶部且一行一个；运算符两侧空格；用 is None 判空。团队常用 black/autopep8 自动格式化。",
     "答出是官方风格指南：1.5分\n答出至少三条具体规范：2.5分\n提到自动格式化工具：1分",
     "工程素养题，答出“官方风格指南+任意三条”即合格。", "Python", "简单", "基础"),

    ("如何安装和管理 Python 第三方库？",
     "pip install 包名 安装（pip install -r requirements.txt 批量、pip install 包==版本 指定版本）；pip list 查看已装；pip uninstall 卸载；pip freeze 导出锁定。国内可配镜像源（-i 清华源）。现代替代：uv/poetry。虚拟环境里装，避免污染全局。",
     "答出 pip install/uninstall/list：2.5分\n答出 requirements 或版本指定：1.5分\n答出镜像源或虚拟环境习惯：1分",
     "", "Python", "简单", "基础"),

    ("Python 字符串有哪些常用方法？",
     "split(sep) 分割成列表、join(iterable) 拼接、strip() 去首尾空白（lstrip/rstrip）、replace(a,b) 替换、upper/lower 大小写、startswith/endswith 前后缀判断、find/index 查找（find 找不到返回 -1，index 抛异常）、format/f-string 格式化。注意字符串不可变，这些方法都返回新串。",
     "每答对两个常用方法各 0.5 分（最多 4 分）\n答出字符串不可变返回新串：1分",
     "可以现场追问 split/join 配合解析日志的用法。", "Python", "简单", "基础"),

    ("Python 中如何查看对象的类型和可用属性方法？",
     "type(obj) 看类型；isinstance(obj, cls) 判断类型（含子类）；dir(obj) 列出全部属性和方法名；help(obj) 或 obj.__doc__ 查看文档；vars(obj)/obj.__dict__ 查看实例属性；hasattr/getattr/setattr 动态操作属性。调试和探索陌生对象的日常工具。",
     "答出 type/dir/help 三件套：3分\n答出 isinstance 或 hasattr/getattr：1分\n答出 __dict__/vars：1分",
     "", "Python", "简单", "基础"),

    # 数据库 3
    ("一个基本的 CREATE TABLE 语句包含哪些部分？",
     "表名、列定义（列名 + 数据类型 + 约束）、表级约束。示例：CREATE TABLE users (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50) NOT NULL, age INT DEFAULT 0, email VARCHAR(100) UNIQUE, created_at DATETIME)；常用约束：PRIMARY KEY、NOT NULL、UNIQUE、DEFAULT、FOREIGN KEY。",
     "答出表名列名类型结构：2分\n答出至少三种约束：2分\n给出合理示例：1分",
     "", "数据库", "简单", "基础"),

    ("什么是数据库事务？举个必须用事务的例子。",
     "事务是一组要么全部成功、要么全部回滚的 SQL 操作单元。经典例子：转账——A 账户扣 100 元与 B 账户加 100 元必须同时成功；若扣款后加款前系统故障，事务回滚，避免钱凭空消失。MySQL 中 START TRANSACTION ... COMMIT/ROLLBACK 控制。",
     "答出全部成功或全部回滚：2.5分\n给出转账等正确示例：2分\n答出 COMMIT/ROLLBACK：0.5分",
     "", "数据库", "简单", "基础"),

    ("为什么用数据库而不是直接用文件/Excel 存数据？",
     "数据库提供：并发控制（多用户同时读写不冲突）；事务保证一致性；索引高效检索（百万行毫秒级）；权限与安全控制；备份恢复机制；约束保证数据合法性。文件存少量配置可以，业务数据一旦涉及并发查询和可靠性就要数据库。",
     "答出并发/事务/索引三点核心：3分\n答出权限或备份安全：1分\n答出适用边界（少量配置可用文件）：1分",
     "", "数据库", "简单", "基础"),

    # 智能体 3
    ("什么是开源大模型？举几个例子。",
     "权重公开可下载、可自行部署和微调的模型，区别于只提供 API 的闭源模型（GPT-4o/Claude）。常见开源系：Meta Llama、阿里 Qwen（通义千问）、DeepSeek、智谱 GLM、Mistral 等，HuggingFace/Ollama 可下载。优势：数据私有、可定制、无调用费；代价：需要 GPU 与运维。",
     "答出权重公开可自行部署：2分\n答出至少两个例子（Llama/Qwen/DeepSeek/GLM 等）：2分\n答出与闭源 API 的区别：1分",
     "", "智能体", "简单", "基础"),

    ("大模型能做哪些常见任务？举几个实际例子。",
     "文本生成与改写（文案、邮件）、翻译、摘要（长文转要点）、问答与知识查询、代码生成与解释（Copilot 类）、分类与信息抽取（情感、实体）、对话陪聊、头脑风暴。配合工具还能做搜索问答（Perplexity）、图片理解。本质是把“语言任务”统一为生成。",
     "每举对两类任务各 1 分（最多 4 分）\n答出代码助手/搜索问答等具体产品：1分",
     "考察对大模型应用面的常识了解。", "智能体", "简单", "基础"),

    ("模型的“参数量”是什么意思？7B、70B 指什么？",
     "参数量是模型内部可学习权重（矩阵数值）的总数，B=十亿（Billion）。7B ≈ 70 亿参数，70B ≈ 700 亿。参数量越大通常能力越强，但显存与算力需求也越大（FP16 下显存≈参数量×2 字节，7B 约 14GB）。7B~14B 适合单卡部署，70B+ 需多卡/量化。",
     "答出参数是模型可学习权重总数：2分\n答出 B=十亿、7B 含义：1.5分\n答出参数量与显存/能力的权衡：1.5分",
     "数字换算能答出来说明真的理解部署成本。", "智能体", "简单", "基础"),
]
