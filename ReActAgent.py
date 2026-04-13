from search import ToolExecutor,search
from HelloAgentsLLM import HelloAgentsLLM
import re

# ReAct 提示词模板
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}[{{tool_input}}]`:调用一个可用工具。
- `Finish[最终答案]`:当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action:字段后使用 Finish[最终答案] 来输出最终答案。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""
"""
这个模板定义了智能体与LLM之间交互的规范：

- 角色定义： “你是一个有能力调用外部工具的智能助手”，设定了LLM的角色。
- 工具清单 (`{tools}`)</strong>： 告知LLM它有哪些可用的“手脚”。
- 格式规约 (`Thought`/`Action`)： 这是最重要的部分，它强制LLM的输出具有结构性，使我们能通过代码精确解析其意图。
- 动态上下文 (`{question}`/`{history}`)： 将用户的原始问题和不断累积的交互历史注入，让LLM基于完整的上下文进行决策。
"""

class ReActAgent:
    def __init__(self,llm_client:HelloAgentsLLM,tool_executor:ToolExecutor,max_steps:int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self,question:str) -> str:
        """
        运行ReAct智能体来回答一个问题。
        """
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"---No.{current_step} Step ---")

            # 格式化提示词
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools = tools_desc,
                question = question,
                history = history_str
            )

            # 调用LLM进行思考
            messages = [{"role":"user","content":prompt}]
            response_txt = self.llm_client.think(messages=messages)

            if not response_txt:
                print("❌ 调用LLM失败，无法继续执行")
                break

            thought,action = self._parse_output(response_txt)

            if thought:
                print(f"💡 思考: {thought}")
            
            if not action:
                print("❌ 未找到Action，无法继续执行")
                break

            if action.strip().startswith("Finish"):
                # Finish 与 [ 之间常有空格/换行；re.match 要求紧贴 [，否则会匹配失败
                m = re.search(r"Finish\s*\[(.*)\]", action.strip(), re.DOTALL)
                if not m:
                    print("❌ 无法解析 Finish[...]，请检查模型输出是否为 Finish[答案] 或 Finish [答案]")
                    print(f"原始 Action 片段: {action[:500]!r}...")
                    break
                final_answer = m.group(1).strip()
                print(f"🎯 最终答案: {final_answer}")
                return final_answer
            
            tool_name,tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                continue

            print(f"🔍 执行工具: {tool_name}，输入: {tool_input}")

            tool_function = self.tool_executor.getTool(tool_name)
            if not tool_function:
                observation = "❌ 未找到名为'{tool_name}'的工具"
            else:
                observation = tool_function(tool_input) # 调用真实工具
            print(f"👀 观察: {observation}")
            self.history.append(f"Action:{action}")
            self.history.append(f"Observation:{observation}")
        
        # loop over
        print("已达到最大步数，流程终止")
        return None

    def _parse_output(self,text:str):
        """解析LLM的输出，提取Thought和Action。
        """
        # Thought: 匹配到Action：或文本文尾
        thought_match = re.search(r"Thought:\s*(.*?)(?:Action:|$)",text,re.DOTALL)
        # Action: 匹配到文本文尾
        action_match = re.search(r"Action:\s*(.*?)$",text,re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought,action

    def _parse_action(self,action_txt:str):
        """解析Action字符串，提取工具名称和输入。
        """
        match = re.match(r"(\w+)\[(.*)\]",action_txt,re.DOTALL)
        if match:
            return match.group(1),match.group(2)
        return None,None

if __name__ == '__main__':
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor() # 初始化工具箱
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。" # 查询工具描述
    tool_executor.register_tool("Search", search_desc, search) # 注册一个查询工具
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "Iphone手机的最新型号是什么？它与安卓手机相比的优势在哪里？"
    agent.run(question)
