# -*- coding: utf-8 -*-
"""题库数据：Python 方向 40 题（简单16 / 中等16 / 困难8），均为业内高频真题。
字段: (题干, 参考答案, 采分点, 讲解, 类型, 难度, 所属部分)
"""

PYTHON = [
    # ================= 简单 16 =================
    ("Python 中列表（list）和元组（tuple）有什么区别？",
     "列表可变，支持增删改；元组不可变，定义后不能修改。元组因不可变可哈希，能作为字典的键和集合元素，列表不行。元组内存占用更小、创建更快，适合存固定结构数据（如坐标）；列表适合动态集合。",
     "答出列表可变、元组不可变：2分\n答出元组可作字典键（可哈希）：1.5分\n答出使用场景或内存差异：1.5分",
     "可追问：元组里装了列表还能当字典键吗？", "Python", "简单", "基础"),

    ("Python 中 is 和 == 有什么区别？",
     "== 比较两个对象的值是否相等（调用 __eq__）；is 比较两个对象是否是同一个对象（内存身份，即 id 是否相同）。小整数缓存和字符串驻留可能导致 is 为 True 的巧合，但不应依赖。判断 None 必须用 is None。",
     "答出 == 比较值：2分\n答出 is 比较对象身份（内存地址/id）：2分\n提到 is None 的惯例或小整数缓存：1分",
     "", "Python", "简单", "基础"),

    ("浅拷贝和深拷贝的区别是什么？",
     "赋值（b = a）只复制引用，两个变量指向同一对象。浅拷贝（copy.copy 或 list[:]）创建新对象，但内部子元素仍是引用，嵌套对象修改会互相影响。深拷贝（copy.deepcopy）递归复制所有层级，完全独立。",
     "答出赋值只复制引用：1.5分\n答出浅拷贝只复制第一层、嵌套元素共享：2分\n答出深拷贝递归复制全部层级：1.5分",
     "可追问：copy.deepcopy 对循环引用怎么处理（备忘录机制）。", "Python", "简单", "基础"),

    ("Python 有哪些可变类型和不可变类型？函数传参是传值还是传引用？",
     "不可变：int、float、str、tuple、frozenset、bytes；可变：list、dict、set、bytearray 及大多数自定义对象。Python 传参是“传对象引用”：对不可变对象重新赋值不影响外部；对可变对象原地修改（如 append）会影响外部。",
     "各答出至少三类可变/不可变类型：2分\n答出传的是对象引用：2分\n能说明可变对象原地修改影响外部、不可变对象赋值生成新对象：1分",
     "", "Python", "简单", "基础"),

    ("*args 和 **kwargs 是什么？",
     "*args 把多余的位置参数收集为元组；**kwargs 把多余的关键字参数收集为字典。调用时 * 和 ** 还可以解包序列/字典展开传参。参数顺序：普通参数、*args、关键字参数、**kwargs。",
     "答出 *args 收集位置参数为元组：2分\n答出 **kwargs 收集关键字参数为字典：2分\n提到解包用法或参数顺序：1分",
     "", "Python", "简单", "基础"),

    ("sorted() 和 list.sort() 有什么区别？",
     "list.sort() 原地排序，修改原列表，返回 None；sorted() 返回新列表，不改动原对象，且能接受任意可迭代对象（元组、字典、生成器等）。两者都支持 key 和 reverse 参数。",
     "答出 sort 原地修改、返回 None：2分\n答出 sorted 返回新列表且适用任意可迭代对象：2分\n提到 key/reverse 参数：1分",
     "经典陷阱：a = a.sort() 会把 a 变成 None。", "Python", "简单", "基础"),

    ("字典（dict）和集合（set）有什么区别？分别什么场景使用？",
     "底层都是哈希表，元素都必须可哈希，查找都是平均 O(1)。dict 是 key→value 映射，适合需要按 key 取值的场景（配置、计数、缓存）；set 只存不重复的 key，适合去重、成员判断、交并差运算。",
     "答出 dict 存键值对、set 存不重复元素：2分\n答出两者都基于哈希、查找快：1.5分\n答出去重/交并差或映射场景：1.5分",
     "", "Python", "简单", "基础"),

    ("如何去除列表中的重复元素？如何保持原顺序？",
     "set(lst) 去重但不保序。保持顺序用 list(dict.fromkeys(lst))（利用字典键有序且唯一）；或写循环 + 已见集合判断。对不可哈希元素（如嵌套列表）需手动遍历比较。",
     "答出 set 去重：2分\n答出 dict.fromkeys 保序去重（或循环+seen 集合）：2.5分\n提到不可哈希元素处理：0.5分",
     "", "Python", "简单", "基础"),

    ("Python 格式化字符串有哪几种方式？",
     "老式 % 格式化（'%s' % x）；str.format()（'{}'.format(x)）；f-string（f'{x}'，Python 3.6+，性能最好、可写表达式 f'{a+b}'）；string.Template（少用）。日常推荐 f-string。",
     "答出 % 与 format：2分\n答出 f-string 及其优势（简洁/性能）：2分\n答出 f-string 内可放表达式或格式控制符：1分",
     "", "Python", "简单", "基础"),

    ("什么是切片？步长为负是什么效果？",
     "切片语法 seq[start:stop:step]，区间左闭右开，省略时默认 start=0、stop=末尾、step=1。步长为负表示反向取，如 s[::-1] 反转字符串/列表。切片返回新对象（浅拷贝）。",
     "答出切片语法与左闭右开：2分\n答出 s[::-1] 反转或步长为负反向：2分\n答出切片产生新对象（浅拷贝）：1分",
     "", "Python", "简单", "基础"),

    ("Python 异常处理中 try/except/else/finally 的执行顺序是怎样的？",
     "try 中无异常：执行完 try 后执行 else，再执行 finally；try 中有异常：跳到匹配的 except 执行，不执行 else，最后 finally 必执行。finally 常用于释放资源，即使 try 里有 return 也会先执行 finally。",
     "答出异常时 except 捕获、else 不执行：2分\n答出 finally 无论如何都执行：2分\n答出无异常时走 else 或 finally 与 return 的关系：1分",
     "", "Python", "简单", "基础"),

    ("为什么读写文件推荐用 with open？",
     "with 是上下文管理器，代码块结束（含异常）时自动调用 f.close() 释放文件句柄，避免忘记关闭导致资源泄漏或数据未刷盘。等价于 try/finally 中手动 close。",
     "答出自动关闭文件：2分\n答出异常情况下也会关闭：2分\n提到上下文管理器或资源泄漏：1分",
     "", "Python", "简单", "基础"),

    ("集合（set）支持哪些运算？举个例子。",
     "交集 & 或 a.intersection(b)；并集 |；差集 -；对称差 ^（不同时在两边）。均支持原地版本 &=、|= 等。还可判断子集/超集：<=、>=。",
     "交集并集差集各 1 分（共 3 分）\n答出对称差 ^ 或子集判断：2分",
     "", "Python", "简单", "基础"),

    ("如何判断一个对象是可迭代的？迭代器和可迭代对象有什么区别？",
     "isinstance(obj, collections.abc.Iterable) 或尝试 iter(obj) 不报错。可迭代对象实现了 __iter__；迭代器额外实现 __next__，是惰性一次性的，耗尽后抛 StopIteration。for 循环本质是先 iter() 再不断 next()。",
     "答出 iter()/isinstance 判断方法：1.5分\n答出可迭代实现 __iter__、迭代器多一个 __next__：2分\n答出 for 循环原理或 StopIteration：1.5分",
     "", "Python", "简单", "基础"),

    ("判断 x 是否为 None 为什么推荐用 is None 而不是 == None？",
     "None 是全局单例，is 直接比较对象身份，速度最快且语义明确。== 会调用 x 的 __eq__，若对象重载了 __eq__（如 numpy 数组、pandas 对象）可能返回数组导致布尔上下文报错。PEP 8 也规定与 None 比较用 is/is not。",
     "答出 None 是单例、is 比较身份：2分\n答出 == 可能被 __eq__ 重载干扰（如返回数组报错）：2分\n提到 PEP 8 规范：1分",
     "", "Python", "简单", "基础"),

    ("Python 3 的 range(10) 返回什么？和列表有什么区别？",
     "返回 range 对象，是惰性序列，按需计算，内存 O(1)，支持 in 判断、索引、len，不可变。列表是立即展开的容器，内存 O(n)。大范围循环应使用 range。",
     "答出 range 是惰性/按需生成的对象：2分\n答出内存差异（O(1) vs O(n)）：2分\n答出支持 in/索引等序列操作：1分",
     "", "Python", "简单", "基础"),

    # ================= 中等 16 =================
    ("请解释 Python 的 GIL 及其对多线程的影响。",
     "GIL（全局解释器锁）是 CPython 的互斥锁，保证同一时刻只有一个线程执行 Python 字节码。因此 CPU 密集任务多线程无法利用多核，应用 multiprocessing；IO 密集任务在等待时释放 GIL，多线程/协程仍然有效。",
     "答出 GIL 使同一时刻仅一个线程执行字节码：2分\n答出 CPU 密集应使用多进程：1.5分\n答出 IO 密集多线程/协程仍有效（等待时释放 GIL）：1.5分",
     "可追问：Python 3.13 的 free-threading 实验特性。", "Python", "中等", "基础"),

    ("什么是装饰器？请实现一个打印函数执行耗时的装饰器。",
     "装饰器是接收函数并返回新函数的高阶函数，@ 语法是语法糖。计时装饰器：import time, functools；def timer(func): @functools.wraps(func) def wrapper(*args, **kwargs): t0=time.perf_counter(); r=func(*args,**kwargs); print(func.__name__, time.perf_counter()-t0); return r; return wrapper。",
     "答出装饰器是接收函数返回新函数的高阶函数：2分\n写出闭包 wrapper 并调用原函数：1.5分\n使用 functools.wraps 保留元信息或计时用 perf_counter：1.5分",
     "可追问带参数装饰器（三层嵌套）。", "Python", "中等", "基础"),

    ("生成器是什么？yield 的执行原理？",
     "生成器是含 yield 的函数调用后返回的惰性迭代器。执行到 yield 暂停并返回值，保存局部状态与执行位置；next() 时从暂停处恢复。适合流式处理大文件、无限序列，内存 O(1)。send() 可向生成器内传值。",
     "答出惰性求值/按需生成：2分\n答出 yield 暂停并保存状态、next 恢复执行：2分\n答出大文件/无限序列场景或 send：1分",
     "", "Python", "中等", "基础"),

    ("什么是闭包？有哪些应用场景？",
     "闭包是内层函数引用了外层函数作用域的变量，且外层函数返回该内层函数，被引用的变量随闭包存活。应用：装饰器、函数工厂（生成不同配置的函数）、延迟计算、回调保存上下文。查看 __closure__ 可见引用的单元格。",
     "答出内层函数引用外层变量并被携带：2分\n答出变量生命周期延长（脱离外层函数仍存活）：1.5分\n答出装饰器/函数工厂等场景：1.5分",
     "", "Python", "中等", "基础"),

    ("with 语句的原理是什么？如何自定义上下文管理器？",
     "with 调用对象的 __enter__（返回值赋给 as 变量）执行代码块，结束或异常时调用 __exit__(exc_type, exc_val, tb)；__exit__ 返回 True 可吞掉异常。自定义：实现这两个方法的类，或用 @contextlib.contextmanager 装饰生成器函数（yield 前后分别是进入和清理）。",
     "答出 __enter__/__exit__ 协议：2分\n答出异常时 __exit__ 仍被调用（可吞异常）：1.5分\n答出 contextlib.contextmanager 生成器写法：1.5分",
     "", "Python", "中等", "基础"),

    ("可变默认参数有什么陷阱？如何避免？",
     "def f(x, lst=[]) 中默认值在函数定义时只创建一次，所有调用共享同一个列表，导致上次调用的影响残留（如多次 append 累积）。避免：默认值用 None，函数体内 lst = lst if lst is not None else []。",
     "答出默认值只求值一次、跨调用共享：2.5分\n答出用 None 作哨兵再在函数内新建：2分\n能举出累积现象例子：0.5分",
     "可追问为什么 lambda 默认参数绑定循环变量（闭包晚绑定）。", "Python", "中等", "基础"),

    ("Python 的垃圾回收机制是怎样的？",
     "以引用计数为主：对象引用数为 0 立即回收；缺点是无法处理循环引用，因此辅以标记-清除定期检测不可达循环；再用分代回收（0/1/2 三代，越老扫描越少）降低开销。gc 模块可控制和调试。",
     "答出引用计数为主、归零即回收：2分\n答出循环引用问题与标记-清除：1.5分\n答出分代回收降低开销：1.5分",
     "", "Python", "中等", "基础"),

    ("Python 中如何选择多线程、多进程、协程？",
     "CPU 密集：multiprocessing 多进程利用多核（绕过 GIL），进程间通信用 Queue/Pipe。IO 密集高并发：asyncio 协程单线程事件循环，切换开销极小，适合网络请求、爬虫；IO 密集但任务不复杂：threading 多线程，代码简单，线程数不宜过多。混合场景可用进程池+协程。",
     "答出 CPU 密集用多进程：2分\n答出 IO 密集用协程/多线程并说明原因：2分\n答出协程与线程的适用差异或混合方案：1分",
     "", "Python", "中等", "基础"),

    ("async/await 和 asyncio 事件循环的工作原理？",
     "async def 定义协程，调用返回协程对象不执行；await 把控制权交回事件循环，让其他协程运行。事件循环基于 IO 多路复用（select/epoll），IO 就绪后恢复对应协程。asyncio.gather 并发多个任务，Task 是被事件循环调度的协程封装。协程是协作式调度，单个协程阻塞（如 time.sleep、同步请求）会卡住整个循环。",
     "答出 await 让出控制权、事件循环调度：2分\n答出事件循环基于 epoll/select 等 IO 多路复用：1.5分\n答出同步阻塞调用会卡死循环或 gather/Task 用法：1.5分",
     "", "Python", "中等", "基础"),

    ("Python 变量作用域的 LEGB 规则是什么？global 和 nonlocal 的作用？",
     "查找顺序 Local（函数内）→ Enclosing（外层函数）→ Global（模块）→ Builtin（内置）。函数内读取外部变量可以，但赋值会创建局部变量；要在函数内修改全局变量用 global x；修改闭包外层函数变量用 nonlocal x。",
     "答出 LEGB 四层含义：2分\n答出赋值默认创建局部变量：1.5分\n答出 global 与 nonlocal 各自用途：1.5分",
     "", "Python", "中等", "基础"),

    ("__new__ 和 __init__ 的区别？",
     "__new__ 是静态方法，负责创建并返回实例（object.__new__(cls)），先于 __init__ 调用；__init__ 在实例创建后初始化属性，返回值必须是 None。__new__ 常用于单例模式、继承不可变类型（str/tuple）定制值。",
     "答出 __new__ 创建实例、__init__ 初始化：2分\n答出 __new__ 先执行且是静态方法：1.5分\n答出单例或不可变类型定制场景：1.5分",
     "", "Python", "中等", "基础"),

    ("什么是鸭子类型？和传统继承多态有什么不同？",
     "鸭子类型：“走路像鸭子、叫声像鸭子，那就是鸭子”——只关心对象是否有需要的方法/行为，不关心其继承体系。如任何实现 __iter__ 的对象都能被 for 遍历。与 Java 等基于接口/继承的多态相比更灵活，但缺少编译期检查，可用 typing.Protocol 或 abc 抽象基类补充约束。",
     "答出关注行为而非类型/继承：2分\n答出不要求显式接口即可多态：1.5分\n提到 Protocol/ABC 或 isinstance 检查习惯：1.5分",
     "", "Python", "中等", "基础"),

    ("functools.lru_cache 的作用和原理？什么场景使用？",
     "给函数加最近最少使用缓存：以参数为键缓存返回值，命中直接返回；超过 maxsize 按 LRU 淘汰。适合纯函数（参数相同结果相同）的重复计算，如递归斐波那契、读配置、固定查询。注意参数必须可哈希，且有副作用的函数不适合。",
     "答出按参数缓存结果、命中免计算：2分\n答出 LRU 淘汰策略：1.5分\n答出适用纯函数场景或副作用警告：1.5分",
     "", "Python", "中等", "基础"),

    ("str 和 bytes 的区别？encode/decode 是做什么的？",
     "str 是 Unicode 文本序列；bytes 是原始字节序列。文本要落盘、传输必须编码：s.encode('utf-8') 得到 bytes；bytes.decode('utf-8') 还原为 str。读写文件建议指定 encoding='utf-8'。乱码本质是编解码用了不同字符集。",
     "答出 str 是 Unicode 文本、bytes 是字节：2分\n答出 encode 文本转字节、decode 字节转文本：2分\n提到指定编码避免乱码：1分",
     "", "Python", "中等", "基础"),

    ("Python 如何做类型注解？它影响运行时吗？",
     "语法：def f(x: int, name: str = '') -> bool，变量 x: list[int] = []。typing 提供 Optional/List/Dict/Union 等。注解默认不影响运行时，仅静态检查工具（mypy、IDE）使用，第三方库（pydantic）可利用注解在运行时校验。提升可读性与维护性，大型项目推荐。",
     "答出注解语法示例：1.5分\n答出运行时不强制、靠 mypy/IDE 静态检查：2分\n提到 pydantic 运行时校验等用途：1.5分",
     "", "Python", "中等", "基础"),

    ("静态方法、类方法、实例方法有什么区别？",
     "实例方法第一个参数是 self，可访问实例属性；类方法 @classmethod 第一个参数是 cls，常用于替代构造器（如 dict.fromkeys）；静态方法 @staticmethod 无隐式参数，就是放在类命名空间里的普通函数。继承时类方法拿到的 cls 是实际子类，便于多态构造。",
     "答出 self/cls/无参数三种形式：2分\n答出类方法常用于替代构造器：1.5分\n答出 cls 在继承时的多态价值或静态方法定位：1.5分",
     "", "Python", "中等", "基础"),

    ("什么是猴子补丁（monkey patching）？有什么风险？",
     "运行时动态替换模块、类或函数的属性，如替换 requests.get 做测试打桩、给第三方库修 bug。风险：隐式改变全局行为、影响所有使用方、库升级后失效、难排查；应限定作用范围（如仅测试内 fixture）并打标记。",
     "答出运行时动态替换属性/方法：2分\n答出测试 mock 等常见用途：1.5分\n答出全局影响、版本升级失效等风险：1.5分",
     "", "Python", "中等", "基础"),

    # ================= 困难 8 =================
    ("什么是元类（metaclass）？有哪些实际应用？",
     "元类是类的类：class 语句创建类时实际调用 type(name, bases, dict)，type 就是默认元类。继承 metaclass=MyMeta 可拦截类的创建，改写属性、校验、注册。应用：ORM（Django Model 通过元类收集字段生成表结构）、抽象基类 abc.ABCMeta、接口校验、单例。type 动态建类：MyClass = type('MyClass', (Base,), {'x': 1})。",
     "答出元类是类的类、type 是默认元类：2分\n答出拦截类创建过程（__new__/__init__）：1.5分\n答出 ORM/ABCMeta/单例等实际应用或 type 三参建类：1.5分",
     "口头追问“元类 vs __init_subclass__”：后者更轻量，多数场景够用。", "Python", "困难", "应用"),

    ("描述符协议的原理是什么？property、classmethod 是怎么实现的？",
     "描述符是定义了 __get__/__set__/__delete__ 的类。数据描述符（含 __set__）优先级高于实例 __dict__，非数据描述符低于实例字典——这是属性查找顺序的核心。property 就是数据描述符：把 fget/fset 包装成 __get__/__set__；classmethod/staticmethod 是非数据描述符改写 __get__ 绑定行为。ORM 字段、__slots__、缓存属性都基于描述符。",
     "答出 __get__/__set__ 协议与两类描述符：2分\n答出数据/非数据描述符与实例字典的优先级差异：1.5分\n答出 property/ORM 字段等实现原理：1.5分",
     "", "Python", "困难", "应用"),

    ("实现一个带参数的装饰器（如重试 retry(3)），要注意什么？",
     "三层结构：外层接收参数，中层接收函数，内层执行逻辑并 return 结果；每层都要 functools.wraps。例如 def retry(times): def deco(func): @wraps(func) def wrapper(*a, **kw): for i in range(times): try: return func(*a, **kw) except Exception: if i == times-1: raise; return wrapper; return deco。注意点：@retry(3) 带括号；参数校验；装饰类可用类实现 __call__。",
     "答出三层嵌套结构（参数→函数→包装）：2分\n写出循环重试并最终抛出异常：1.5分\n答出 functools.wraps 或 @retry(3) 必须带括号：1.5分",
     "", "Python", "困难", "应用"),

    ("不使用 functools，手写一个 LRU 缓存类，思路是什么？",
     "用哈希表 + 双向链表：链表节点存 key/value，哈希表 key→节点实现 O(1) 定位。get 命中则把节点移到头部；put 已存在则更新并移头部，否则头插新节点，超容量删除尾节点（最久未使用）。借助 OrderedDict 可简化：move_to_end + popitem(last=False)。",
     "答出哈希表+双向链表结构：2分\n答出命中移头部、淘汰尾部：1.5分\n答出 OrderedDict 实现或复杂度 O(1)：1.5分",
     "", "Python", "困难", "应用"),

    ("Python 多进程间有哪些通信方式？各适合什么场景？",
     "Queue：进程安全队列，最常用，适合生产者消费者；Pipe：双端管道性能高，适合两个进程一对一；共享内存（Value/Array、multiprocessing.shared_memory）：大数据量低拷贝开销；Manager：代理复杂结构（dict/list）跨进程共享，但性能低；进程池回调/imap 传递结果。注意 pickle 序列化限制与 Windows spawn 启动方式（须 if __name__ == '__main__'）。",
     "答出 Queue 与 Pipe 两种及以上方式：2分\n答出共享内存低拷贝或 Manager 代理结构：1.5分\n答出 pickle 限制或 spawn/入口保护：1.5分",
     "", "Python", "困难", "应用"),

    ("CPython 的内存管理为什么要用对象池/内存池（pymalloc）？",
     "小对象（≤512 字节）创建销毁频繁，直接走系统 malloc 开销大。pymalloc 用 arena→pool→block 三级结构管理小块内存，释放后归还池子复用，减少碎片和系统调用。此外小整数（-5~256）与短字符串有驻留缓存，避免重复分配。这对高频创建 dict/tuple 的程序性能影响显著。",
     "答出小对象频繁分配导致 malloc 开销大：2分\n答出 arena/pool/block 分级池化复用：2分\n答出小整数/字符串驻留：1分",
     "", "Python", "困难", "应用"),

    ("Python 性能优化的常见手段有哪些？如何定位瓶颈？",
     "定位：cProfile/profile 统计函数耗时，line_profiler 按行分析，py-spy 采样线上进程，timeit 微基准。优化：算法与数据结构优先（dict/set 查找、减少 O(n²)）；用生成器与惰性计算省内存；内置函数/列表推导比手写循环快（C 实现）；局部变量与缓存属性查找；__slots__ 减少实例内存；numpy/pandas 向量化数值计算；CPU 热点改 C 扩展/Cython；IO 并发化（asyncio/线程池）。原则：先测量再优化。",
     "答出 cProfile/py-spy 等定位手段：1.5分\n答出算法数据结构优先或向量化：1.5分\n答出生成器/内置函数/__slots__ 等三点以上优化：2分",
     "", "Python", "困难", "应用"),

    ("asyncio 中怎么执行阻塞的同步代码（如 requests、time.sleep）而不卡死事件循环？",
     "loop.run_in_executor(None, func, args) 把同步函数丢进线程池；Python 3.9+ 用 await asyncio.to_thread(func)。CPU 密集用 ProcessPoolExecutor。批量阻塞任务可用 ThreadPoolExecutor + asyncio.gather 配合。绝对不要在协程里直接调用阻塞调用；time.sleep 换 asyncio.sleep，requests 换 aiohttp/httpx。",
     "答出 run_in_executor/asyncio.to_thread 放线程池：2分\n答出 CPU 密集用进程池：1.5分\n答出换 asyncio.sleep/aiohttp 等异步等价物：1.5分",
     "", "Python", "困难", "应用"),
]
