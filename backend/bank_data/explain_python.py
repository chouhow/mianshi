# -*- coding: utf-8 -*-
"""题目讲解（完整版）：Python 方向 88 题，Markdown 富文本。

键 = 完整题干（精确匹配），值 = 讲解内容。build.py 以最高优先级使用本文件。
模板：考察要点 / 追问路线 / 常见误区与加分项，可按题目灵活取舍。
"""

PYTHON_EXPLAIN = {

    "Python 中列表（list）和元组（tuple）有什么区别？": """
**核心差异是可变性**：列表可增删改，元组定义后不可变。

### 考察要点
- 能否说清「不可变」的含义：不能重新绑定/修改元素，而非"只读对象"
- 由不可变推导出**元组可哈希**（前提：元素也可哈希），能作 dict 键、入集合；列表不行
- 内存与性能：元组更小、创建更快（C 层复用小元组缓存）

### 追问路线
1. 元组里装了列表，还能当字典键吗？（不能，元素不可哈希则整体不可哈希）
2. 单元素元组怎么写？（`(1,)`，漏逗号就是普通括号表达式）
3. 什么场景必须用元组：多返回值、数据库行、namedtuple 固定结构

> 常见误区：把元组说成"只读列表"。要点在语义——固定结构的数据载体，而非性能优化。
""",

    "Python 中 is 和 == 有什么区别？": """
`==` 调用 `__eq__` 比较**值**；`is` 比较两个名字是否指向**同一个对象**（内存身份）。

### 考察要点
- 能否举例说明二者结果不同的场景：`a = [1]; b = [1]` 则 `a == b` 为 True、`a is b` 为 False
- 知道 `is` 的成本低于 `==`（不调用用户代码）

### 追问路线
1. 为什么判断 None 必须用 `is None`？（None 是单例；`==` 可能被 `__eq__` 重载出意外结果）
2. 小整数缓存与字符串驻留：`a = 256; b = 256` 时 `a is b` 为 True，`257` 时通常为 False——但这是 CPython 实现细节，不应依赖

> 加分项：能说"is 用于单例判断（None/True/哨兵对象），== 用于值比较"，边界清晰。
""",

    "浅拷贝和深拷贝的区别是什么？": """
三个层次：**赋值**（共享对象）、**浅拷贝**（复制外壳，子元素仍共享）、**深拷贝**（递归复制全部层级）。

### 考察要点
- 浅拷贝的多种写法：`copy.copy`、`list(x)`、`x[:]`、`dict(x)`
- 能举出浅拷贝的坑：嵌套列表 `b = a[:]` 后 `b[0].append(...)` 会影响 `a`

### 追问路线
1. `copy.deepcopy` 如何处理循环引用？（备忘录 dict 记录已复制对象，`id` 映射）
2. 深拷贝自定义类如何控制行为？（实现 `__deepcopy__` 或 `__reduce__`）
3. 为什么可变默认参数等价于共享同一个对象

> 常见误区：认为"切片总是安全的复制"。一维列表够用，嵌套结构立刻翻车。
""",

    "Python 有哪些可变类型和不可变类型？函数传参是传值还是传引用？": """
不可变：`int/float/str/tuple/frozenset/bytes`；可变：`list/dict/set/bytearray` 及多数自定义对象。

传参是**传对象引用（pass by object reference）**：
- 重新赋值（`x = ...`）只改局部名字绑定，不影响外部
- 原地修改（`x.append(...)`）外部可见

### 考察要点
- 能用代码说明两种情况的差异，而不是背"传值/传引用"二选一
- 理解不可变对象的"修改"其实是创建新对象并重新绑定

### 追问路线
1. `a += [1]` 与 `a = a + [1]` 对可变对象有何不同？（前者原地 `__iadd__`，后者新对象）
2. 为什么 str 拼接循环里用 `+=` 性能差？（每次创建新字符串）

> 加分项：提到 tuple 内容不可变 ≠ 元素自身不可变（元组里装列表，列表仍可改）。
""",

    "*args 和 **kwargs 是什么？": """
`*args` 把多余**位置参数**收为元组；`**kwargs` 把多余**关键字参数**收为字典。

### 考察要点
- 双向用法：定义时收集、调用时解包——`f(*lst, **cfg)`
- 参数顺序铁律：普通参数 → `*args` → 仅关键字参数 → `**kwargs`

### 追问路线
1. 写一个"参数透传"装饰器，为什么必须 `wrapper(*args, **kwargs)`？
2. `def f(a, *, b)` 中单独的 `*` 是什么？（其后参数只能按关键字传）
3. kwargs 的键一定是字符串，为什么？

> 常见误区：以为 `*args` 里是列表。它是元组；kwargs 是普通 dict（Python 3.7+ 保序）。
""",

    "sorted() 和 list.sort() 有什么区别？": """
`list.sort()` **原地**排序、返回 `None`；`sorted()` 返回**新列表**，且接受任意可迭代对象（元组、dict、生成器均可）。

### 考察要点
- 经典陷阱：`a = a.sort()` 会把 a 变成 `None`——候选人是否主动提及
- `key` 与 `reverse` 参数；`key=lambda x: (x.age, -x.score)` 多级排序

### 追问路线
1. 怎么按字典的值排序？`sorted(d.items(), key=lambda kv: kv[1])`
2. 怎么让自定义类支持排序？（实现 `__lt__` 或传 key / `functools.cmp_to_key`）
3. 排序稳定性是什么？Python 的 Timsort 是稳定排序，同 key 保持原序

> 加分项：知道 `heapq.nlargest` 在"只要前 K 名"时比全量排序省。
""",

    "字典（dict）和集合（set）有什么区别？分别什么场景使用？": """
底层同为**哈希表**，元素都要求可哈希，查找均摊 O(1)。dict 是 key→value 映射；set 只存不重复的 key。

### 考察要点
- dict 场景：按 key 取值、计数、缓存、配置
- set 场景：去重、成员判断 O(1)、交并差运算

### 追问路线
1. `d[k]`、`d.get(k)`、`k in d` 的区别（异常 / 默认值 / 布尔）
2. Python 3.7+ dict 保持插入顺序，底层怎么做到？（紧凑数组存 entries，哈希表存索引）
3. set 的 `| & - ^` 对应哪些方法名？（union/intersection/difference/symmetric_difference）

> 常见误区：以为 dict/set "查询一定快"——哈希冲突与扩容时有代价；且大量数据下并非排序结构。
""",

    "如何去除列表中的重复元素？如何保持原顺序？": """
三种层次：
- `list(set(lst))`：最快，但**无序**
- `list(dict.fromkeys(lst))`：保序（3.7+ dict 有序）
- 手写循环 + seen 集合：元素不可哈希时用 `id` 或元组化处理

### 考察要点
- 是否知道 set 方式会打乱顺序，并给出保序方案
- 去重对象是 dict 等不可哈希元素时怎么办

### 追问路线
1. `dict.fromkeys` 与循环写法的时间复杂度？（都是 O(n)）
2. 按对象某字段去重怎么做？（循环 + seen 记录该字段的元组）
3. `[{} for _ in range(3)]` 与 `[{}] * 3` 去重时的坑

> 加分项：主动确认"元素是否可哈希、是否需要保序"再选方案，说明有工程意识。
""",

    "Python 格式化字符串有哪几种方式？": """
三种主流方式：
- `%` 格式化：`"name=%s" % name`（老代码、日志常见）
- `str.format()`：`"{0}-{1}".format(a, b)`
- **f-string**（3.6+，首选）：`f"{user=} {score:.2f}"`

### 考察要点
- f-string 的高效用法：表达式内直接运算、`=` 调试语法、格式说明符 `:>10`、`:.1%`
- 各方式性能：f-string 编译期优化，通常最快

### 追问路线
1. f-string 里怎么嵌套引号、怎么换行？（外双内单；3.12+ 才允许同引号嵌套）
2. 模板与用户输入拼接有什么风险？（SQL 注入 / 提示词注入）
3. `format(value, spec)` 与 `__format__` 协议

> 常见误区：仍全程使用 `%` 或 `+` 拼接且不知 f-string 的调试语法。
""",

    "什么是切片？步长为负是什么效果？": """
切片 `s[start:stop:step]` 按 [start, stop) 取子序列，**产生新对象**（浅拷贝）。

### 考察要点
- 负步长=反向：`s[::-1]` 反转序列；`s[5:1:-2]` 从 5 往前隔 2 取
- 越界不报错：`s[:100]` 安全截断；start/stop 为负时从尾部数

### 追问路线
1. `s[::-1] == reversed(s)` 吗？（前者返回新序列，后者返回迭代器）
2. 切片赋值：`a[1:3] = [10, 20, 30]` 长度可变
3. 切片对象 `slice(1, None, 2)` 用在哪？（numpy/pandas 维度索引）

> 加分项：知道 `s[:]` 是清浅拷贝惯用法，以及 mutable 切片赋值会原地改变长度。
""",

    "Python 异常处理中 try/except/else/finally 的执行顺序是怎样的？": """
顺序：try 无异常 → **else** 执行 → finally；try 有异常 → 匹配的 except 执行 → finally。finally **无论如何都执行**（进程被杀除外）。

### 考察要点
- else 的价值：把"可能不异常"的后续逻辑与 try 隔离，避免误捕获自己引发的异常
- except 捕获顺序：子类异常须写在父类之前，否则被吞

### 追问路线
1. finally 里的 return 会怎样？（会**吞掉**异常与 try 里的返回值——反模式，能指出者加分）
2. `except Exception as e` 与裸 `except:` 的区别（裸 except 连 KeyboardInterrupt 都吞）
3. 异常链：`raise NewErr(...) from e` 保留原始堆栈

> 常见误区：用异常做常规流程控制；except 里只写 pass 不留日志。
""",

    "为什么读写文件推荐用 with open？": """
`with` 是上下文管理器语法：无论正常结束还是**中途抛异常**，都会调用 `__exit__` 保证 `close()`，避免句柄泄漏与数据未刷盘。

### 考察要点
- 能说出不用 with 的风险：异常路径漏 close、缓冲数据没 flush
- 编码意识：`open(p, encoding='utf-8')` 显式声明，避免 Windows 默认 GBK 乱码

### 追问路线
1. 同时读写两个文件怎么写？（`with open(a) as fa, open(b) as fb:`）
2. `__enter__/__exit__` 与 `contextlib.contextmanager` 两种实现
3. 大文件为什么逐行迭代而不是 `read()` 全量？（内存）

> 加分项：知道 close 语义里包含 flush，以及 try-finally 写法是 with 的手动等价物。
""",

    "集合（set）支持哪些运算？举个例子。": """
运算符与方法两套：
- 并 `a | b` / `union`；交 `a & b` / `intersection`
- 差 `a - b` / `difference`；对称差 `a ^ b` / `symmetric_difference`
- 子集/超集：`a <= b`、`issubset`、`issuperset`

### 考察要点
- 能现场写出至少 3 种运算并说清语义
- 知道这些运算是 O(len) 级别的哈希操作，适合替代嵌套循环判重

### 追问路线
1. 两个列表找共同元素：`set(a) & set(b)` 与双循环的复杂度对比
2. `|=` 与 `|` 的区别（原地更新 vs 新集合）
3. frozenset 何时用？（要作为另一个 set 的元素或 dict 键时）

> 常见误区：用 `+` 连接集合（不支持）；以为集合运算会保序（无序结构）。
""",

    "如何判断一个对象是可迭代的？迭代器和可迭代对象有什么区别？": """
两协议：
- **Iterable**：实现 `__iter__`（或老式 `__getitem__`），能被 for 遍历
- **Iterator**：实现 `__next__` 和 `__iter__`，是"取数游标"

判断：`isinstance(x, collections.abc.Iterable)` 或 `iter(x)` 试错。for 循环的本质是先 `iter()` 再不断 `next()` 直到 StopIteration。

### 考察要点
- 迭代器是一次性的：耗尽后不再产出元素
- `iter(x) is x` 可判断 x 是否已是迭代器

### 追问路线
1. 生成器是迭代器吗？（是，且只能被遍历一次）
2. list 可迭代但不是迭代器——为什么这样设计？（可重复遍历）
3. `zip/map/enumerate` 返回什么？（迭代器，惰性）

> 加分项：能写一个自定义迭代器类，实现 `__iter__` 返回 self + `__next__`。
""",

    "判断 x 是否为 None 为什么推荐用 is None 而不是 == None？": """
三个理由：
1. None 是**单例**，`is` 直接比身份，O(1) 且语义精确
2. `==` 会调用 `x.__eq__`，可能被重载出意外结果（如 NumPy 数组返回数组而非布尔，直接炸 if）
3. PEP 8 明确规定：与 None 比较必须用 is / is not

### 考察要点
- 能举出 `== None` 出错的实例（pandas/numpy 的向量化比较）
- 同理适用于 True/False 与哨兵对象判断

### 追问路线
1. `x == None` 什么时候"碰巧"也 True？（默认 `__eq__` 就是 is 比较）
2. 自定义类怎样让 `== None` 返回 False 永远成立/不成立？（重载 `__eq__`）

> 常见误区：认为两者等价永远可用——库代码里被重载的 `__eq__` 是真实生产事故来源。
""",

    "Python 3 的 range(10) 返回什么？和列表有什么区别？": """
返回 `range` 对象：**惰性序列**，按需计算元素，不管多大都只占常数内存（只存 start/stop/step）。

### 考察要点
- 支持 `in`、索引 `r[3]`、len——是序列协议成员，但不是迭代器（可重复遍历）
- `range(10**8)` 立即创建无压力，`list(range(10**8))` 才吃内存

### 追问路线
1. `range(10) == range(0, 10)` 为 True？（range 实现了值相等比较）
2. Python 2 的 xrange 与 3 的 range 的渊源
3. `for i in range(len(lst))` 与 `enumerate(lst)` 哪个好？（后者；直接遍历更好）

> 加分项：能区分"惰性容器（range）"与"一次性迭代器（zip/map）"。
""",

    "请解释 Python 的 GIL 及其对多线程的影响。": """
GIL 是 CPython 解释器级互斥锁：同一时刻仅一个线程执行 Python 字节码。

### 考察要点
- 结论分两条：**CPU 密集**多线程无法并行（应多进程）；**IO 密集**多线程仍有效（等待时释放 GIL）
- 典型误区：GIL = 线程不安全。其实共享状态仍有竞态，该加锁还要加锁

### 追问路线
1. 选型题：爬虫下载 / 数值计算 / Web 服务分别用什么并发模型？
```python
from concurrent.futures import ProcessPoolExecutor  # CPU 密集
from concurrent.futures import ThreadPoolExecutor  # IO 密集、简单场景
import asyncio                                      # IO 密集、高并发
```
2. 演进：PEP 703 free-threading（3.13 实验性可选，3.14 继续）逐步移除 GIL
3. `sys.setswitchinterval` 与检查点机制

> 加分项：能说出 C 扩展（numpy 等）计算时会释放 GIL，所以"CPU 密集 + numpy"多线程也有效。
""",

    "什么是装饰器？请实现一个打印函数执行耗时的装饰器。": """
装饰器是"接收函数、返回新函数"的可调用对象，`@` 语法等价于 `f = deco(f)`。用于日志、计时、缓存、鉴权等横切逻辑。

### 参考实现
```python
import time, functools

def timer(func):
    @functools.wraps(func)          # 保留原函数名与文档
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} 耗时 {time.perf_counter() - t0:.3f}s")
        return result
    return wrapper
```

### 考察要点
- 必写 `functools.wraps`（否则 `__name__` 变 wrapper，调试/序列化出问题）
- 用 `*args, **kwargs` 透传任意签名

### 追问路线
1. 不写 wraps 会引发什么实际问题？（递归按名字找自己、文档丢失）
2. 类装饰器（实现 `__call__`）与函数装饰器的取舍
3. `time.time` 与 `time.perf_counter` 的差别（单调高精度，适合计时）

> 加分项：主动提到装饰器在导入时就生效，以及如何在装饰器里读取被装饰函数的签名。
""",

    "生成器是什么？yield 的执行原理？": """
含 `yield` 的函数调用时**不执行函数体**，而是返回生成器对象；每次 `next()` 执行到 yield **暂停并交出值**，局部变量与执行位置完整保留，下次从暂停处继续。

### 考察要点
- 惰性求值：处理大文件/无限序列不爆内存
- 生成器是迭代器，只能消费一次

### 追问路线
1. 逐行读 10GB 日志统计，为什么生成器是标准答案
2. yield 表达式可接收值（`x = yield`），与 send 的关系
3. 生成器表达式 `(x*x for x in ...) `与列表推导的内存差异

```python
def read_large(path):
    with open(path, encoding='utf-8') as f:
        for line in f:      # 文件对象本身也是生成器式迭代
            yield line.strip()
```

> 加分项：知道生成器协程是 asyncio 的前身（yield from → await 的演化）。
""",

    "什么是闭包？有哪些应用场景？": """
闭包 = 内层函数 + 它捕获的外层作用域变量（存在 `__closure__` cell 里），外层函数返回后这些变量仍存活。

### 考察要点
- 经典陷阱：循环里创建闭包共享同一个变量
```python
fs = [lambda: i for i in range(3)]        # 全部输出 2
fs = [lambda i=i: i for i in range(3)]    # 默认参数绑定当前值
```
- 应用：装饰器、回调携带上下文、工厂函数、偏函数

### 追问路线
1. 怎么查看闭包捕获了什么？（`f.__closure__`、`cell.cell_contents`）
2. 闭包变量为什么默认只读，改外层变量为什么要 nonlocal？
3. 装饰器与闭包的关系（装饰器就是靠闭包保存原函数）

> 加分项：能讲清"晚绑定"（late binding）——闭包捕获的是变量本身而非创建时的值。
""",

    "with 语句的原理是什么？如何自定义上下文管理器？": """
`with` 调用对象的 `__enter__`（进入，返回值绑定 as 变量），退出时无论是否异常都调用 `__exit__(exc_type, exc_val, tb)`；`__exit__` 返回 True 可**吞掉异常**。

### 两种实现
```python
# 方式一：类
class Timer:
    def __enter__(self):
        self.t = time.perf_counter(); return self
    def __exit__(self, *exc):
        print(time.perf_counter() - self.t); return False

# 方式二：生成器装饰器（更简洁）
from contextlib import contextmanager
@contextmanager
def timer():
    t = time.perf_counter()
    try:
        yield          # yield 前后分别对应 enter/exit
    finally:
        print(time.perf_counter() - t)
```

### 追问路线
1. `contextlib.suppress`、`closing`、`ExitStack` 各解决什么？
2. 多个临时资源的组合释放顺序（后进先出）

> 常见误区：以为 with 只是 try/finally 的语法糖——它还是协议，异常信息可被 `__exit__` 检查和抑制。
""",

    "可变默认参数有什么陷阱？如何避免？": """
默认值在**函数定义时求值一次**，此后所有调用共享同一个对象。

```python
def add_item(item, lst=[]):        # 危险：所有调用共享同一个 list
    lst.append(item); return lst   # 结果越积越多

def add_item(item, lst=None):      # 正确
    if lst is None:
        lst = []
    return lst
```

### 考察要点
- 能解释"为什么"：默认值存在函数对象 `__defaults__` 里，随函数存活
- 同理适用于 dict/set 等一切可变默认值

### 追问路线
1. 什么场景"共享默认值"反而是特性？（缓存、记忆化，但要说明线程安全）
2. `inspect.signature` 里怎么看默认值？
3. 类属性 vs 实例属性的同类陷阱（类属性被可变对象共享）

> 加分项：lint 工具（flake8-B008 / ruff B006）会抓这个坑。
""",

    "Python 的垃圾回收机制是怎样的？": """
CPython 以**引用计数**为主（归零立即回收），辅以**分代收集**处理循环引用：
- 新生代→老生代，默认阈值 700/10/10，存活越久扫描越少
- 循环引用靠"标记-清除"找到不可达的引用环

### 考察要点
- 为什么引用计数搞不定循环引用（互相引用计数不归零）
- `gc` 模块：`gc.collect()`、`gc.get_referrers`、可关闭自动 GC

### 追问路线
1. 什么情况内存"泄漏"但 GC 无能为力？（全局缓存/闭包/异常回溯持有大对象引用）
2. `__del__` 的坑（循环引用时不可靠；3.4 后 PEP 442 缓解）
3. weakref 弱引用如何打破持有关系

> 加分项：知道 PyPy 用纯追踪 GC、CPython 3.13+ free-threading 下引用计数的改造。
""",

    "Python 中如何选择多线程、多进程、协程？": """
按任务类型与扩展库选择：

| 方案 | 适合 | 特点 |
| --- | --- | --- |
| 多线程 | IO 密集 + 简单场景 | 等待时释放 GIL；共享内存需加锁 |
| 多进程 | CPU 密集 | 真并行；开销大、需序列化通信 |
| asyncio | 高并发 IO（万级连接） | 单线程事件循环；生态需 async 化 |

### 考察要点
- 决策顺序：先看是 IO 还是 CPU 密集，再看并发量级与库支持
- 混合方案：进程池 × 每进程内 asyncio

### 追问路线
1. requests + 多线程 vs aiohttp + asyncio 怎么选？
2. CPU 密集只有一小段，值得开进程吗？（扩展库/numpy 释放 GIL 的场景线程即可）
3. 协程切换比线程省在哪？（用户态、无内核上下文切换）

> 加分项：能指出"协程不提升单任务速度，只提升吞吐/并发承载"。
""",

    "async/await 和 asyncio 事件循环的工作原理？": """
- `async def` 定义**协程函数**，调用返回协程对象（不执行）
- `await` 把控制权**让渡**给事件循环，等待的 Future 完成后从断点恢复
- 事件循环在单线程内基于 IO 多路复用（epoll/kmap/IOCP）轮询就绪事件，驱动协程推进

### 考察要点
- 并发本质：所有协程在同一线程交错执行，await 处让出
- `asyncio.gather` / `TaskGroup` / `create_task` 的并发原语

### 追问路线
1. 忘写 await 会怎样？（只创建协程不执行，并有 RuntimeWarning）
2. 协程里调用 time.sleep 会怎样？（阻塞整个循环 → 应用 `await asyncio.sleep`）
3. `asyncio.run` 做了什么？（新建循环、跑主协程、关闭）

> 加分项：知道"CPU 密集片段"会卡死整个循环，应丢进 `run_in_executor`。
""",

    "Python 变量作用域的 LEGB 规则是什么？global 和 nonlocal 的作用？": """
名字查找顺序：**L**ocal → **E**nclosing（闭包外层函数）→ **G**lobal（模块）→ **B**uilt-in。

- `global x`：函数内声明的 x 指向**模块级**变量，可重新绑定
- `nonlocal x`：指向**最近外层函数**的同名变量，用于闭包内修改捕获变量

### 考察要点
- 经典陷阱：函数内先读后写同名变量 → UnboundLocalError（编译期把 x 判定为局部）
- 闭包里 counter 不加 nonlocal 无法累加

### 追问路线
1. 为什么只读不需要 global，赋值才需要？
2. `globals()` / `locals()` 的用法与坑
3. 循环内定义函数引用循环变量的晚绑定问题

> 加分项：能解释 nonlocal 找的是"词法作用域最近一层"，与运行时调用栈无关。
""",

    "__new__ 和 __init__ 的区别？": """
- `__new__(cls, ...)`：**创建**实例（静态方法），返回实例后才调用 `__init__` 做初始化
- `__init__(self, ...)`：**初始化**已创建的实例，不返回任何东西（返回非 None 报错）

### 考察要点
- `__new__` 的应用：单例、不可变类型定制（int/str/tuple 子类）、元类配合
- 单例模式现场写：`__new__` 里 `cls._instance` 判断

### 追问路线
1. `__new__` 返回别的类的实例会怎样？（`__init__` 不会被调用）
2. 为什么不可变类型（str/int）定制要在 `__new__` 里改值？
3. `object.__new__` / `__init__` 被重复调用的问题（pickle 等场景）

> 加分项：知道 `__new__` 是真正的"构造"，`__init__` 是"初始化"，术语上区分清楚。
""",

    "什么是鸭子类型？和传统继承多态有什么不同？": """
"关注对象能做什么，而不是它是什么"：只要实现了所需方法（走起来像鸭子、叫起来像鸭子），即可接受，不要求继承同一基类。

### 对比
- 继承多态：`isinstance(obj, Base)` 显式约束，静态语言主流
- 鸭子类型：按**协议**工作——`__len__`、`__iter__`、`__call__` 等，Python 内建行为大多如此（for 不检查类型，只要可迭代）

### 追问路线
1. `len(x)` 与 `x.__len__()`、for 与 `__iter__` 的协议链
2. 鸭子类型的代价（运行期才发现缺方法）与补救（`typing.Protocol` 结构化类型 + 静态检查）
3. `collections.abc` 的抽象基类与鸭子类型如何配合（`__subclasshook__`）

> 加分项：能举 numpy 代替 list 直接进数学库的例子，说明"协议而非类型"的实用价值。
""",

    "functools.lru_cache 的作用和原理？什么场景使用？": """
用哈希表 + 双向链表（LRU 淘汰）缓存"参数 → 返回值"：命中直接返回，未命中计算后存入，超容量淘汰最久未使用项。

### 适用与不适用
- ✅ 纯函数、参数可哈希、重复调用多：递归（斐波那契/爬楼梯）、配置解析、API 结果缓存
- ❌ 有副作用、参数含 list/dict（unhashable 直接报错）、返回可变对象被调用方修改（缓存污染）

### 追问路线
1. `@lru_cache(maxsize=None)` 与 `@cache` 的关系（3.9+ 别名）
2. `cache_info()` 的 hit/miss 怎么用来看收益？
3. 装了 lru_cache 的函数怎么失效？（`cache_clear()`；或 key 里带版本号）

> 加分项：知道缓存返回可变对象的坑——调用方改了它，下一个命中者拿到脏数据；建议返回不可变对象或深拷贝。
""",

    "str 和 bytes 的区别？encode/decode 是做什么的？": """
- `str`：Unicode 文本（抽象字符序列）
- `bytes`：字节序列（原始 0-255）
- `encode`：str → bytes（按编码 utf-8/gbk...）；`decode`：bytes → str

### 考察要点
- 编解码必须成对且用同一编码，否则 UnicodeDecodeError / 乱码
- IO 边界原则：**外部世界走 bytes，程序内部统一 str**，在入口处 decode、出口处 encode

### 追问路线
1. utf-8 与 gbk 中文占几字节？BOM 是什么？
2. 打开文件不指定 encoding 在 Windows 上会发生什么？（默认 GBK，跨平台乱码）
3. `b"abc"` 与 `"abc"` 混用拼接/比较会怎样？（TypeError / False）

> 加分项：能讲"Unicode 是字符集，UTF-8 是编码方案"的区别，术语准确。
""",

    "Python 如何做类型注解？它影响运行时吗？": """
语法：`def f(x: int, name: str = "") -> bool: ...`、`lst: list[int] = []`。运行时**不强制**——注解存进 `__annotations__`，解释器不做检查；靠 mypy / pyright 等静态检查器或 runtime 校验库（pydantic）落实。

### 考察要点
- 基本容器注解与泛型：`dict[str, list[int]]`、`Optional[int] = None`
- `TypedDict`、`Literal`、`Protocol` 的场景

### 追问路线
1. `from __future__ import annotations` 是干嘛的？（延迟求值，注解变字符串，避免前向引用问题）
2. pydantic 如何用注解在运行时做校验？
3. 类型注解的性能代价？（几乎为零，仅存元数据）

> 加分项：知道注解可被 `typing.get_type_hints` 提取，是 FastAPI 等框架自动生成接口文档与校验的基础。
""",

    "静态方法、类方法、实例方法有什么区别？": """
- **实例方法**：第一个参数 self，可访问实例状态
- **类方法**（`@classmethod`）：第一个参数 cls，可访问/修改类状态；常用作**备选构造器**（`from_json`）
- **静态方法**（`@staticmethod`）：无隐式首参，就是恰好放在类命名空间里的普通函数

### 考察要点
- 能各举一个真实用例而不是复述定义
- 继承时类方法拿到的是**实际调用的子类**（cls 多态）

### 追问路线
1. `dict.fromkeys` 为什么设计成类方法？
2. 工厂模式用 classmethod 怎么写？
3. 子类调用父类的 classmethod，cls 是谁？（子类）

> 加分项：知道 Python 里方法就是描述符，实例方法通过 `__get__` 绑定 self。
""",

    "什么是猴子补丁（monkey patching）？有什么风险？": """
运行时动态替换模块/类的属性或方法，改变其行为。典型用途：测试里 mock、紧急热修、给第三方库加钩子。

```python
import some_lib
some_lib.fetch = my_fetch   # 之后所有调用 some_lib.fetch 的代码行为改变
```

### 风险
- 隐式全局影响：所有使用方同时被改，排查困难
- 升级即碎：依赖库内部实现变化后补丁失效
- 补丁时机不确定（导入顺序），并发打补丁有竞态

### 追问路线
1. 测试里 `monkeypatch.setattr` 与手打补丁的区别（自动还原作用域）
2. pytest/unittest.mock 的 patch 为什么推荐装饰器/上下文管理器形式？

> 加分项：能说出更稳的替代——依赖注入、适配器、fork 库发版；补丁是最后手段。
""",

    "什么是元类（metaclass）？有哪些实际应用？": """
元类是"类的类"：`class Foo(metaclass=Meta)` 时，Foo 这个**类对象由 Meta 创建**。类的创建过程（属性收集、命名空间处理）可被元类介入。

### 考察要点
- 理解 `type(name, bases, ns)` 三参调用即可动态造类
- 常见应用：ORM 模型注册（Django Model 把字段映射成表结构）、接口/抽象强制、单例、属性自动改名

### 追问路线
1. `__init_subclass__`（3.6+）能替代哪些简单元类场景？（子类钩子，无需元类）
2. 元类的 `__new__` 与 `__call__` 分别介入什么阶段？
3. "元类冲突"是怎么产生的？（多继承且元类不同）

> 加分项：能引用 Tim Peters 那句"如果你不确定是否需要元类，那你就不需要"。
""",

    "描述符协议的原理是什么？property、classmethod 是怎么实现的？": """
描述符：定义 `__get__` / `__set__` / `__delete__` 的对象，作为**类属性**时拦截实例对该名字的访问。
- 数据描述符（含 `__set__`）：优先级高于实例 `__dict__`——property、`__slots__` 属于这类
- 非数据描述符（仅 `__get__`）：实例字典优先——普通函数、classmethod 属于这类

### 考察要点
- 属性查找顺序：数据描述符 → 实例 `__dict__` → 非数据描述符/类属性
- `obj.method` 的绑定机制就是非数据描述符 `__get__` 返回绑定方法

### 追问路线
1. 手写一个 `Field` 描述符实现类型校验 ORM 字段
2. property 的 setter/deleter 语法
3. 为什么描述符必须定义在类上、不能放实例上？

> 加分项：知道 `functools.cached_property` 是非数据描述符（写回实例 dict），第二次访问不再走描述符。
""",

    "实现一个带参数的装饰器（如重试 retry(3)），要注意什么？": """
带参装饰器是**三层**结构：最外层收参数 → 中间层收函数 → 最内层收调用参数。

```python
def retry(times=3, delay=1):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if i == times - 1:
                        raise
                    time.sleep(delay * (2 ** i))   # 指数退避
        return wrapper
    return deco

@retry(times=3)     # 注意：带参必须加括号
def call_api(): ...
```

### 注意点
- `@retry` 与 `@retry()` 效果不同——前者 func 被当成 times；可写兼容层判断第一个参数是不是 callable
- wraps 必不可少；只重试预期异常（ValueError→具体异常类）

### 追问路线
1. 怎么让装饰后的函数还能拿到原函数（`wrapper.__wrapped__`）
2. 指数退避 + 抖动（jitter）防雪崩

> 加分项：主动提"只捕获可重试异常，网络类错误分类处理"。
""",

    "不使用 functools，手写一个 LRU 缓存类，思路是什么？": """
数据结构 = **dict（O(1) 查找）+ 双向链表（O(1) 移动/删除）**：
- 命中：返回值并把节点移到头部（最近使用）
- 未命中：写入头部；超容量删尾部（最久未用）

```python
class Node:
    __slots__ = ('k', 'v', 'prev', 'next')

class LRUCache:
    def __init__(self, cap):
        self.cap = cap; self.d = {}
        # 头尾哨兵简化边界判断
        self.head, self.tail = Node(), Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, n): ...
    def _push_front(self, n): ...
    def get(self, k):
        if k not in self.d: return -1
        n = self.d[k]; self._unlink(n); self._push_front(n)
        return n.v
    def put(self, k, v):
        if k in self.d: self._unlink(self.d[k])
        n = Node(); n.k, n.v = k, v
        self.d[k] = n; self._push_front(n)
        if len(self.d) > self.cap:
            last = self.tail.prev
            self._unlink(last); del self.d[last.k]
```

### 追问路线
1. 用 `collections.OrderedDict`（move_to_end + popitem(last=False)）三行实现
2. 哨兵节点为什么能简化代码？
3. 线程安全怎么加？（方法级 Lock）

> 加分项：主动说明"dict+双向链表"组合的来由——两个结构互补各自的 O(1) 短板。
""",

    "Python 多进程间有哪些通信方式？各适合什么场景？": """
| 方式 | 特点 | 适用 |
| --- | --- | --- |
| `multiprocessing.Queue` | 进程安全队列，pickle 序列化 | 生产者-消费者、任务分发 |
| `Pipe` | 双端连接，更快 | 两个进程间点对点 |
| `shared_memory` / Value/Array | 共享内存，零拷贝 | 大块数值数据（图像/数组） |
| `Manager` | 代理对象（dict/list 跨进程共享） | 结构复杂但吞吐不高 |
| 文件/Redis/消息队列 | 跨机器 | 服务间、持久化 |

### 考察要点
- 知道进程间不共享内存，一切 IPC 都要序列化或共享内存
- 大数组 pickle 的开销 → shared_memory / numpy 的多进程共享

### 追问路线
1. `Pool.map` 与 `Queue` 手写 worker 的取舍
2. 共享内存谁负责释放？（`resource_tracker`、引用计数）
3. Windows 上为什么必须有 `if __name__ == '__main__'`？（spawn 重新导入模块）

> 加分项：能对比线程 Queue（内存共享、锁保护）与进程 Queue（序列化）的实现差异。
""",

    "CPython 的内存管理为什么要用对象池/内存池（pymalloc）？": """
两层设计：
- **对象特性**：Python 一切皆对象，int 甚至都有类型头和引用计数——小对象创建/销毁极其频繁
- **pymalloc**：小于 512B 的对象走内存池（arena 256KB → pool 4KB → block），**回收不还给 OS**，而是留在池里复用，避免频繁 malloc/free 系统调用与碎片

### 考察要点
- 能讲出 arena/pool/block 三级结构
- 小整数缓存（-5~256）与字符串驻留是对象复用的另一层

### 追问路线
1. 为什么大量创建小对象内存占用不降？（池内空闲、未触发 arena 释放）
2. `sys.getsizeof` 看到的大小与实际占用的区别
3. free-threading 构建下 pymalloc 面临什么问题？（需每线程 arena，3.13 起调整）

> 加分项：把"对象池"与"引用计数"连起来讲：销毁只是 block 归还池、引用归零立即触发。
""",

    "Python 性能优化的常见手段有哪些？如何定位瓶颈？": """
**先定位后优化**：
```bash
python -m cProfile -s cumulative app.py    # 函数级耗时
# 线上/长进程：py-spy top --pid <pid>     # 采样式，不侵入
```

### 优化手段（按性价比排序）
1. **算法与数据结构**：O(n²) → O(n)；list 成员判断改 set
2. **用对内建**：内建函数/推导式比手写循环快（C 实现）；字符串拼接 join
3. **减少重复计算**：lru_cache、循环外提、生成器省内存
4. **并发**：IO 密集线程/协程，CPU 密集多进程
5. **换工具**：numpy 向量化；热点路径 Cython/Rust/ctypes
6. **缓存层**：Redis、HTTP 缓存

### 追问路线
1. cProfile 的 tottime 与 cumtime 区别？
2. memory_profiler / tracemalloc 查内存
3. 什么信号说明该上多进程而不是继续调代码？

> 加分项："先测量、后优化；不成熟的优化是万恶之源"——能说出具体数据支撑决策。
""",

    "asyncio 中怎么执行阻塞的同步代码（如 requests、time.sleep）而不卡死事件循环？": """
把阻塞调用丢进**线程/进程池**，用 await 挂起当前协程、让事件循环继续跑别的任务：

```python
import asyncio, time

async def main():
    # 3.9+：直接用 asyncio.to_thread（线程池）
    r = await asyncio.to_thread(time.sleep, 2)

    # 兼容写法 / CPU 密集用进程池
    loop = asyncio.get_running_loop()
    r2 = await loop.run_in_executor(None, blocking_io)          # 默认线程池
    r3 = await loop.run_in_executor(ProcessPoolExecutor(), cpu_heavy)
```

### 考察要点
- 能说清"卡死"的原理：事件循环单线程，同步阻塞期间所有协程都停
- 线程池 vs 进程池的选择（IO 阻塞 / CPU 密集）

### 追问路线
1. `to_thread` 与 `run_in_executor` 的关系？（前者是后者的易用封装）
2. 为什么不推荐在协程里直接调用 requests？（应换 aiohttp/httpx.AsyncClient）
3. 大量阻塞任务全丢线程池会怎样？（默认线程数有限，需调 executor）

> 加分项：知道 GIL 下 IO 阻塞线程确实会让出，所以线程池对 requests 这类是有效的。
""",

    "Python 有哪些内置数据类型？分别举两个例子。": """
按类别记忆：

| 类别 | 类型 |
| --- | --- |
| 数值 | int、float、complex、bool（int 子类） |
| 序列 | str、list、tuple、range、bytes |
| 散列/集合 | dict、set、frozenset |
| 二进制 | bytearray、memoryview |
| 其他 | NoneType、enumerate/zip 等迭代器 |

### 考察要点
- 分类清晰而不是流水账；能说出可变性归属
- bool 是 int 子类（`True + True == 2`）这类细节

### 追问路线
1. 哪些是有序的？哪些可哈希？
2. `range` 和 `str` 都不可变，带来的好处？
3. memoryview 的零拷贝场景

> 常见误区：把 set/dict 说成"无序所以随机输出"——3.7+ dict 是插入有序的。
""",

    "Python 里如何实现类似 switch-case 的分支？": """
三种主流方案：
```python
# 1. 字典派发（经典）
ops = {'add': lambda a, b: a + b, 'sub': lambda a, b: a - b}
result = ops.get(op, default)(x, y)

# 2. match-case 结构化匹配（3.10+）
match command.split():
    case ['go', direction]:       move(direction)
    case ['drop', *items]:        drop(items)
    case _:                       print('unknown')

# 3. if/elif 链（分支少时最直白）
```

### 考察要点
- 知道 3.10 前没有 switch，字典派发是惯用法
- match 的本质是**结构模式匹配**而非简单值比较：解构、序列/映射/类模式、捕获变量、守卫 `if`

### 追问路线
1. match-case 里 `_` 与 `case 0` 的区别？
2. 类模式 `case Point(x=0, y=y)` 匹配时发生了什么？（`__match_args__`）
3. 字典派发怎么处理默认分支？（`.get(op, default_fn)`）

> 加分项：能说 match 是"绑定名字"而非"比较值"——`case x:` 永远匹配并把值绑给 x。
""",

    "break 和 continue 的区别是什么？": """
- `break`：**终止整个循环**，跳到循环体之后
- `continue`：**跳过本次剩余语句**，直接进入下一轮迭代（while 是回到条件判断，for 是取下一个元素）

### 考察要点
- 能配对说清多层循环里 break 只跳出**最内层**
- 与 else 子句联动：break 后 else 不执行

### 追问路线
1. 怎么一次跳出多层？（标志位 / 提炼成函数用 return / 异常 / for-else）
2. 半成品循环：continue 前忘记推进游标的死循环
3. 语义化建议：复杂嵌套循环拆函数，return 替代 break 更清晰

> 这是基础题，重点看表达是否准确、无含糊；答错内外层语义通常是信号。
""",

    "for 循环的 else 子句什么时候执行？": """
**循环未被 break 打断而正常结束**（包括迭代 0 次）时执行 else；一旦 break 则跳过。

```python
for u in users:
    if u.name == target:
        print('found'); break
else:                       # 没找到（循环走完没 break）
    print('not found')
```

### 考察要点
- else 的语义是"没有 break / 搜索失败"，不是"循环后"
- while 的 else 同理：条件变 False 正常退出时执行

### 追问路线
1. `for ... else` 等价于什么写法？（found 标志位）
2. 为什么很多人认为这个设计不直观？（else 关键字复用；3.10 曾有提议改用 `nobreak` 未通过）
3. 实战场景：找第一个满足条件的元素，找不到给默认值

> 加分项：能用"搜索/查找"场景自然说出用法，而不是背规则。
""",

    "dict.get、setdefault 和 collections.defaultdict 有什么区别？": """
三者的核心差异在"键不存在时做什么"：
- `d.get(k, default)`：返回默认值，**不写入**字典
- `d.setdefault(k, v)`：不存在则**写入** v 并返回；注意 v **总是会被求值**（即使键已存在）
- `defaultdict(factory)`：访问缺失键时自动调用 factory 建默认值写入，之后同键访问复用

### 典型场景
```python
groups = defaultdict(list)
for x in items:
    groups[x.type].append(x)      # 无需判断键是否存在
```

### 追问路线
1. setdefault 传工厂调用的坑：`d.setdefault(k, expensive())` 每次都执行 expensive
2. defaultdict 访问（不只是读值，`d[k]`）就会插入默认值，遍历前误访问会污染
3. `__missing__` 钩子：自定义 dict 子类的扩展点

> 加分项：分組/聚合题能直接 defaultdict(list) 现场写对，说明肌肉记忆到位。
""",

    "列表的 append、extend、insert 有什么区别？": """
- `append(x)`：尾插**一个元素**——`[1,2].append([3,4])` 得 `[1,2,[3,4]]`
- `extend(iter)`：把可迭代对象**逐个**追加——`[1,2].extend([3,4])` 得 `[1,2,3,4]`（等价 `+=`）
- `insert(i, x)`：在位置 i 前插入，**O(n)** 移动后续元素

### 考察要点
- append 一个列表 vs extend 同一列表的结果差异是必考细节
- 头部插入的性能陷阱 → 用 `collections.deque.appendleft`

### 追问路线
1. `a += [1]` 与 `a = a + [1]` 的区别（原地 vs 新对象）
2. deque 与 list 的复杂度对比（头尾 O(1) vs 头部 O(n)）
3. 大量 extend 用 `itertools.chain` 或推导式替代多次调用

> 常见误区：append([3,4]) 之后 len 变 3 而不是 4，没意识到元素本身是那个列表。
""",

    "dict 的 keys()/values()/items() 返回的是什么？": """
返回**动态视图（view）对象**：不是拷贝，是底层字典的"活窗口"——字典变化视图跟着变；本身可迭代、支持 len/in，`keys()` 还支持集合运算。

### 考察要点
- 迭代字典时修改字典会 RuntimeError → 需先 `list(d.keys())` 固化
- `d.keys() & other.keys()` 求交集是合法的视图集合运算

### 追问路线
1. 视图与 `list(d.keys())` 的内存与语义差异
2. Python 2 的行为（返回列表拷贝）与 3 的区别
3. 迭代中安全删除：`for k in [k for k in d if ...]: del d[k]`

> 加分项：知道视图是惰性的、不占额外数据副本；这也解释了它为何能反映实时修改。
""",

    "Python 程序如何接收命令行参数？": """
三个层次：
```python
import sys
print(sys.argv)              # 最原始：[脚本名, 参数字符串...]，无类型转换

import argparse              # 标准库首选
p = argparse.ArgumentParser(description='示例')
p.add_argument('path')                       # 位置参数
p.add_argument('-n', '--num', type=int, default=10)
p.add_argument('-v', action='count', default=0)   # 计数开关
args = p.parse_args()        # 自动生成 -h 帮助

# 现代第三方选择：typer（基于类型注解，FastAPI 风格）
```

### 考察要点
- argparse 的 type/default/choices/action 常规用法
- 知道 sys.argv[0] 是脚本路径

### 追问路线
1. 子命令（git 风格 add/commit）怎么写？（`add_subparsers`）
2. 布尔参数的坑：`--flag true` 不是想象的那样（应用 action='store_true'）
3. 需要交互式补全/彩色输出会考虑什么库？（rich/click/typer）

> 加分项：按"临时脚本 sys.argv、正式工具 argparse/typer"分层给出选择。
""",

    "lambda 表达式是什么？有什么局限？": """
lambda 是匿名单表达式函数：`sorted(users, key=lambda u: u.age)`。只能写**一个表达式**，结果即返回值；不能有语句（赋值/while/try）、不能直接定义命名内部函数。

### 考察要点
- 正确定位：作为 key/回调的"一次性小函数"，与 def 生成同样的函数对象
- 局限清单：无语句、无注解（旧版）、难调试（名字是 `<lambda>`）

### 追问路线
1. 复杂 key 排序更好的写法？（def 或 operator.itemgetter/attrgetter）
2. 循环里 lambda 捕获循环变量的晚绑定坑
3. `key=lambda x: (x.a, -x.b)` 多级排序

> 常见误区：以为 lambda "更快"。它与 def 生成的对象没有性能差别。
""",

    "map、filter、reduce 各做什么？": """
- `map(f, it)`：对每个元素应用 f，返回惰性迭代器
- `filter(pred, it)`：保留使 pred 为真的元素，惰性
- `reduce(f, it, init)`：滚动聚合两两归约为单值（functools 模块）

```python
nums = [1, 2, 3, 4, 5]
list(map(str, nums))                      # ['1','2','3','4','5']
list(filter(lambda n: n % 2, nums))       # [1, 3, 5]
reduce(lambda a, b: a * b, nums, 1)       # 120 阶乘
# 现代更常见写法：
[str(n) for n in nums]                    # 推导式通常更直观
sum(n for n in nums if n % 2)             # 内置聚合优先
```

### 考察要点
- map/filter 返回迭代器（3.x），需 list() 固化
- 知道推导式/生成器表达式是更 Pythonic 的选择

### 追问路线
1. reduce 为什么被移出内建？（Guido 不鼓励，多数场景有 sum/max/any 替代）
2. 多序列 map：`map(lambda a, b: a + b, xs, ys)` 按短截断
3. 惰性链 map(filter(...)) 的求值时机

> 加分项：能对比"函数式三件套"与推导式的可读性取舍，而不是教条站队。
""",

    "if __name__ == '__main__' 是什么作用？": """
模块被**直接运行**时 `__name__` 等于 `'__main__'`；被 **import** 时等于模块名。该判断让"入口逻辑"只在直接执行时跑，被导入时不执行。

### 考察要点
- 双重用途：模块既提供函数，又可作脚本执行（`python mytool.py args`）
- 多进程（Windows/macOS 的 spawn 启动方式）**必须**有它：子进程重新 import 主模块，没有守卫会无限递归创建进程

### 追问路线
1. `python -m mypkg` 方式运行时 `__name__` 是什么？（`__main__`）
2. 包内模块如何写可执行入口？（`__main__.py`）
3. 没写它、被 import 时执行了 print/连接数据库会发生什么？

> 加分项：能主动连到 multiprocessing spawn 的坑，说明踩过或读过原理。
""",

    "Python 命名中的单下划线、双下划线前缀、双前后下划线分别是什么含义？": """
| 形式 | 含义 |
| --- | --- |
| `_name` | 约定俗成的"内部"标识（import * 不导入） |
| `name_` | 避开关键字冲突（class_） |
| `__name` | 类内触发**名称改写**（`_ClassName__name`），子类不易覆盖 |
| `__name__` | 魔术方法/属性（Python 保留），自己别发明新的 |

### 考察要点
- 名称改写不是"私有访问控制"——只是避免继承冲突/误用，仍可从外部访问改写后的名字
- 能列几个常用 dunder：`__init__ __repr__ __eq__ __len__ __enter__`

### 追问路线
1. 为什么说 Python 没有真私有？"约定优于强制"的设计哲学
2. 名称改写在什么场景真的有用？（防子类覆盖的内部缓存属性）
3. `__all__` 控制的是什么的导出？

> 常见误区：说 `__x` 是"私有变量、外部不能访问"——能纠正这一点说明理解到位。
""",

    "round(2.5) 和 round(3.5) 在 Python 3 里等于几？为什么？": """
**round(2.5) == 2，round(3.5) == 4**。Python 3 采用**银行家舍入（round half to even）**：恰好在 .5 时取偶数，避免统计场景里系统性偏大。

### 考察要点
- 能说出"四舍五入"直觉与 banker's rounding 的差异及原因（累积误差平衡）
- 浮点表示陷阱：`round(2.675, 2)` 得 2.67 而非 2.68，因为 2.675 的二进制表示实际略小于它

### 追问路线
1. 要"传统四舍五入"怎么办？（`decimal.Decimal` + `ROUND_HALF_UP`；或加极小偏移，不推荐）
2. 金融计算为什么要用 Decimal/定点而不是 float？
3. `int()` 截断与 `math.floor/ceil` 的区别

> 加分项：能主动提 float 精度（0.1+0.2 != 0.3）这一族问题。
""",

    "如何把一个 Unix 时间戳与可读时间互相转换？": """
```python
from datetime import datetime, timezone

# 时间戳 → 可读（先转 aware datetime 再格式化）
datetime.fromtimestamp(1760000000, tz=timezone.utc)
datetime.fromtimestamp(1760000000).strftime('%Y-%m-%d %H:%M:%S')

# 可读 → 时间戳
dt = datetime(2025, 10, 9, 12, 0, tzinfo=timezone.utc)
int(dt.timestamp())
```

### 考察要点
- 知道时间戳是 UTC 秒数，而 fromtimestamp 不传 tz 时用**本地时区**
- aware 与 naive datetime 的区别——跨时区/存储场景的根源问题

### 追问路线
1. ISO 8601 字符串怎么解析？（`datetime.fromisoformat`，3.11+ 支持更全）
2. 时区转换：`dt.astimezone(timezone(timedelta(hours=8)))`
3. 数据库/接口里存时间该用什么格式？（UTC 时间戳或 ISO 带 tz，避免 naive）

> 常见误区：`datetime.utcnow()` 返回 naive UTC（已弃用），与 `timestamp()` 混用差 8 小时——能指出此坑是强加分。
""",

    "json.dumps 和 json.loads 的常用参数有哪些？": """
```python
import json
json.dumps(obj,
    ensure_ascii=False,   # 中文不转 \\uXXXX（中文系统必备）
    indent=2,             # 美化缩进
    sort_keys=True,       # 键排序（做签名的稳定序列化）
    default=str)          # 遇到不可序列化对象（date/自定义类）的兜底

json.loads(s,
    object_hook=...,      # dict 层的反序列化钩子
    parse_float=Decimal)  # 精度敏感场景防浮点误差
```

### 考察要点
- ensure_ascii 必须知道，否则中文全是转义
- 遇到 set/datetime 报 TypeError 的处理（default=str 或自写 encoder）

### 追问路线
1. 自定义类怎么优雅序列化？（`default=lambda o: o.__dict__` 或实现协议）
2. `object_pairs_hook` 能做什么？（检测重复键、保序定制）
3. JSON 不支持的类型：set/tuple(转 list)/bytes/NaN（非标准）

> 加分项：用 default=str 时能提醒"反序列化回不来类型"的代价。
""",

    "如何让自定义类的对象支持 for 循环遍历？": """
实现**可迭代协议**：定义 `__iter__` 返回迭代器。最简方式是让它返回一个生成器：

```python
class Team:
    def __init__(self): self.members = ['a', 'b', 'c']
    def __iter__(self):
        return iter(self.members)          # 方式一：委托内置
        # yield from self.members          # 方式二：生成器方法
```

### 考察要点
- `__iter__` 与 `__next__` 的分工：容器只管 `__iter__`
- 想让对象既是容器又是自身迭代器（文件那样一次性遍历）的取舍

### 追问路线
1. 只实现 `__getitem__` 能否被 for 遍历？（旧式协议可以，从 0 开始整数索引，但推荐 `__iter__`）
2. 怎么支持 `len()` / `in` / 反向遍历？（`__len__` / `__contains__` / `__reversed__`）
3. unpack `a, b = obj` 用到什么？（`__iter__`）

> 加分项：知道生成器方法作 `__iter__` 每次调用生成新迭代器，天然支持重复遍历。
""",

    "生成器的 send、throw、close 方法分别做什么？": """
生成器是可双向通信的协程原语：
- `send(v)`：恢复执行，并把 v 作为**当前 yield 表达式的值**送入（`x = yield` 接收）；首次须 `send(None)` 或 next() 启动
- `throw(exc)`：在暂停点**注入异常**，生成器内部可 try 捕获处理
- `close()`：在暂停点注入 GeneratorExit，请求关闭；生成器可做清理

```python
def echo():
    while True:
        x = yield
        print('got', x)

g = echo(); next(g)      # 启动到第一个 yield
g.send('hi')             # got hi
```

### 追问路线
1. `x = yield val` 一行里的两个动作（交出 val / 收回 send 的值）
2. close 时生成器又 yield 会怎样？（RuntimeError）
3. 这些机制与 async/await 的历史关系（生成器协程 → native coroutine）

> 加分项：知道 `yield from` 会把 send/throw **透传**给子生成器——这是它相比手写 for 的本质增强。
""",

    "多个装饰器叠放时，执行顺序是怎样的？": """
**装饰（定义期）自下而上；调用（运行期）自上而下**，像洋葱：

```python
@a
@b
def f(): ...
# 等价于 f = a(b(f))：b 先包住 f，a 再包住 b(f)

f(x)   # 调用时：a 的 wrapper → b 的 wrapper → f
```

### 考察要点
- 用日志+计时+缓存叠放时能说清每层进出顺序
- 定义期立即执行（打印顺序自下而上）与调用期执行分开讲

### 追问路线
1. wraps 在每一层为什么都要写？
2. 缓存装饰器放在最外层/最内层的差别（缓存命中则完全跳过内层）
3. 用 `f.__wrapped__` 还能拿到原函数吗？（多层需逐层解）

> 常见误区：背反了方向。记法："离函数近的先包装（定义），离调用近的先执行（调用）"。
""",

    "property 装饰器怎么用？解决什么问题？": """
把方法伪装成属性访问，实现**读写受控**：

```python
class Temperature:
    def __init__(self): self._c = 0
    @property
    def celsius(self): return self._c
    @celsius.setter
    def celsius(self, v):
        if v < -273.15: raise ValueError('低于绝对零度')
        self._c = v
    @property
    def fahrenheit(self): return self._c * 9 / 5 + 32   # 只读派生属性
```

### 解决的问题
- 属性带**校验/联动/惰性计算**而调用方代码不变（`t.celsius = 30`）
- 先暴露公开属性、后续加逻辑时无需改接口（封装演进而无破坏）
- 只读属性、计算属性

### 追问路线
1. property 是什么描述符？（数据描述符，优先于实例 `__dict__`）
2. 循环依赖坑：setter 里又给同名属性赋值（死递归，应写 `self._x`）
3. `cached_property` 与 property 的差异（首次计算后写回实例 dict）

> 加分项：能讲"从公开属性平滑升级到 property 而调用方零改动"——这是它相对 getter/setter 的核心价值。
""",

    "__slots__ 是做什么的？有什么代价？": """
类定义 `__slots__ = ('a', 'b')` 后，实例**不再有 `__dict__`**，属性直接存在固定的 slot 里：省内存（每实例少一个 dict，通常省 40%+）、属性访问略快。

### 代价
- 不能动态添加未声明属性
- 除非基类也有 `__slots__`（或加 `'__dict__'`），继承会重新引入 dict
- 弱引用需显式加 `'__weakref__'`

### 适用场景
大量小对象：百万级数据行、图/树节点、游戏实体。

### 追问路线
1. `__slots__` 与 `__dict__` 共存的条件？（父类无 slots 或显式包含 `'__dict__'`）
2. 省多少怎么测？（`pympler`/`sys.getsizeof` + tracemalloc 实测）
3. 与 dataclass 配合的写法

> 加分项：知道 slots 本质是**描述符**（每 slot 一个 slot descriptor），并提醒"先测再上"。
""",

    "Python 如何定义抽象基类（ABC）？": """
`abc` 模块：元类 ABCCeta + `@abstractmethod`：

```python
from abc import ABC, abstractmethod

class Storage(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def load(self, key: str) -> bytes: ...

    def exists(self, key):           # 普通方法可复用抽象接口
        return self.load(key) is not None

class S3Storage(Storage):
    def save(self, key, data): ...
    def load(self, key): ...
# Storage() 直接实例化报 TypeError；缺 load 也能拦
```

### 考察要点
- 抽象方法+抽象属性、`@abstractmethod` 与 `@classmethod/@property` 叠放
- 实例化检查发生在**实例化时**而非运行调用时——早失败

### 追问路线
1. ABC 与 Protocol（结构化类型）的选择：接口先行 vs 事后归一
2. `register()` 让既有类"认亲"的玩法
3. collections.abc 的 Iterable/Sized 等如何做"虚拟子类"

> 加分项：能对比 Java 式显式继承与 Python 鸭子类型，说明 ABC 的定位是"可选的显式约束"。
""",

    "dataclass 装饰器有什么用？": """
自动生成样板代码：`__init__`、`__repr__`、`__eq__` 等，专注字段定义：

```python
from dataclasses import dataclass, field

@dataclass
class User:
    name: str
    age: int = 0
    tags: list = field(default_factory=list)   # 可变默认值的正确姿势
    uid: int = field(init=False, default=0)    # 不进 __init__

@dataclass(frozen=True)     # 不可变 + 可哈希（可作 dict 键）
class Point:
    x: float; y: float
```

### 考察要点
- 可变默认值必须 `field(default_factory=list)`（同可变默认参数原理）
- frozen=True 的适用（值对象）；eq/order 的控制

### 追问路线
1. `asdict` / `astuple` 与 FastAPI/pydantic 的关系
2. 继承时字段顺序规则（带默认值字段在后）
3. `__post_init__` 做派生字段与校验

> 加分项：能对比 dataclass（标准库、轻量）与 pydantic（运行时校验、生态）的边界。
""",

    "什么场景用枚举（Enum）？比常量好在哪里？": """
一组**封闭的、相关的符号常量**：状态机、类型码、配置选项、错误码。

```python
from enum import Enum, auto

class OrderStatus(Enum):
    CREATED = auto()
    PAID = auto()
    SHIPPED = auto()
    DONE = auto()

if s is OrderStatus.PAID: ...       # 身份比较
OrderStatus['PAID']                 # 按名取
OrderStatus(2)                      # 按值取
```

### 比裸常量好在哪
- **命名空间隔离**：Status.PAID 与 PayStatus.PAID 不混淆，打印自解释
- **类型安全**：函数签名/序列化可校验合法值域；拼错立即 AttributeError
- 可迭代、可做 dict 键、`@unique` 强制值唯一

### 追问路线
1. IntEnum / StrEnum 的取舍（要 JSON 序列化时 StrEnum 更省心）
2. Enum 与字面量 `Literal['paid','done']` 的选择（轻量 vs 需要方法/迭代）
3. 枚举里定义方法/属性组织状态行为

> 加分项：提到数据库存值、代码用枚举的映射层，说明有真实工程经验。
""",

    "raise ... from ... 是做什么的？自定义异常怎么写？": """
`raise New(...) from e` 设置 **`__cause__`**，保留原始异常链（ traceback 显示 "The above exception was the direct cause..."），排查不丢根因。`from None` 则显式抑制链。

```python
class ConfigError(Exception):
    # 配置相关错误的基类：统一捕获口径
    pass

class ConfigFileError(ConfigError):
    def __init__(self, path, reason):
        super().__init__(f'配置文件 {path} 无效: {reason}')
        self.path = path          # 携带结构化上下文

def load_config(path):
    try:
        return json.loads(read(path))
    except FileNotFoundError as e:
        raise ConfigFileError(path, '不存在') from e   # 链住根因
    except json.JSONDecodeError as e:
        raise ConfigFileError(path, 'JSON 非法') from e
```

### 考察要点
- 自定义异常继承 Exception（不要继承 BaseException）
- 一个业务域一个基类，子类细分——调用方可粗可细地捕获

### 追问路线
1. `__cause__` / `__context__` / 显式 `from None` 的区别
2. 异常里携带上下文（path/参数）对日志与排障的价值
3. EAFP 哲学与异常层次设计

> 加分项：主动讲"在系统边界统一转译异常（底层异常不泄漏给上层）"的分层实践。
""",

    "__str__ 和 __repr__ 的区别？": """
- `__str__`：面向**用户**的可读描述，`print()` / `str()` 调用
- `__repr__`：面向**开发者**的明确表示，理想情况是 `eval` 得回等价对象；交互式回显 / `repr()` / 容器内元素打印都走它

```python
class Point:
    def __init__(self, x, y): self.x, self.y = x, y
    def __repr__(self): return f'Point({self.x!r}, {self.y!r})'
    def __str__(self): return f'({self.x}, {self.y})'

print(Point(1, 2))        # (1, 2)
Point(1, 2)               # Point(1, 2)
print([Point(1, 2)])      # [Point(1, 2)]  ← 容器元素用 repr！
```

### 考察要点
- 只定义 repr 时 str 会兜底用 repr（反之不然）——所以**只写 repr 通常就够**
- 容器打印元素用 repr 这一细节

### 追问路线
1. `{!r}` 与 `{}` 在 f-string 里的区别
2. 日志打印对象为什么建议显式 repr（避免巨量内容刷屏可用截断）

> 加分项：知道默认 repr（`<__main__.Point object at 0x...>`）对排障几乎无用，主动补 repr 是好习惯。
""",

    "collections 模块有哪些常用工具？": """
| 工具 | 用途 | 典型场景 |
| --- | --- | --- |
| `namedtuple` / `NamedTuple` | 带字段名的元组 | 轻量记录、坐标、返回多值 |
| `deque` | 双端队列，头尾 O(1) | 滑动窗口、BFS、LRU 底层 |
| `Counter` | 计数器（dict 子类） | 词频、Top-K（most_common） |
| `defaultdict` | 缺失键自动工厂 | 分组聚合 |
| `OrderedDict` | 有序 dict（3.7 前） | 兼容旧版/需 move_to_end |
| `ChainMap` | 多层映射叠加 | 配置默认值级联 |
| `UserDict/List` | 更好继承的基类 | 定制容器 |

### 考察要点
- Counter：`Counter(words).most_common(3)`；`+`/`-`/交集运算
- deque：`maxlen=5` 自动淘汰——固定长度窗口一行搞定

### 追问路线
1. Counter 统计后按值排序的几种写法
2. defaultdict(list) 做邻接表
3. ChainMap 实现配置优先级（CLI > 环境变量 > 默认）

> 加分项：能立刻说出"这个场景用 collections 里的 XX"而不是手写循环——工具意识是本题真正要考的。
""",

    "itertools 里最常用的函数有哪些？": """
分组记忆：
- 拼接/展开：`chain`（多迭代器串联）、`chain.from_iterable`
- 笛卡尔与组合：`product`（嵌套循环拉平）、`permutations`、`combinations`
- 切分：`islice`（迭代器切片）、`takewhile`/`dropwhile`、`batched`(3.12+)
- 分组：`groupby`（**先排序再分组**是铁律）、`pairwise`
- 无限流：`count`、`cycle`、`repeat`
- 其他：`zip_longest`、`accumulate`（前缀和）

```python
from itertools import chain, groupby, islice, product
flat = chain.from_iterable(nested)
for key, grp in groupby(sorted(data, key=by), key=by): ...
first10 = islice(infinite_stream, 10)
for a, b in product(xs, ys): ...     # 双层循环
```

### 考察要点
- 全部**惰性**、内存友好；配合生成器表达式使用
- groupby 的连续分组语义（不排序会得到碎片组）

### 追问路线
1. product 与 permutations 的区别
2. accumulate 自定义函数做运行最大值
3. zip 与 zip_longest 的截断行为

> 加分项：用 itertools 重写嵌套循环/分页遍历的现场手感，是区分"读过"和"用过"的标志。
""",

    "Python 项目如何管理依赖和虚拟环境？": """
标准三件套：**虚拟环境隔离 + requirements 锁定 + 镜像加速**。

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt    # Windows
# 现代工具链（推荐）：
uv venv && uv pip install -r requirements.txt    # 极快
uv add requests                                  # pyproject.toml + uv.lock
poetry install                                   # pyproject + poetry.lock
```

### 考察要点
- 为什么要虚拟环境：项目间依赖隔离、可复现
- requirements.txt（直接锁版本）与 pyproject.toml（声明依赖）+ lock 文件的分工
- 本地依赖别提交进仓库（.venv 进 .gitignore）

### 追问路线
1. pip freeze > requirements.txt 与 pip-tools compile 的区别
2. 传递依赖锁不住的痛点怎么解？（lock 文件）
3. pipx / conda / docker 各自的适用边界

> 加分项：知道"部署环境用 lock 文件精确复现，开发环境用 pyproject 灵活添加"的双层策略。
""",

    "logging 模块的基本用法？为什么不用 print？": """
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
log = logging.getLogger(__name__)
log.info('user %s login', uid)    # 惰性格式化，别用 f-string
```

### 比 print 强在
1. **级别过滤**：一行配置控制 DEBUG~CRITICAL 输出量，上线免改代码
2. **多目的地**：console + 文件 RotatingFileHandler + 远程（Handler 体系）
3. **结构化元数据**：时间/模块名/进程/异常堆栈（`log.exception()` 自动带 traceback）
4. 按模块 logger 树控制（`__name__`），第三方库噪音可单独降噪

### 追问路线
1. Root logger 重复日志（Handler 叠加）怎么排查？
2. 日志轮转：TimedRotatingFileHandler vs RotatingFileHandler
3. `log.info('x %s', v)` 与 f-string 的差别（级别不够时不格式化，省性能）

> 加分项：提结构化日志（json formatter / structlog）方便 ELK 检索。
""",

    "用 pytest 写单元测试的基本姿势？": """
```python
# test_math.py —— 文件名 test_ 前缀，函数 test_ 前缀即可被发现
import pytest

def add(a, b): return a + b

def test_add():
    assert add(1, 2) == 3          # 原生 assert，失败自动显示 diff

@pytest.mark.parametrize('a,b,exp', [
    (1, 2, 3), (0, 0, 0), (-1, 1, 0),
])
def test_add_many(a, b, exp):
    assert add(a, b) == exp

@pytest.fixture
def user():
    return User(name='u1')          # 依赖注入：参数名=fixture 名

def test_user_name(user):
    assert user.name == 'u1'

def test_error():
    with pytest.raises(ValueError):
        int('abc')
```

### 考察要点
- 与 unittest 比：无类模板、原生 assert、参数化一把梭
- fixture 的 setup/teardown（yield 分界）、conftest.py 共享

### 追问路线
1. `tmp_path` / `monkeypatch` / `capsys` 常用内建 fixture
2. mock 外部依赖：`unittest.mock.patch` + pytest 的 monkeypatch.setattr
3. 覆盖率：`pytest --cov=app --cov-report=term-missing`

> 加分项：会按"一个行为一个测试函数、命名说清场景"组织，而不是一个大函数跑到底。
""",

    "字符串驻留（interning）和小整数缓存是什么？": """
CPython 的**对象复用**优化：
- **小整数缓存**：-5~256 预创建单例，所有引用共享同一对象
- **字符串驻留**：像标识符的字符串（字母数字下划线）常被 intern 共享；编译期常量合并

```python
a = 256; b = 256
a is b        # True（缓存池同一对象）
a = 257; b = 257
a is b        # 交互式下通常 False（各自新建）
```

### 考察要点
- 这是**实现细节**：只保证 is None 这类单例判断，不能依赖 `is` 做值相等
- 运行时拼接的字符串未必驻留：`'a' + 'b'` 结果 is 'ab' 不保证

### 追问路线
1. `sys.intern()` 的用途（大量重复键去重省内存）
2. 为什么把 is 用于数字/字符串比较是 bug 来源？
3. 与 GC 的关系：驻留/缓存对象生命周期是永生的

> 加分项：能一句话定性——"性能优化的副作用，语言规范之外的观察窗口"，说明理解层次。
""",

    "如何在 Python 里做简单的并发下载？": """
按量级选工具：
```python
# 1) 线程池：几十上百个 URL，最省事（IO 密集，GIL 等待时让出）
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=16) as ex:
    futs = {ex.submit(fetch, u): u for u in urls}
    for fut in as_completed(futs):
        try:
            save(fut.result())
        except Exception as e:
            log.warning('fail %s: %s', futs[fut], e)

# 2) asyncio：上千级并发更省资源
import asyncio, aiohttp

async def fetch_all(urls):
    sem = asyncio.Semaphore(32)                    # 并发上限防打挂对端
    async def one(u):
        async with sem:
            async with aiohttp.ClientSession() as s:
                async with s.get(u) as r:
                    return await r.read()
    return await asyncio.gather(*(one(u) for u in urls))
```

### 考察要点
- 异常隔离：单个失败不能掀翻整批
- 限流意识：max_workers / Semaphore，而不是裸开全部

### 追问路线
1. as_completed 与 map 的结果顺序差异
2. 超时与重试怎么加？（future.result(timeout) / retry 装饰器）
3. 线程池开多少合适？（IO 密集常几十，受对端与带宽约束）

> 加分项：主动提"失败收集 + 部分成功"的工程处理，而不是只写 happy path。
""",

    "__getattr__ 和 __getattribute__ 的区别？各适合什么场景？": """
- `__getattribute__(self, name)`：**所有**属性访问都走它（默认实现在 object 里找 dict/描述符/类）——重写极易踩递归与性能坑，只用于 ORM/代理类等重场景
- `__getattr__(self, name)`：**仅在常规查找失败后**才调用（找不到才兜底）——安全得多

```python
class Proxy:
    def __init__(self, target): object.__setattr__(self, '_t', target)
    def __getattr__(self, name):              # 找不到的转发给目标
        return getattr(self._t, name)

class Record:
    def __getattr__(self, name):              # 兜底：字段惰性加载
        if name.startswith('col_'):
            return self._load(name)
        raise AttributeError(name)
```

### 考察要点
- 触发时机差异是核心：`__getattr__` 是 fallback，`__getattribute__` 是拦截一切
- `__getattribute__` 里取其他属性必须 `super().__getattribute__(...)`，否则无限递归

### 追问路线
1. `__setattr__` 与二者的配合（代理写透）
2. `hasattr` 为什么会触发 `__getattr__`（内部吞 AttributeError）
3. ORM 里 `Table.column` 链式查询如何靠这套协议实现

> 加分项：知道 `__getattr__` 里抛 AttributeError 而不是其他异常，才能让 hasattr/getattr 默认值正常工作。
""",

    "多继承时方法解析顺序（MRO）如何确定？": """
Python 用 **C3 线性化**：保持每个父类的相对顺序、且子类永远在父类前、共同父类只出现一次且尽量靠后。用 `Cls.__mro__` 或 `Cls.mro()` 查看。

```python
class A:      def who(self): print('A')
class B(A):   def who(self): print('B')
class C(A):   def who(self): print('C')
class D(B, C): pass

D.__mro__     # D → B → C → A → object
D().who()     # B：沿 MRO 第一个命中
```

### 考察要点
- super() 不是"父类"而是 **MRO 的下一个**：协作式多继承里每个类 super 调用串成链
- 菱形继承：A 只被初始化一次（super 链保证）

### 追问路线
1. 菱形结构里各类 `__init__` 都写 super().__init__() 的执行顺序
2. 什么多继承顺序会报错？（无法 C3 线性化时 TypeError）
3. mixin 模式：mixin 放左边、基类放右边，依赖 super 串行为

> 加分项：能用 mixin（如 LoginRequiredMixin）讲"为什么 Python 多继承在实践中可控"——约定 + super 链。
""",

    "yield from 与生成器委托解决什么问题？它和 async/await 什么关系？": """
`yield from iterable` 把"逐个 yield"委托给子生成器，并**透传 send/throw/close**：

```python
def inner():
    x = yield 'inner-1'
    yield f'got {x}'

def outer():
    yield from inner()          # 委托：简化 + 双向通信透传
    yield 'outer-end'

g = outer(); next(g); g.send('hi')
# 等价于手写：for v in inner(): yield v —— 但那样拿不到 send 的回传
```

### 解决的问题
1. 样板简化：不用手写 for-yield
2. **return 值回传**：`result = yield from sub()` 拿到子生成器 return 的值
3. 双向通信透传——这是生成器协程的基石

### 与 async/await 的关系
- `await coro` 的语义几乎就是 yield from（挂起并等待结果），PEP 492 把它引入 native coroutine
- 生成器协程（@asyncio.coroutine + yield from）→ async/await 是同一条演化线

> 加分项：能说清"yield from 是生成器时代的 await"，展示对 asyncio 起源的理解。
""",

    "如何排查 Python 程序的内存持续增长（疑似泄漏）？": """
Python 里"泄漏"多数是**引用没断开**（缓存、闭包、全局 list、异常回溯），而非真泄漏。

### 排查路径
```python
# 1. 快照对比：哪类对象在涨
import tracemalloc
tracemalloc.start()
s1 = tracemalloc.take_snapshot()
run_requests(1000)
s2 = tracemalloc.take_snapshot()
for stat in s2.compare_to(s1, 'lineno')[:10]:
    print(stat)                       # 文件:行号 + 增量

# 2. 谁引用着它（找持有链）
import gc, objgraph
objgraph.show_backrefs([leaked_obj], filename='ref.png')
objgraph.growth()                     # 类型级增长速览

# 3. 容器内分层：cgroup/RSS 看趋势，tracemalloc 定位 Python 层
```

### 高发点清单
- 全局 dict/list/缓存无上限（加 LRU 上限/weakref）
- 闭包与回调持有大对象（self 被隐式捕获）
- 异常对象与 traceback 持有整条栈帧（sys.exc_info 长期保存）
- C 扩展层的真泄漏（Python 层工具看不到 → valgrind/分配器日志）

### 追问路线
1. gc.collect() 后 RSS 不降就是泄漏吗？（pymalloc 池不还给 OS，正常）
2. weakref / WeakValueDictionary 打破持有的用法
3. 长期任务如何埋内存监控线（psutil 定时采样告警）

> 加分项：先区分"RSS 不降"与"对象数持续涨"再下结论——说明真排过线上问题。
""",

    "描述一下：给一段 Python 热点代码提速，什么情况下选择 ctypes/Cython/Rust 扩展？": """
决策顺序：**先算法/内建/numpy，都不行才上原生扩展**。

| 方案 | 适用 | 特点 |
| --- | --- | --- |
| ctypes | 调**现成** C 库（无绑定） | 零编译，但手写类型签名，回调笨重 |
| Cython | 纯 Python 热点渐进提速 | 语法近 Python，类型标注后可达 C 级；生态成熟 |
| Rust（pyo3/maturin） | 要内存安全 + 并行 + 现代工具链 | 开发成本高，但无 GIL、可发布 abi3 wheel |

### 判断依据
1. 已确认瓶颈在**纯计算**（profiler 证据），且算法无余地
2. 数据能整块进出（序列化开销摊薄）；细粒度往返调用会亏
3. 团队维护能力：Cython 上手最快；Rust 适合长期核心库
4. numpy 能向量化的先向量化（零扩展成本）

### 追问路线
1. 扩展里释放 GIL 才能多线程并行（Cython `nogil` / Rust 天然）
2. 打包与分发：cibuildwheel 跨平台 wheel
3. pybind11（C++）在选项里的位置

> 加分项：能说出"扩展边界要粗粒度 API，别让调用开销吃掉收益"，说明做过真的集成。
""",

    "用 asyncio 实现一个生产者-消费者模型要注意什么？": """
核心组件：`asyncio.Queue`（协程安全，自带容量与挂起唤醒）。

```python
import asyncio

async def producer(q: asyncio.Queue):
    for i in range(10):
        await q.put(i)                 # 满则挂起，不忙等
    # 多生产者时用哨兵/计数通知结束

async def consumer(q: asyncio.Queue):
    while True:
        item = await q.get()
        try:
            await process(item)
        finally:
            q.task_done()              # 配合 join 统计完成度

async def main():
    q = asyncio.Queue(maxsize=5)       # 背压：防止生产过快撑爆内存
    workers = [asyncio.create_task(consumer(q)) for _ in range(3)]
    await asyncio.gather(*(producer(q) for _ in range(2))
    await q.join()                     # 等全部 task_done
    for w in workers:
        w.cancel()                     # 优雅退出：取消 + gather 收尾
    await asyncio.gather(*workers, return_exceptions=True)
```

### 要点清单
- **背压**：maxsize 限制队列，put 自动挂起
- **优雅退出**：join + cancel 的组合；粗暴 while True 不退出是常见错误
- **异常隔离**：单个消费失败不能拖死 worker（try/finally 保证 task_done）
- 消费并行度 = worker 数量，不是越多越好

### 追问路线
1. 与线程版 Queue 的区别（无锁，靠 await 让出）
2. 生产者速度远快于消费者怎么扩容/限流？
3. TaskGroup（3.11+）改写上述结构

> 加分项：主动提"背压"与"取消语义"，说明不止写过 demo。
""",

    "Python 的 import 机制和循环导入问题怎么处理？": """
import 时执行模块顶层代码并缓存进 `sys.modules`；再次 import 直接取缓存。**循环导入**：A import B、B 又 import A，某方拿到"半初始化"模块（属性还没定义）→ ImportError/AttributeError。

### 解法（按推荐顺序）
1. **调整设计**：把互相依赖的部分抽到第三个模块 C（大多数循环是分层失误的信号）
2. **延迟导入**：函数体内 import，运行时才触发（插件/可选依赖常用）
3. **模块底部导入**或 `TYPE_CHECKING` 内导入（仅为类型注解时）
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import User      # 只为注解，运行时不导入

def f(u: 'User') -> None: ...
```
4. 只 import 模块不 import 属性：`import b` 然后用 `b.X`（定义期不取属性）

### 追问路线
1. sys.modules 缓存与 `importlib.reload` 的坑
2. 包的相对导入（`.`/`..`）与 `__init__.py` 的角色
3. 找不到模块怎么排查？（sys.path、虚拟环境是否装了、脚本 vs -m 运行的路径差异）

> 加分项：把循环导入当作"设计味道"来谈——依赖倒置/事件解耦，而不是只给糖式解法。
""",

    "写一个线程安全的计数器和带过期时间的缓存，思路是什么？": """
两个经典并发组件：

```python
import threading, time

class Counter:
    def __init__(self):
        self._n = 0
        self._lock = threading.Lock()      # GIL 不等于线程安全！

    def incr(self, n=1):
        with self._lock:                   # += 是读改写三步，必须整体加锁
            self._n += n
            return self._n

class ExpiringCache:
    def __init__(self, ttl):
        self.ttl = ttl
        self._data = {}                    # key -> (value, expire_at)
        self._lock = threading.Lock()

    def set(self, k, v):
        with self._lock:
            self._data[k] = (v, time.monotonic() + self.ttl)

    def get(self, k):
        with self._lock:
            item = self._data.get(k)
            if not item: return None
            v, exp = item
            if time.monotonic() > exp:     # 惰性过期：读时清理
                del self._data[k]
                return None
            return v
```

### 考察要点
- 计数器：`+=` 非原子是必考点；`itertools.count` + `__next__` 是无锁替代
- 缓存：**time.monotonic**（不受系统时间跳变影响）、惰性过期 vs 后台线程清扫的取舍、锁粒度

### 追问路线
1. Lock 与 RLock 的区别（同线程可重入）
2. 读写多怎么办？（读多写少可考虑分片锁 / threading.local 视图聚合）
3. 过期+容量上限的组合 → 就是简化版 TTL-LRU（参考 Redis expire 策略）

> 加分项：指出"单测试可能测不出竞态"（需要压测或 ThreadSanitizer 思想），并发意识到位。
""",

    "Python 中如何交换两个变量的值？": """
```python
a, b = b, a          # 打包成元组再解包，无需临时变量
```
右侧先求值为 `(b_val, a_val)` 新元组，再按位置解包给左边的名字。任意数量皆可：`a, b, c = c, a, b`。

### 考察要点
- 能讲清机制（元组打包/解包），而不是当魔法背
- 不用临时变量的可读性收益

### 追问路线
1. `a, b = b, a` 与 `a = b; b = a` 的结果差异（后者两值相同——顺序赋值破坏了原值）
2. 不用第三个变量还有别的写法吗？（加减法/异或——但仅限整数且有溢出/可读性问题，不推荐）
3. 解包的其它应用：函数返回多值、`first, *rest = lst`、字典 items 解包

> 基础送分题，看表达与原理是否清晰；顺带能聊到序列解包的广泛用法是加分。
""",

    "isinstance 和 type 有什么区别？": """
- `isinstance(x, T)`：考虑**继承链**（含 ABC 虚拟子类），是判断类型的推荐方式
- `type(x) is T`：精确匹配单个类，子类返回 False

```python
class Animal: ...
class Dog(Animal): ...
d = Dog()
isinstance(d, Animal)     # True（父类也算）
type(d) is Animal         # False（精确类才 True）
isinstance(d, (int, str)) # 元组任一命中即可
```

### 考察要点
- isinstance 接受类型元组
- bool 是 int 子类：`isinstance(True, int)` 为 True——JSON 序列化时的坑

### 追问路线
1. `type(x) == T` 与 `type(x) is T` 哪个对？（is；type 是单例）
2. `__class__` 与 type() 的关系
3. 为什么鸭子类型语境下尽量少用两者，改 EAFP/Protocol？

> 加分项：提到"接口判断用 isinstance(x, collections.abc.Iterable) 这类抽象类"，而非具体类型。
""",

    "Python 的三元表达式（条件表达式）怎么写？": """
```python
value = a if condition else b
# 对比 C 系：condition ? a : b
level = '高' if score >= 80 else '低'
```

### 考察要点
- 语序：**真值结果在前**，条件居中，else 结果在后
- 与 and/or 陷阱：`a and b or c` 不等价三元（b 为假时出错），不要用

### 追问路线
1. 嵌套三元的可读性（应该改 if/elif 或 dict 派发）
2. 条件表达式 vs 立即求值：`x() if cond else y()` 只调用其一
3. 推导式里的位置：`[n if n > 0 else 0 for n in nums]`（变换）vs 尾部 if（过滤）

> 基础题，注意与推导式 if 位置的区分（前面是值映射，尾部是过滤）这一细节即可。
""",

    "什么是 PEP 8？举几个常见的代码规范。": """
PEP 8 是 Python 官方**代码风格指南**，统一可读性基线。常见条目：

- **缩进**：4 空格，不用 Tab
- **命名**：变量/函数 `snake_case`，类 `PascalCase`，常量 `UPPER_CASE`，私有约定 `_leading_underscore`
- **行宽**：79/99 字符（现代项目常放宽到 100-120）
- **空格**：运算符两侧、逗号后留空格；括号内侧紧贴
- **导入**：分组排序（标准库 → 第三方 → 本地），一行一个，禁止 `from x import *`
- 比较：`if x is None:` 而非 `== None`
- 函数/类间空 2 行/1 行

### 考察要点
- 不止背条目，能说出"为什么"：可读性与团队协作一致性
- 知道工具落实：ruff/flake8 检查 + black/ruff format 自动格式化 + pre-commit 挂钩

### 追问路线
1. 格式化与 lint 的区别（black 改代码 vs flake8 只报）
2. 与 PEP 484（类型注解）、PEP 257（docstring）的关系——PEP 体系怎么索引
3. 什么时候可以违反 PEP 8？（与既有风格一致优先；stupid consistency 是 hobgoblin）

> 加分项：把 PEP 8 落到"工具链保障"而不是人肉 review，说明工程化经验。
""",

    "如何安装和管理 Python 第三方库？": """
```bash
pip install requests                  # 安装最新
pip install "flask>=2,<3"             # 版本约束
pip install -r requirements.txt       # 按文件装（部署复现）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pkg   # 镜像加速
pip list / pip show requests / pip freeze > requirements.txt
pip uninstall requests
```

### 考察要点
- 全局环境别乱装：**先虚拟环境再安装**（venv/uv/poetry）
- 版本锁定意识：部署用 freeze/lock 的精确版本
- 国内镜像配置（pip config set global.index-url ...）

### 追问路线
1. 装了但 import 不到怎么排查？（装进别的解释器/环境；which python 与 pip 对应关系；`python -m pip` 保对）
2. 依赖冲突怎么处理？（resolver 报错 → 升级/换版本组合，pip-compile 可视化）
3. 私有包/内网源怎么发与装？（devpi/nexus + --extra-index-url）

> 加分项：坚持 `python -m pip` 而非裸 pip——避免 pip 绑错解释器，是真踩过坑的细节。
""",

    "Python 字符串有哪些常用方法？": """
按用途分组：
- **查找判断**：`find/index`、`count`、`startswith/endswith`、`in`
- **变换**：`upper/lower/title/capitalize`、`strip/lstrip/rstrip`、`replace`、`expandtabs`
- **切分连接**：`split/rsplit/splitlines`、`partition`、`join`、`zfill`、`center/ljust/rjust`
- **格式判断**：`isdigit/isalpha/isalnum/isspace/isupper`
- **对齐填充**：`format`、f-string、`%`

### 易错细节
```python
'a,b,,c'.split(',')      # ['a','b','','c'] 空串保留
'a b  c'.split()          # ['a','b','c'] 无参按任意空白且去空
'-'.join(['a','b'])       # 连接用 join 而不是循环 +=
```

### 追问路线
1. strip 的参数语义（删的是字符集合不是子串）：`'xyabcxy'.strip('xy')` → 'abc'
2. split 指定 maxsplit 的行为
3. 正则 re.sub 处理复杂替换；str.maketrans + translate 批量映射

> 考察方式：让候选人现场说"把一串日志按分隔符切成字段再清洗"，看方法组合的熟练度。
""",

    "Python 中如何查看对象的类型和可用属性方法？": """
```python
type(obj)              # 类型
isinstance(obj, T)     # 类型判断（含继承）
dir(obj)               # 属性与方法名列表（含继承的）
vars(obj)              # 实例 __dict__（自身属性）
getattr(obj, 'name', default)   # 动态取属性
hasattr(obj, 'name')   # 是否存在
help(obj.method)       # 文档
obj.__dict__           # 同 vars；类则有 __mro__、__doc__
import inspect
inspect.signature(f)   # 函数签名；inspect.getsource(f) 源码
```

### 考察要点
- 会组合使用：type 看类、dir 找能力、help/signature 看用法
- 动态性意识：getattr/hasattr 是"协议试探"的基础（鸭子类型的工程形态）

### 追问路线
1. dir() 里下划线开头的方法是什么？（魔术方法/私有约定）
2. `__doc__` 与 help 的关系；交互式 ? 与 ??（IPython）
3. 没有源码的 C 扩展对象怎么探？（dir + signature 兜底）

> 加分项：日常调试习惯里会先 dir/inspect 再查文档，说明自驱排障能力强。
""",
}
