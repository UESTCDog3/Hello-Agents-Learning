import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List,Dict

# 加载.env文件中的环境变量
load_dotenv()

# 封装基础LLM调用函数
class HelloAgentsLLM:
    """
    为本书 "Hello Agents" 定制的LLM客户端。
    它用于调用任何兼容OpenAI接口的服务，并默认使用流式响应。
    """
    def __init__(self,model:str = None,apiKey:str = None,baseUrl:str = None,timeout:int = None):  # timeout：防止请求卡死
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))


        if not all([self.model,apiKey,baseUrl]):
            raise ValueError("模型ID、API密钥和服务器地址必须被提供或在.env文件中定义")

        self.client = OpenAI(api_key=apiKey,base_url=baseUrl,timeout=timeout)  # client是啥？ client Initialization：客户端初始化

    def think(self,messages:List[Dict[str,str]],temperature:float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            # 发起对话请求 
            response = self.client.chat.completions.create(   # 这是什么调用格式？  chat.completions.create 调用对话模型标准的方法
                model = self.model,
                messages = messages,
                temperature = temperature,  # temperature：控制输出的随机性（0表示确定、严谨；值越高越具创造性）
                stream = True,
                extra_body={"thinking": {"type": "enabled"}}
            )

            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response: #  因为 response 是数据流，所以需要用 for 循环不断接收模型吐出的“数据碎块（chunk）”。chunk是Python对象（类），并不是字典
                content = chunk.choices[0].delta.content or ""  # 在非流式输出中，我们获取文本用的是 .message.content；但在流式输出中，每次传来的只是增量（delta），即最新生成的那个字或词。都是对象的属性
                # or "": 这是一个容错处理。有时候数据块可能不包含文本内容（比如流的开头或结尾），这能防止程序抛出 NoneType 错误。
                print(content,end="",flush=True) # Python 的 print 函数默认会在每次打印后换行（end="\n"）。将其设置为空字符串 ""，可以确保新的字紧紧贴在刚才的字后面，而不是另起一行。
                # flush=True 会强行清空缓冲区，强制要求系统立刻把刚收到的字打印到屏幕上，从而形成平滑的打字效果。
                collected_content.append(content)
            print()
            return "".join(collected_content) # 空字符拼接，将所有小块拼接成一个完整的字符串

        except Exception as e:
            print(f"❌ 调用大语言模型失败: {e}")
            return None

if __name__ == "__main__":
    try:
        limClient = HelloAgentsLLM()
        exapmpleMessages = [{"role": "system", "content": "You are a good assistant"},
            {"role": "user", "content": "你知道《咒术回战》这部动漫吗？"}
        ]
        print(f"原文:{exapmpleMessages[1]['content']}")
        print("🧠 正在思考...")
        responseText = limClient.think(exapmpleMessages)
        # if responseText:
        #     print("\n💡 思考结果:")
        #     print(responseText)
    except Exception as e:
        print(e)
