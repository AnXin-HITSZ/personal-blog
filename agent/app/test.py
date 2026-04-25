# app/test_memory.py
import time
from app.memory.working_memory import MemoryItem, MemoryConfig, WorkingMemory


def test_retrieval():
    print("=== 测试混合检索功能 ===\n")

    # 1. 初始化
    config = MemoryConfig(working_memory_capacity=20, working_memory_ttl=60)
    wm = WorkingMemory(config)

    # 2. 添加一些测试记忆（模拟一个真实的对话历史）
    print("正在添加测试记忆...")

    memories = [
        ("你好，我是新来的", "user", 0.8),
        ("你好！欢迎访问我的博客。", "assistant", 0.7),
        ("Python怎么安装？", "user", 0.9),
        ("你可以去python.org下载安装包。", "assistant", 0.7),
        ("Redis是什么？", "user", 0.9),
        ("Redis是一个内存数据库，速度很快。", "assistant", 0.7),
        ("Redis和MySQL有什么区别？", "user", 0.8),
        ("Redis是NoSQL，MySQL是关系型数据库。", "assistant", 0.7),
        ("今天天气真好", "user", 0.5),
        ("是的，适合出去走走。", "assistant", 0.5),
    ]

    for content, role, imp in memories:
        wm.add(MemoryItem(content=content, role=role, importance=imp))
        time.sleep(0.01)  # 稍微错开时间，让时间戳不一样

    # 3. 测试检索
    print("\n--- 开始检索测试 ---")

    test_queries = [
        "Redis数据库",
        "Python安装",
        "天气怎么样"
    ]

    for query in test_queries:
        print(f"\n🔍 查询: '{query}'")
        results = wm.retrieve(query, limit=3)

        if results:
            print("  最相关的记忆:")
            for i, mem in enumerate(results):
                # 简单计算一下分数用于展示（实际逻辑在retrieve内部）
                print(f"  {i + 1}. [{mem.role}] {mem.content}")
        else:
            print("  未找到相关记忆")


if __name__ == "__main__":
    test_retrieval()