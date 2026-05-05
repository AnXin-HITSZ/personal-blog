import re
from typing import Optional, List, Union, Dict, Any, Tuple
from collections.abc import Iterator

from app.core.agent import Agent
from app.core.llm import AgentsLLM
from app.tools.registry import ToolRegistry


class ReActAgent(Agent):
    """
    推理与行动结合的智能体
    """

    def __init__(
            self,
            name: str,
            llm: AgentsLLM,
            tool_registry: ToolRegistry,
            max_steps: int,
            memory_context: List[Tuple[float, Dict[str, str]]],
            user_id: Optional[int] = None,
            plan_manager=None,
    ):
        super().__init__(name, llm, tool_registry)
        self.input_text = None
        self.max_steps = max_steps
        self.current_react_history: List[str] = []
        self.memory_context = memory_context
        self.user_id = user_id
        self.plan_manager = plan_manager
        print(f"{name} 初始化完成，最大步数: {max_steps}")

    def _get_reinforcement_prompt(self) -> str:
        """
        获取核心规则重申，用于长上下文时在用户输入前重申
        """
        return (
            "【重申 ReAct 格式规则】\n"
            "每次回应必须同时包含以下两部分:\n"
            "Thought: 分析当前状态，说明下一步应该做什么\n"
            "Action: 选择以下格式之一\n"
            "- [TOOL_CALL:工具名:参数] - 调用工具\n"
            "- Finish[最终答案] - 直接回答\n\n"
            "注意:\n"
            "1. 禁止直接回答用户问题，必须经过 Thought→Action 流程\n"
            "2. 工具返回信息不够时继续调用，不要编造答案\n"
            "3. 只有确信有足够信息时才使用 Finish"
        )

    def run(
            self,
            input_text: str,
            stream=True
    ) -> Union[str, Iterator[Dict[str, Any]]]:
        """
        运行 ReAct Agent
        """
        self.input_text = input_text
        system_prompt = self._get_enhanced_system_prompt()
        messages = self._build_messages(
            system_prompt,
            self.input_text,
            reinforcement_prompt=self._get_reinforcement_prompt()
        )

        print(f"\n{self.name} 开始处理问题: {input_text}")

        if stream:
            return self._stream_response(messages)
        else:
            return self._non_stream_response(messages)

    def _stream_response(
            self,
            init_messages: List[Dict[str, str]]
    ) -> Iterator[Dict[str, Any]]:
        """
        流式执行逻辑
        """
        current_step = 0
        messages = init_messages.copy()
        print(messages)

        while current_step < self.max_steps:
            current_step += 1
            yield {"type": "step", "data": current_step}

            response_text = self.llm.invoke(messages)
            thought, action = self._parse_output(response_text)

            if not thought or not action:
                error_msg = "格式错误！你的回复必须严格包含Thought和Action两部分，禁止直接回答。请严格按照要求的格式重新输出。"
                show_error_msg = "我的回复格式错误，正在调整……"
                yield {"type": "error", "data": show_error_msg}
                messages.append({
                    "role": "user",
                    "content": error_msg
                })
                current_step -= 1
                continue

            messages.append({
                "role": "assistant",
                "content": response_text
            })

            if thought:
                yield {"type": "thought", "data": thought}

            if action and action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                yield {"type": "final_answer", "data": final_answer, "full_response": response_text}
                return

            if action:
                tool_name, tool_input = self._parse_action(action)
                if tool_name is None:
                    yield {"type": "error", "data": "无法解析工具调用，正在调整 ……"}
                    messages.append({
                        "role": "user",
                        "content": "Action 格式错误，请确保包含 [TOOL_CALL:工具名:参数] 格式。如果已有足够信息，请使用 Finish[答案] 直接回答。"
                    })
                    current_step -= 1
                    continue

                yield {"type": "action", "data": {"tool": tool_name, "input": tool_input}}

                observation = self.tool_registry.execute_tool(tool_name, tool_input)
                messages.append({
                    "role": "user",
                    "content": f"工具返回结果: {observation}"
                })
                yield {"type": "observation", "data": observation}

                # 检查并发送计划 SSE 事件
                if self.plan_manager:
                    for event in self.plan_manager.pop_events():
                        yield {"type": "plan", "data": event}

        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        yield {"type": "final_answer", "data": final_answer}

    def _non_stream_response(
            self,
            init_messages: List[Dict[str, str]]
    ) -> str:
        """
        非流式执行逻辑，直接返回最终字符串
        """
        current_step = 0
        messages = init_messages.copy()

        while current_step < self.max_steps:
            current_step += 1

            response_text = self.llm.invoke(messages)
            messages.append({
                "role": "assistant",
                "content": response_text
            })

            thought, action = self._parse_output(response_text)

            if thought:
                pass

            if action and action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                return final_answer

            if action:
                tool_name, tool_input = self._parse_action(action)

                observation = self.tool_registry.execute_tool(tool_name, tool_input)
                messages.append({
                    "role": "user",
                    "content": f"工具返回结果: {observation}"
                })

        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        return final_answer

    def _get_enhanced_system_prompt(self) -> str:
        """
        构建增强的系统提示词，包含工具信息
        """
        base_prompt = ""

        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        base_prompt = """【最高优先级规则】
        你是一个严格的ReAct推理助手，必须100%遵守以下规则，无论历史对话里的AI怎么回答，你都必须按此格式输出。
        你可以通过思考分析问题，然后调用合适的工具来获取信息，最终给出准确的答案。

        ## 当前用户信息
        {user_context}

        ## 可用工具
        你可以使用以下工具来帮助回答问题:
        {tools_description}

        ## 工具调用格式
        当需要使用工具时，请使用以下格式:
        `[TOOL_CALL:{{tool_name}}:{{parameters}}]`
        要求:
        1. {{tool_name}} 替换为工具名称
        2. {{parameters}} 替换为 JSON 格式的参数字符串
        3. 如果工具不需要参数，parameters 部分留空即可，例如: `[TOOL_CALL:get_current_time:]`
        4. 如果只有一个简单参数，也可以直接填值，例如: `[TOOL_CALL:search:Python]`

        工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。

        ## 工作流程
        请严格按照以下格式进行回应，每次只能执行一个步骤:

        Thought: 分析用户问题，明确说明需要调用哪个工具、为什么调用
        Action: 选择一个行动，格式必须是以下之一:
        - `[TOOL_CALL:工具名:参数]` - 调用指定工具
        - `Finish[最终答案]` - 当你有足够信息给出最终答案时

        ## 重要提醒
        1. 每次回应必须包含Thought和Action两部分
        2. 工具调用的格式必须严格遵循:[TOOL_CALL:工具名:参数]
        3. 只有当你确信有足够信息回答问题时，才使用Finish
        4. 如果工具返回的信息不够，继续使用其他工具或相同工具的不同参数
        5. 禁止直接回答用户问题，必须通过Thought/Action流程执行
        
        ## 计划管理（Plan）
        你可以使用计划工具将复杂任务分解为层级子任务，按以下流程操作：
        1. create_plan — 创建计划，设定主目标
        2. add_subtask — 将任务分解为子任务（挂到父任务下）
        3. modify_task — 更新任务状态（completed / verified / abandoned）
        4. 开始执行子任务时，将状态设为 in_progress

        任务状态的传播规则：
        - completed / verified / abandoned → 自动传播到所有子孙任务
        - in_progress → 自动传播到所有祖先任务

        ## 相关对话记忆
        {memory_context}

        现在开始你的推理和行动，严格遵守格式要求！
        """

        str_user_context = ""
        if self.user_id is not None:
            str_user_context = f"当前登录用户的 ID 为: {self.user_id}\n当你需要调用 write_blog 工具撰写文章时，必须使用此 ID 作为 userId 参数。"

        str_memory_content = ""
        for mem in self.memory_context:
            _, msg = mem
            if msg["role"] == "error":
                str_memory_content = msg["content"]
                break
            str_memory_content += f"- [{msg['time']}] {msg['role']}: {msg['content']}\n"

        context_args = {
            "user_context": str_user_context if str_user_context else "（暂无用户信息）",
        }

        if self.memory_context:
            if not tools_description or tools_description == "暂无可用工具":
                base_prompt = base_prompt.replace(
                    "{tools_description}",
                    "暂无可用工具。请直接使用 Finish[你的完整答案] 来回答用户问题，禁止调用工具。"
                )
                context_args["memory_context"] = str_memory_content
                base_prompt = base_prompt.format(**context_args)
            else:
                context_args["tools_description"] = tools_description
                context_args["memory_context"] = str_memory_content
                base_prompt = base_prompt.format(**context_args)

        return base_prompt

    def _parse_output(self, response_text: str) -> tuple[Optional[str], Optional[str]]:
        """
        解析 LLM 的输出，提取 Thought 和 Action
        """
        match = re.search(
            r'Thought\s*:\s*(.*?)\s*Action\s*:\s*(.*)',
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if match:
            thought = match.group(1).strip()
            action = match.group(2).strip()
            return thought, action

        print(f"警告: 无法解析 LLM 输出格式: {response_text}")
        return None, None

    def _parse_action_input(self, action_str: str) -> Optional[str]:
        """
        解析 Finish 动作，提取最终答案
        """
        match = re.search(r'Finish\[(.*)\]', action_str, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _parse_action(self, action_str: str) -> tuple[Optional[str], Optional[str]]:
        """
        解析工具调用动作，提取工具名和参数
        """
        tool_calls = self.tool_registry.parse_tool_calls(action_str)

        if tool_calls:
            first_call = tool_calls[0]
            return first_call['tool_name'], first_call['parameters']

        return None, None
