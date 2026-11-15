# -*- coding: utf-8 -*-
"""题库扩充：Python 新增 39 题（简单15 / 中等16 / 困难8）。字段与主数据文件一致。"""

PYTHON_EXT = [
    # ================= 简单 15 =================
    ("Python 有哪些内置数据类型？分别举两个例子。",
     "数字：int、float、complex；文本：str；序列：list、tuple、range；二进制：bytes、bytearray；映射：dict；集合：set、frozenset；布尔：bool（int 子类）；None：NoneType。",
     "按类别答出至少六类且例子正确：4分\n每多答一类且正确：0.5分（最多1分）",
     "", "Python", "简单", "基础"),

    ("Python 里如何实现类似 switch-case 的分支？",
     "3.10+ 用 match-case 结构匹配（支持字面量、序列、映射、类模式解构）；旧版本用 dict 映射 {'a': func_a}.get(x, default) 或 if-elif 链。大量分发逻辑推荐 dict 映射表。",
     "答出 match-case 语法（3.10+）：2分\n答出 dict 映射分发：2分\n提到 if-elif 或 match 解构能力：1分",
     "", "Python", "简单", "基础"),

    ("break 和 continue 的区别是什么？",
     "break 立即终止整个循环；continue 跳过本次循环体剩余部分，进入下一次迭代。都只作用于最近一层循环，循环配 else 时 break 会跳过 else。",
     "答出 break 终止整个循环：2.5分\n答出 continue 跳过本次进入下次：2.5分",
     "", "Python", "简单", "基础"),

    ("for 循环的 else 子句什么时候执行？",
     "循环正常结束（迭代完或条件为假）而没有被 break 打断时执行 else；被 break 跳出则不执行。典型用途：搜索场景，else 里输出“未找到”。while...else 同理。",
     "答出未被 break 时执行：3分\n答出 break 时跳过 else：1.5分\n给出搜索类使用示例：0.5分",
     "", "Python", "简单", "基础"),

    ("dict.get、setdefault 和 collections.defaultdict 有什么区别？",
     "d.get(k, default) 只读不写入，键不存在返回默认值；d.setdefault(k, default) 读且不存在时写入默认值；defaultdict(factory) 在任何访问缺失键时自动调用工厂函数创建（如 defaultdict(list)、defaultdict(int)），适合聚合收集场景。",
     "答出 get 不写入返回默认：1.5分\n答出 setdefault 会写入：1.5分\n答出 defaultdict 自动工厂创建及适用场景：2分",
     "", "Python", "简单", "基础"),

    ("列表的 append、extend、insert 有什么区别？",
     "append(x) 尾部追加单个元素（列表会被当一个元素）；extend(iterable) 把可迭代对象逐个元素并入；insert(i, x) 在指定位置插入（O(n)，大量头部插入应用 deque）。append([1,2]) 得到 [..., [1,2]]，extend([1,2]) 得到 [..., 1, 2]。",
     "答出 append 追加单元素：1.5分\n答出 extend 逐个并入：1.5分\n答出 insert 按位置插入及 O(n) 或 append 嵌套示例：2分",
     "", "Python", "简单", "基础"),

    ("dict 的 keys()/values()/items() 返回的是什么？",
     "返回动态视图对象（不是列表）：反映字典的实时变化，支持迭代、len、in 判断，可转为 list()。视图不支持索引。Python 2 返回列表的行为已改变。",
     "答出是视图而非列表：2分\n答出随字典实时变化：2分\n答出可迭代/支持 in/可 list() 转换：1分",
     "", "Python", "简单", "基础"),

    ("Python 程序如何接收命令行参数？",
     "sys.argv 简单场景（argv[0] 是脚本名）；argparse 标准库支持位置参数、可选参数、类型校验、自动生成 -h 帮助；click/typer 第三方更简洁。脚本入口常用 if __name__ == '__main__': 组合。",
     "答出 sys.argv：1.5分\n答出 argparse 及其能力（类型/帮助/可选参数）：2.5分\n提到 click/typer 或入口组合：1分",
     "", "Python", "简单", "基础"),

    ("lambda 表达式是什么？有什么局限？",
     "lambda 参数: 表达式，创建匿名函数，只能写单个表达式、不能有语句（赋值/while/多行逻辑）、不能方便地加文档。适合作为 sorted(key=)、map/filter 的轻量回调；复杂逻辑应使用 def。",
     "答出匿名函数语法与返回表达式值：2分\n答出只能单表达式：2分\n给出 key= 等使用场景：1分",
     "", "Python", "简单", "基础"),

    ("map、filter、reduce 各做什么？",
     "map(f, it) 对每个元素应用 f；filter(pred, it) 保留使谓词为真的元素；reduce(f, it, init)（functools）把相邻元素累计折叠成一个值（如求和、拼串）。前两者返回惰性迭代器，多数场景可用列表推导替代更易读。",
     "map/filter/reduce 各答对含义：各1.5分（共4.5分）\n提到返回迭代器或列表推导替代：0.5分",
     "", "Python", "简单", "基础"),

    ("if __name__ == '__main__' 是什么作用？",
     "__name__ 是模块名：直接运行该文件时为 '__main__'，被 import 时为模块名。该判断保证初始化/入口代码只在直接执行时运行，被导入时不执行，是可复用模块的标准写法。",
     "答出直接运行与导入时 __name__ 的区别：3分\n答出保护入口代码不被 import 触发：2分",
     "", "Python", "简单", "基础"),

    ("Python 命名中的单下划线、双下划线前缀、双前后下划线分别是什么含义？",
     "_name：约定为内部实现，from m import * 不导入；__name：类内触发名称改写（_ClassName__name），用于避免子类覆盖；__name__：解释器保留的魔法属性/方法（如 __init__、__len__），不要自造。仅约定而非强制访问控制。",
     "答出 _ 内部约定：1.5分\n答出 __ 名称改写机制：2分\n答出 __x__ 为魔法方法保留：1.5分",
     "", "Python", "简单", "基础"),

    ("round(2.5) 和 round(3.5) 在 Python 3 里等于几？为什么？",
     "round(2.5)=2、round(3.5)=4。Python 3 的 round 采用银行家舍入（round half to even）：恰在 .5 时取最近的偶数。另有浮点表示误差（0.1+0.2 != 0.3）。需要常规四舍五入用 decimal.Decimal + quantize。",
     "答出两个结果 2 和 4：2.5分\n答出银行家舍入（取偶）：2分\n提到 decimal 方案或浮点误差：0.5分",
     "经典陷阱题，考察对浮点和标准库行为的细致程度。", "Python", "简单", "基础"),

    ("如何把一个 Unix 时间戳与可读时间互相转换？",
     "时间戳转 datetime：datetime.fromtimestamp(ts)；datetime 转时间戳：dt.timestamp()。格式化字符串：dt.strftime('%Y-%m-%d %H:%M:%S')，解析：datetime.strptime(s, fmt)。注意时区（naive vs aware，astimezone(timezone.utc)）。",
     "答出 fromtimestamp/timestamp 互转：2分\n答出 strftime/strptime：2分\n提到时区处理：1分",
     "", "Python", "简单", "基础"),

    ("json.dumps 和 json.loads 的常用参数有哪些？",
     "dumps：ensure_ascii=False 输出中文不转义、indent 缩进美化、default= 处理不可序列化对象（如 datetime 转 str）、sort_keys；loads：object_hook 定制解析。序列化 NaN 需 allow_nan。中文乱码问题九成是忘了 ensure_ascii=False。",
     "答出 loads/dumps 互逆关系：1.5分\n答出 ensure_ascii=False：2分\n答出 default= 或 object_hook：1.5分",
     "", "Python", "简单", "基础"),

    # ================= 中等 16 =================
    ("如何让自定义类的对象支持 for 循环遍历？",
     "实现迭代器协议：类定义 __iter__ 返回 self（或独立迭代器），__next__ 逐个返回元素并在耗尽时 raise StopIteration。for 循环会自动调用 iter() 与 next()。也可让 __iter__ 返回生成器函数的结果，最简洁。",
     "答出实现 __iter__ 与 __next__：3分\n答出 StopIteration 终止：1分\n答出 __iter__ 返回生成器简化写法：1分",
     "", "Python", "中等", "基础"),

    ("生成器的 send、throw、close 方法分别做什么？",
     "send(x)：恢复执行并把 x 作为当前 yield 表达式的值送入生成器（首次须 send(None)）；throw(exc)：在暂停处抛出异常，可被生成器内部 try 捕获；close()：在暂停处抛 GeneratorExit 结束生成器，清理逻辑放 finally。这是协程的底层机制（yield from 之前的双向通道）。",
     "send/send 含义各 1.5分（共3分）\n答出 close 触发 GeneratorExit：1分\n提到协程底层演进：1分",
     "", "Python", "中等", "基础"),

    ("多个装饰器叠放时，执行顺序是怎样的？",
     "@a @b def f 等价于 f = a(b(f))：靠近函数的先包装，执行时外层 a 先进入、内层 b 后进入（洋葱模型）。若装饰器带日志，会看到 a before → b before → f → b after → a after。",
     "答出等效嵌套 a(b(f))：2.5分\n答出执行时外层先进后出（洋葱）：2.5分",
     "", "Python", "中等", "基础"),

    ("property 装饰器怎么用？解决什么问题？",
     "@property 把方法变成属性访问，可配合 @x.setter/@x.deleter 定义读写删逻辑。作用：把简单属性升级为带校验/计算的属性而不改调用方代码（obj.x 语法不变）；只读属性只定义 getter。本质是描述符协议的便捷封装。",
     "答出 @property 语法：1.5分\n答出 setter 校验或计算属性场景：2分\n答出只读控制或本质为描述符：1.5分",
     "", "Python", "中等", "基础"),

    ("__slots__ 是做什么的？有什么代价？",
     "类定义 __slots__=('a','b') 后实例不再有 __dict__，属性直接存固定位置：内存占用显著降低、属性访问略快，适合百万级小对象。代价：不能再动态加未声明属性、多数情况下与普通继承混用会失效（子类无 slots 则又生成 __dict__）、与弱引用等特性需显式声明。",
     "答出省内存与固定属性位：2分\n答出不能动态加属性：1.5分\n答出继承限制或适用场景：1.5分",
     "", "Python", "中等", "基础"),

    ("Python 如何定义抽象基类（ABC）？",
     "继承 abc.ABC，用 @abstractmethod 标记必须实现的方法；子类未实现全部抽象方法则无法实例化。可配合 @abstractmethod @property。用途：定义接口契约、在框架中强制子类实现钩子。与 duck typing 互补（Protocol 是结构化替代）。",
     "答出 ABC + abstractmethod：3分\n答出未实现不能实例化：1分\n提到应用场景或 Protocol 对比：1分",
     "", "Python", "中等", "基础"),

    ("dataclass 装饰器有什么用？",
     "@dataclass 自动生成 __init__、__repr__、__eq__ 等，字段用类型注解声明（x: int = 0），支持 field(default_factory=list) 可变默认值、frozen=True 不可变、order=True 生成比较方法。大幅减少样板代码，是纯数据类的标准写法。",
     "答出自动生成 init/repr/eq：2分\n答出类型注解声明字段或 default_factory：2分\n答出 frozen/order：1分",
     "", "Python", "中等", "基础"),

    ("什么场景用枚举（Enum）？比常量好在哪里？",
     "enum.Enum 定义一组具名常量（class Color(Enum): RED=1）。优势：类型安全防拼错、可迭代、带 name/value、is 比较明确、自动 repr；IntEnum/StrEnum 可直接当值用。用于状态机、配置项、错误码等有限集合，替代散落的魔法数字/字符串。",
     "答出定义语法与用途：2分\n答出防魔法值/类型安全/可迭代任三点：2分\n提到 IntEnum 或 StrEnum：1分",
     "", "Python", "中等", "基础"),

    ("raise ... from ... 是做什么的？自定义异常怎么写？",
     "raise NewError('xx') from e 保留原始异常链（__cause__），traceback 显示 'The above exception was the direct cause'，便于排查；from None 显式切断。自定义异常：class MyError(Exception): def __init__(self, code, msg)...，继承合适层级（Exception/RuntimeError），可携带结构化信息供上层处理。",
     "答出 from 保留异常链：2分\n答出 from None 或排查价值：1分\n答出继承 Exception 并携带信息：2分",
     "", "Python", "中等", "基础"),

    ("__str__ 和 __repr__ 的区别？",
     "__str__ 面向用户（print、str()），要求可读；__repr__ 面向开发者（交互式回显、repr()、日志），理想格式是能重建对象的表达式（ClassName(args)）。只定义 __repr__ 时 str() 会退回用它。调试日志应优先保证 repr 有信息量。",
     "答出 str 给用户、repr 给开发者：2.5分\n答出 repr 应无歧义/可重建：1.5分\n答出 str 缺省回退 repr：1分",
     "", "Python", "中等", "基础"),

    ("collections 模块有哪些常用工具？",
     "Counter：计数器（most_common(n) 高频统计）；defaultdict：缺失键工厂；namedtuple：具名元组轻量记录；deque：双端队列（appendleft/popleft O(1)，滑窗、队列）；OrderedDict（3.7 前 dict 无序时的选择，现有 move_to_end）；ChainMap：多字典级联查找。",
     "Counter/defaultdict/namedtuple/deque 各 1 分（共4分）\n答出各自典型场景或 ChainMap：1分",
     "", "Python", "中等", "基础"),

    ("itertools 里最常用的函数有哪些？",
     "chain 拼接多个可迭代；groupby 按键分组（需先排序）；islice 切片迭代器；product/permutations/combinations 笛卡尔积/排列/组合；cycle 无限循环；accumulate 累计；batched（3.12+）分批。配合生成器处理流式与组合问题非常高效。",
     "chain/groupby/islice/product/combinations 每答对一个 1 分（最多5分）",
     "", "Python", "中等", "基础"),

    ("Python 项目如何管理依赖和虚拟环境？",
     "venv 创建隔离环境（python -m venv .venv）；pip freeze > requirements.txt 或 pip-tools 生成锁定依赖；现代工具 poetry/pyproject.toml 声明式管理、uv 极速安装。原则：项目独立环境、版本锁定可复现、生产用精确版本号。pipx 安装 CLI 工具。",
     "答出 venv 隔离与 requirements：2分\n答出 poetry/pyproject 或 uv：2分\n答出锁定版本可复现原则：1分",
     "", "Python", "中等", "基础"),

    ("logging 模块的基本用法？为什么不用 print？",
     "logging.basicConfig(level, format, filename) 快速配置；logger.debug/info/warning/error/critical 分级输出；Handler 控制目的地（控制台/文件/轮转 RotatingFileHandler），Formatter 定格式，可按模块配 logger。print 的问题：无级别、无时间戳、难重定向、无法按级别开关、多模块混乱。",
     "答出分级与 basicConfig：2分\n答出 Handler/Formatter 结构：2分\n答出 print 的缺陷：1分",
     "", "Python", "中等", "基础"),

    ("用 pytest 写单元测试的基本姿势？",
     "test_ 前缀函数 + assert 语句即可；@pytest.fixture 提供共享准备/清理（yield 后清理）；@pytest.mark.parametrize 参数化批量用例；monkeypatch fixture 打桩（setattr/env）；pytest.raises 断言异常；mock.patch 替换外部依赖。conftest.py 放公共 fixture。",
     "答出 test_ 函数+assert：1.5分\n答出 fixture：1.5分\n答出 parametrize/monkeypatch/mock 任两个：2分",
     "", "Python", "中等", "基础"),

    ("字符串驻留（interning）和小整数缓存是什么？",
     "CPython 把 [-5, 256] 的 int 与部分标识符样式的短字符串全局缓存复用，使 a is b 可能为 True；运行时也可 sys.intern() 显式驻留。这只是实现优化，不能作为身份判断依据，== 才是值比较。解释了为什么 256 is 257 结果不同的经典面试现象。",
     "答出小整数 [-5,256] 缓存：2分\n答出短字符串驻留：1.5分\n强调 is 与 == 应区分：1.5分",
     "", "Python", "中等", "基础"),

    ("如何在 Python 里做简单的并发下载？",
     "requests + ThreadPoolExecutor.map 线程池（IO 密集、简单）；asyncio + aiohttp/httpx.AsyncClient 协程 + Semaphore 限流（高并发首选，注意超时与重试）；批量任务 gather。要点：限并发（信号量）、超时、失败重试与失败收集、Session 复用。",
     "答出线程池或 asyncio+aiohttp 方案：2分\n答出限流/超时/重试要点：2分\n答出 Session 复用或失败收集：1分",
     "", "Python", "中等", "基础"),

    # ================= 困难 8 =================
    ("__getattr__ 和 __getattribute__ 的区别？各适合什么场景？",
     "__getattribute__ 拦截所有属性访问（性能敏感，重写需 super() 调用否则死递归）；__getattr__ 只在常规查找失败（属性不存在）时调用，适合动态代理、按需生成属性。代理类常用 __getattr__ 转发 + __dict__ 白名单；ORM/懒加载也基于它。",
     "答出 __getattribute__ 拦截一切且需 super()：2分\n答出 __getattr__ 仅未命中时触发：2分\n答出代理/懒加载场景：1分",
     "追加点：重写 __getattribute__ 里再 self.x 会无限递归，必须 object.__getattribute__(self, 'x')。", "Python", "困难", "应用"),

    ("多继承时方法解析顺序（MRO）如何确定？",
     "Python 3 用 C3 线性化：子类优先、保持各父类声明顺序、父类在其子类之后。类属性 __mro__ 或 mro() 可查看；super() 沿 MRO 找下一个而非“父类”，因此菱形继承中每个类只被调用一次（协作式多继承，super() 应贯穿全链）。",
     "答出 C3 线性化及查看方式：2分\n答出 super() 按 MRO 找下一个：2分\n答出菱形继承只调用一次：1分",
     "", "Python", "困难", "应用"),

    ("yield from 与生成器委托解决什么问题？它和 async/await 什么关系？",
     "yield from iter 把内层迭代器的产出与 send/throw 透明转发给外层，消除嵌套 for 与手动 try，重构生成器组合。PEP 380 之后协程基于它实现双向通信，asyncio 早期用 @coroutine+yield from，PEP 492 引入 async/await 成为原生协程语法，语义上 await≈yield from。",
     "答出委托与转发 yield/send：2分\n答出简化嵌套/组合价值：1.5分\n答出 async/await 演进关系：1.5分",
     "", "Python", "困难", "应用"),

    ("如何排查 Python 程序的内存持续增长（疑似泄漏）？",
     "先确认是否真泄漏：tracemalloc.start() 快照对比（snapshot.compare_to 按 lineno 统计增量）；gc.get_objects() 统计对象数量增长；objgraph.show_growth() 找增长最快类型。常见根因：全局缓存无上限、闭包/回调持有大对象、循环引用且 __del__ 阻碍回收、C 扩展泄漏。工具：memray/pytest 负载测试复现。",
     "答出 tracemalloc/objgraph 定位手段：2分\n答出常见根因三类以上：2分\n答出 gc 分析或 memray：1分",
     "线上问题排查型题目，重点看方法论：先量化再定位。", "Python", "困难", "应用"),

    ("描述一下：给一段 Python 热点代码提速，什么情况下选择 ctypes/Cython/Rust 扩展？",
     "先确认无法用算法/向量化（numpy）解决。ctypes 调已有 C 动态库：零依赖改造、但调用开销大且需手工处理内存；Cython：Python 语法加类型标注渐进编译，生态最顺、适合科学计算；PyO3/Rust：安全高性能、打包略繁琐，新项目流行。决策还要考虑构建链、团队栈与 GIL 释放（nogil/原子操作）。",
     "答出先穷尽算法与向量化：1.5分\nctypes/Cython/Rust 各自特点与适用各 1 分（共3分）\n答出构建成本或 GIL 释放考量：0.5分",
     "", "Python", "困难", "应用"),

    ("用 asyncio 实现一个生产者-消费者模型要注意什么？",
     "asyncio.Queue 天然协程安全：生产者 put（可 maxsize 背压）、消费者 get；多消费者 create_task 循环消费；优雅收尾用哨兵值或 queue.join()+task_done() 配合；超时与取消要处理 CancelledError，finally 释放资源；生产速率限制用 Semaphore。常见错误：忘记 await、在消费者里阻塞调用。",
     "答出 asyncio.Queue 与多消费者结构：2分\n答出 join/task_done 或哨兵收尾：1.5分\n答出背压/取消清理/限流任两点：1.5分",
     "", "Python", "困难", "应用"),

    ("Python 的 import 机制和循环导入问题怎么处理？",
     "import 触发 sys.meta_path finder 找模块→编译执行→缓存进 sys.modules。循环导入在模块顶层互相 import 时报部分初始化错误（属性不存在）。解法：把导入移入函数内延迟导入、抽出公共模块下沉依赖、只导入模块不导入属性、合并模块。包结构设计时应单向依赖；插件机制用 importlib 动态加载。",
     "答出 sys.modules 缓存与执行时机：2分\n答出循环导入成因（部分初始化）：1.5分\n答出延迟导入/下沉依赖等解法：1.5分",
     "", "Python", "困难", "应用"),

    ("写一个线程安全的计数器和带过期时间的缓存，思路是什么？",
     "计数器：itertools.count 不可跨值读取，应用 threading.Lock 下 count += 1 并读取；更细粒度可用原子性分析（CPython 单字节码的 GIL 原子性不可依赖）。带 TTL 缓存：dict + 过期时间戳，get 时惰性判断删除（单线程）；线程安全需在锁内操作或用 cachetools.TTLCache。要点：锁粒度、惰性清理 vs 后台清理、容量上限。",
     "答出 Lock 保护共享状态：2分\n答出 TTL 惰性过期或 cachetools：2分\n答出锁粒度/容量上限考量：1分",
     "", "Python", "困难", "应用"),
]
