"""系统监控工具 - 获取服务器 CPU、内存、磁盘、进程等信息"""

import os
import platform
import shutil
from datetime import datetime

from langchain_core.tools import tool
from loguru import logger


@tool
def get_system_info() -> str:
    """获取操作系统基本信息：名称、版本、架构、启动时间、运行时长"""
    try:
        import psutil
    except ImportError:
        return "需要安装 psutil: pip install psutil"

    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        return (
            f"操作系统: {platform.system()} {platform.release()}\n"
            f"版本: {platform.version()}\n"
            f"架构: {platform.machine()}\n"
            f"主机名: {platform.node()}\n"
            f"启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"运行时长: {uptime.days} 天 {uptime.seconds // 3600} 小时 {(uptime.seconds % 3600) // 60} 分钟"
        )
    except Exception as e:
        logger.error(f"get_system_info 失败: {e}")
        return f"获取系统信息失败: {e}"


@tool
def get_cpu_usage() -> str:
    """获取 CPU 使用率（当前和平均负载）"""
    try:
        import psutil
    except ImportError:
        return "需要安装 psutil: pip install psutil"

    try:
        percent = psutil.cpu_percent(interval=0.5)
        count = psutil.cpu_count()
        freq = psutil.cpu_freq()
        freq_str = f"{freq.current:.0f} MHz" if freq else "未知"

        # 平均负载（仅 Unix）
        load = getattr(os, "getloadavg", None)
        load_str = ""
        if load:
            avg = load()
            load_str = f"\n平均负载 (1/5/15分钟): {avg[0]:.2f} / {avg[1]:.2f} / {avg[2]:.2f}"

        return (
            f"CPU 使用率: {percent}%\n"
            f"CPU 核心数: {count}\n"
            f"CPU 频率: {freq_str}"
            f"{load_str}"
        )
    except Exception as e:
        logger.error(f"get_cpu_usage 失败: {e}")
        return f"获取 CPU 信息失败: {e}"


@tool
def get_memory_usage() -> str:
    """获取内存使用情况：总量、已用、可用、使用率"""
    try:
        import psutil
    except ImportError:
        return "需要安装 psutil: pip install psutil"

    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return (
            f"📊 内存使用\n"
            f"总计: {mem.total / 1024**3:.1f} GB\n"
            f"已用: {mem.used / 1024**3:.1f} GB\n"
            f"可用: {mem.available / 1024**3:.1f} GB\n"
            f"使用率: {mem.percent}%\n"
            f"\n交换分区:\n"
            f"  总计: {swap.total / 1024**3:.1f} GB\n"
            f"  已用: {swap.used / 1024**3:.1f} GB ({swap.percent}%)"
        )
    except Exception as e:
        logger.error(f"get_memory_usage 失败: {e}")
        return f"获取内存信息失败: {e}"


@tool
def get_disk_usage(path: str = "") -> str:
    """获取磁盘使用情况

    Args:
        path: 磁盘路径。Windows 下如 C:/ D:/，Unix 下如 / /home。为空则返回所有可见磁盘。
    """
    try:
        import psutil
    except ImportError:
        return "需要安装 psutil: pip install psutil"

    try:
        if path:
            # 查询单个路径
            usage = shutil.disk_usage(path)
            return (
                f"📀 磁盘使用: {path}\n"
                f"总计: {usage.total / 1024**3:.1f} GB\n"
                f"已用: {usage.used / 1024**3:.1f} GB\n"
                f"可用: {usage.free / 1024**3:.1f} GB\n"
                f"使用率: {usage.used / usage.total * 100:.1f}%"
            )
        else:
            # 列出所有分区
            parts = psutil.disk_partitions()
            lines = ["📀 磁盘分区:"]
            for p in parts:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    lines.append(
                        f"  {p.device} ({p.mountpoint}) — "
                        f"{usage.used / 1024**3:.1f} / {usage.total / 1024**3:.1f} GB "
                        f"({usage.percent}%)"
                    )
                except PermissionError:
                    lines.append(f"  {p.device} ({p.mountpoint}) — 无权限")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_disk_usage 失败: {e}")
        return f"获取磁盘信息失败: {e}"


@tool
def get_process_stats() -> str:
    """获取进程统计：总数、按状态分组、Top CPU/内存占用进程"""
    try:
        import psutil
    except ImportError:
        return "需要安装 psutil: pip install psutil"

    try:
        # 统计进程数
        processes = list(psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_percent"]))
        total = len(processes)

        # 按状态分组
        status_count = {}
        for p in processes:
            s = p.info.get("status", "unknown")
            status_count[s] = status_count.get(s, 0) + 1

        # CPU 占用 Top 5
        by_cpu = sorted(
            [p for p in processes if p.info.get("cpu_percent")],
            key=lambda p: p.info["cpu_percent"],
            reverse=True,
        )[:5]

        # 内存占用 Top 5
        by_mem = sorted(
            [p for p in processes if p.info.get("memory_percent")],
            key=lambda p: p.info["memory_percent"],
            reverse=True,
        )[:5]

        lines = [f"📋 进程统计\n总进程数: {total}", "\n状态分布:"]
        for s, c in sorted(status_count.items(), key=lambda x: -x[1]):
            lines.append(f"  {s}: {c}")

        lines.append("\n🔥 CPU Top 5:")
        for p in by_cpu:
            lines.append(f"  {p.info['name'][:30]:30s} {p.info['cpu_percent']:5.1f}%")

        lines.append("\n💾 内存 Top 5:")
        for p in by_mem:
            lines.append(f"  {p.info['name'][:30]:30s} {p.info['memory_percent']:5.1f}%")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_process_stats 失败: {e}")
        return f"获取进程信息失败: {e}"
