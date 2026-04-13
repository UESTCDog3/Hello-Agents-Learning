# Chapter 6：AutoGen 多智能体示例 — 概念笔记

本文围绕 `AutoGen.py` 里的**软件开发团队**示例，说明用到的 API 以及相关的 **Python 异步（async/await）** 概念。可按目录跳读。

---

## 目录

1. [整体串联：这几句代码在干什么](#1-整体串联这几句代码在干什么)
2. [`RoundRobinGroupChat`：轮流发言的团队](#2-roundrobingroupchat轮流发言的团队)
3. [`TextMentionTermination`：什么时候停](#3-textmentiontermination什么时候停)
4. [`run_stream` 与 `Console`：流式跑任务、终端里看过程](#4-run_stream-与-console流式跑任务终端里看过程)
5. [Python：`async` / `await` 与「异步」](#5-pythonasync--await-与异步)
6. [延伸阅读](#6-延伸阅读)

---

## 1. 整体串联：这几句代码在干什么呢

用你这段脚本里的核心逻辑，可以按顺序理解成下面五步：

1. **`async def run_software_development_team()`**  
   定义**异步函数**，因为里面要处理异步消息流（例如流式输出、等待 I/O）。入口处通常用 `asyncio.run(run_software_development_team())` 真正启动它。（参考：[Python — asyncio][1]）

2. **`TextMentionTermination("TERMINATE")`**  
   规定：谁在某条消息里说了 `TERMINATE`，团队就结束。（参考：[AutoGen AgentChat][2]）

3. **`RoundRobinGroupChat(...)`**  
   把多个 agent 组织成**按固定顺序轮流发言**的团队。（参考：[AutoGen 多智能体][3]）

4. **`team_chat.run_stream(task=task)`**  
   启动任务，并把协作过程中的消息**按流**产出，最后会得到 `TaskResult`。（参考：[AutoGen 运行与流式][4]）

5. **`await Console(...)`**  
   消费上面的流，**在终端里实时打印**每条消息，并在结束时把最后的 `TaskResult` 作为返回值赋给 `result`。（参考：[AutoGen UI / Console][5]）

---

## 2. `RoundRobinGroupChat`：轮流发言的团队

`RoundRobinGroupChat` 是 AutoGen 里预置的一种**多智能体团队**：参与者按**轮询 / 轮转**依次发言——第 1 个说完，第 2 个说……到最后一个后再回到第 1 个。

例如：

```python
participants=[
    product_manager,
    engineer,
    code_reviewer,
    user_proxy
]
```

在 `RoundRobinGroupChat` 里，大体就会按这个顺序循环：

1. 产品经理  
2. 工程师  
3. 代码审查员  
4. 用户代理  
5. 再回到产品经理  

底层基类（如 `BaseGroupChat`）的特点是：**参与者共享上下文**，一个 agent 发出的消息会被其他人看到。

角色分工可以很直观地对应为：

- `product_manager`：拆需求、排优先级  
- `engineer`：实现方案与代码  
- `code_reviewer`：审查与改进建议  
- `user_proxy`：代表用户补充输入或收尾  

**适用场景**：流程清晰、发言顺序相对固定的任务。若希望「下一步由最合适的角色说话」，更适合 `SelectorGroupChat` 等更灵活的编排方式。

---

## 3. `TextMentionTermination`：什么时候停

`TextMentionTermination` 是一种**终止条件（termination condition）**。团队在运行过程中会不断检查新消息：若满足条件则发出停止信号，否则继续。

对 `TextMentionTermination` 来说，含义是：**当消息里出现指定文本时，终止对话**。

```python
termination = TextMentionTermination("TERMINATE")
```

即：任意 agent 的消息里一旦出现 `"TERMINATE"`，团队运行就会停止。通常要在系统提示词里约定，例如「任务完成后请输出 `TERMINATE`」。

与 `RoundRobinGroupChat` 组合时：

```python
team_chat = RoundRobinGroupChat(
    ...
    termination_condition=termination,
    max_turns=20,
)
```

相当于两层「刹车」：

- 出现 `TERMINATE` 就停；  
- 同时 **`max_turns=20`** 限制最多轮数，避免无限循环。  

**注意**：对 group chat 而言，终止条件一般在**每个 agent 完成一次响应后**检查，而不是每个 token 检查一次。

---

## 4. `run_stream` 与 `Console`：流式跑任务、终端里看过程

### `team_chat.run_stream(task=task)`

`run_stream()` 会启动团队执行任务，并返回一个**异步生成器**。运行过程中会**一边协作、一边产出消息**；流式输出的最后一个对象通常是 **`TaskResult`**。

也就是说，不是「全部跑完才一次性返回」，而是：

- 先产出一条消息，再产出下一条……  
- 最后产出完整结果 `TaskResult`。  

适合在终端里**实时观察**多 agent 协作。

### `await Console(...)`

`Console(...)` 用来**消费** `run_stream()` 产生的流，并按适合终端的格式打印；若输入来自 `run_stream()`，其返回值一般为最后的 **`TaskResult`**。

因此：

```python
result = await Console(team_chat.run_stream(task=task))
```

含义是：启动任务 → 实时打印流式消息 → 结束后把最终结果保存到 `result`。

这里必须 **`await`**，因为 `Console(...)` 本身是异步的，要一直读到流结束才能完成。

---

## 5. Python：`async` / `await` 与「异步」

### 5.1 一句话区分

- **`async`**：写在 `def` 前，表示**定义异步函数**（协程函数）。调用时**不会立刻跑完函数体**，而是先得到一个 **coroutine 对象**；真正执行要靠 **`await`** 或 **`asyncio.run(...)`** 等驱动。  
- **`await`**：只能写在 **`async def`** 里面，表示**在这里等待某个可等待对象完成**，再带着结果继续往下执行。

可以记成：

- **`async`**：声明「这是异步函数」  
- **`await`**：声明「在这里等异步结果」  

在 AutoGen 示例里：

```python
result = await Console(team_chat.run_stream(task=task))
```

`run_software_development_team` 是 `async def`，内部可以 `await Console(...)`：即**等控制台把整个流式输出处理完**，再把最终结果赋给 `result`。

### 5.2 `async` 具体做什么

```python
async def foo():
    return 123

x = foo()
print(x)   # <coroutine object foo at ...>，不是 123
```

普通函数调用后会从上到下立刻执行完；异步函数调用后先返回协程对象，需要由事件循环配合 `await` / `asyncio.run` 来驱动执行。

### 5.3 `await` 具体做什么

`await` 表示：**等这个异步步骤结束，再往下走**。等待期间，事件循环可以去调度其他协程，从而**减少「干等 I/O」时的浪费**。

```python
import asyncio

async def foo():
    await asyncio.sleep(1)
    return 123
```

`await asyncio.sleep(1)` 不是「占死线程傻等」，而是**先让出执行权**，时间到了再恢复。

### 5.4 两条常用规则

1. **`await` 只能出现在 `async def` 里**（顶层脚本里不能随意 `await`，除非在异步上下文中）。  
2. **只能 `await`「可等待」对象**（协程、`asyncio.sleep`、部分库返回的 Task 等），不能 `await` 普通整数等。

### 5.5 最小完整例子

```python
import asyncio

async def make_tea():
    print("开始烧水")
    await asyncio.sleep(2)
    print("水开了")
    return "茶泡好了"

async def main():
    result = await make_tea()
    print(result)

asyncio.run(main())
```

### 5.6 怎么理解「异步」这个词

生活化理解：

**发出一个需要等待的任务后，不必一直堵在那儿；可以先做别的事，等就绪了再回来接着处理。**

- **同步**：一件事没做完，逻辑上就像一直卡在窗口前等面好。  
- **异步**：点完单可以先找座位、回消息；面好了再回来取——**等待那段时间没有被整条执行流程白白占死**。  

在程序里，网络请求、读文件、等数据库、等大模型回复，都常是「要等」的操作。异步的目的**不一定是让单次请求本身更快**，而是：**在等待发生时，尽量别让程序整段卡住，有机会去推进别的工作**。

烧水仍然要 5 分钟，异步不会把它变成 1 分钟；但这 5 分钟里你可以同时准备茶杯、茶叶——**等待时间更不容易被浪费**。  
本质一句话：**面对需要等待的任务时，尽量不阻塞整条协作流程，让运行时有空间去处理其他可推进的事。**

---

## 6. 延伸阅读

文中引用可对照下面链接（以官方 / 主仓库为准，版本迭代时请以最新文档为准）：

[1]: https://docs.python.org/3/library/asyncio.html  
[2]: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html  
[3]: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html  
[4]: https://microsoft.github.io/autogen/stable/reference/python/autogen_agentchat.teams.html  
[5]: https://microsoft.github.io/autogen/stable/reference/python/autogen_agentchat.ui.html  

（若你本地包版本与文档版本不一致，以当前安装的 `autogen-agentchat` 包内 docstring / 源码为准。）