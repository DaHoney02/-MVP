

"""
Tool calling:
流程：用户问题-》模型选择工具-》python执行工具-》将工具结果交给模型-》最终回答
"""
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app.core.config import settings

# 1.定义工具
@tool
def multiply(a:int,b:int)->int:
    """计算两个整数的乘积"""
    return a*b

@tool
def add(a:int,b:int)->int:
    """计算两个整数的和"""
    return  a+b

@tool
def divide(a:float,b:float)-> float:
    """计算两个数相除，适用于除法运算"""
    if b==0:
        raise ValueError("除法不能为0")

    result=a / b
    print(f"运行：{a} / {b} = {result}")
    return result


def main():
    #2.初始化聊天模型
    model=ChatOpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        model=settings.MODEL_NAME,
        temperature=0
    )

    #3.形成工具列表
    tools=[multiply,add,divide]
    model_with_tools=model.bind_tools(tools,tool_choice="required")  #将工具列表提供给模型

    #4.组织工具注册表   【字典推导式】遍历tools列表，把每个工具的名称作为字典的键，把工具对象作为值
    tool_registry={
        tool.name: tool
        for tool in tools
    }

    question="计算123除以56？,并说明计算结果"
    messages=[
        HumanMessage(content=question)
    ]

    #5.第一次调用模型：决定是否需要工具
    print("准备发起第一次模型请求")
    ai_message=model_with_tools.invoke(messages)
    print("模型请求工具:",ai_message.tool_calls)

    #保存模型返回的消息，其中包含tool_calls
    messages.append(ai_message)

    #6.若模型需要工具调用请求，python执行
    if ai_message.tool_calls:
        for tool_call in ai_message.tool_calls:
            tool_name=tool_call["name"]
            tool_args=tool_call["args"]
            tool_call_id=tool_call["id"]
            print(f"模型选择工具：{tool_name}")
            print(f"工具参数：{tool_args}")

            #根据名称找到工具，并使用模型提供的参数调用它
            selected_tool=tool_registry.get(tool_name)

            if selected_tool is None:
                raise ValueError(f"未知工具：{tool_name}")

            result=selected_tool.invoke(tool_args)
            print(f"工具执行结果：{result}")

            #将工具结果放回消息列表，并关联原本的工具调用ID
            messages.append(
                ToolMessage(  #创建一条代表工具执行结果的消息
                    content=str(result),
                    tool_call_id=tool_call_id
            ))

        #7.第二次调用模型，让模型结合工具组织自然语言回答
        final_message=model_with_tools.invoke(messages)
        print("\n=====最终回答======")
        print(final_message.content)
    else:
        print("\n模型没有请求调用工具")
        print(ai_message.content)

if __name__=="__main__":
    main()

