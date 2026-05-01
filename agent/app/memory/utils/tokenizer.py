import os
import jieba
from typing import Set

def jieba_tokenizer(text):
    """
    自定义分词器: 使用 jieba 进行分词
    """
    return jieba.lcut(text)

def load_stopwords() -> Set[str]:
    """
    从 scripts/stopwords.txt 加载中文停用词表
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    app_dir = os.path.dirname(os.path.dirname(current_dir))

    stopwords_path = os.path.join(app_dir, "scripts", "stopwords.txt")

    stopwords = set()

    try:
        with open(stopwords_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    stopwords.add(line)
        print(f"成功加载停用词表，共 {len(stopwords)} 个词")
    except FileNotFoundError:
        print(f"警告: 未找到停用词表文件 {stopwords_path}，将使用空停用词表")

    return stopwords

STOPWORDS = load_stopwords()
