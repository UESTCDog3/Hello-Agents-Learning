from serpapi import SerpApiClient
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List,Dict,Any

# 加载.env文件中的环境变量
load_dotenv()

def search(query:str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "❌ 未设置 SerpApi API 密钥"
        params = {
            "engine":"google",
            'q' : query,
            'api_key' : api_key,
            'gl': 'cn', # 国家代码
            'hl' :'zh-cn' # 语言代码
        }
        client = SerpApiClient (params)
        results = client.get_dict()
        
        # 智能解析:优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title','')}\n{res.get('snippet','')}"
                for i,res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        return "❌ 未找到相关信息"
    except Exception as e:
        return f"搜索时发生错误：{e}"

class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。
    """
    def __init__(self):
        self.tools : Dict[str,Dict[str,Any]] = {}
    
    def register_tool(self,name:str,description:str,func:callable):
        """
        向工具箱中注册一个新工具。
        """
        if name in self.tools:
            print(f"⚠️ 工具 '{name}' 已存在，将覆盖旧工具。")
        self.tools[name] = {"description":description,"func":func}
        print(f"✅ 工具 '{name}' 已注册成功。")

    def getTool(self,name:str) -> callable: # callable：可执行对象
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name,{}).get("func") # get(name,{}):如果name在tools中，则返回name的值，否则返回空字典 用.get是一种防御性编程

    def getAvailableTools(self) -> str:
        """
        获取所有可用的工具列表。
        """
        return "\n".join([f"- {name}: {info['description']}"
                          for name,info in self.tools.items() # item():返回字典的键值对
        ])


if __name__ == "__main__":
    # 初始化工具执行器
    ToolExecutor = ToolExecutor()

    # 注册实战搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    ToolExecutor.register_tool("Search",search_description,search)

    # 打印可用的工具
    print("\n可用的工具:")
    print(ToolExecutor.getAvailableTools())

    # 智能体的Action调用，
    print("\n--- 执行 Action: Search['Iphone手机的最新型号是什么'] ---")
    tool_name = "Search"
    tool_input = "Iphone手机的最新型号是什么"
    
    tool_function = ToolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("---观察（Observation）---")
        print(observation)
    else:
        print(f"错误：未找到名为'{tool_name}'的工具")