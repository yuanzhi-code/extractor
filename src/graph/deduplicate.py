import logging
from typing import Dict, Literal

from bertopic import BERTopic
from langgraph.types import Command
from pandas import DataFrame
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

from src.graph.state import DeduplicateState

logger = logging.getLogger(__name__)

stopwords = [
    "的",
    "是",
    "在",
    "我",
    "你",
    "他",
    "她",
    "它",
    "们",
    "这",
    "那",
    "和",
    "与",
    "但",
    "而",
    "则",
    "所以",
    "因此",
    "一个",
    "一种",
    "一些",
    "了",
    "着",
    "过",
    "也",
    "都",
    "又",
    "再",
    "很",
    "非常",
    "十分",
    "没有",
    "不",
    "能够",
    "可以",
    "将",
    "把",
    "向",
    "从",
    "通过",
    "对于",
    "关于",
    "以及",
    "并且",
    "或者",
    "然而",
    "虽然",
    "但是",
    "因为",
    "所以",
    "除非",
    "只要",
    "无论",
    "等等",
    "等",
    "之",
    "所",
]


def _get_representive_docs_(info: DataFrame) -> Dict[int, str]:
    """
    Arguments:
        info: the result of get_document_info from bertopic model

    Result:
        a dict of docs id and the representative document sort by Topic id
    """

    return (
        info[(info["Representative_document"] is True) & (info["Topic"] != -1)]
        .sort_values("Probability", ascending=False)
        .drop_duplicates(subset="Topic", keep="first")
        .sort_values("Topic")
        .filter(items=["Document"])["Document"]
        .to_dict()
    )


def deduplicate_node(state: DeduplicateState) -> Command[Literal["reporter"]]:
    docs = state.get("contents")

    # 如果文档数量太少，直接返回
    if len(docs) < 2:
        return Command(
            update={"deduplicated_contents": {0: docs[0]} if docs else {}}
        )

    embed_model = SentenceTransformer("moka-ai/m3e-base")
    pre_embeddings = embed_model.encode(docs, show_progress_bar=True)
    vectorizer_model = CountVectorizer(stop_words=stopwords)

    # 调整参数以适应小数据集
    bertopic_model = BERTopic(
        embedding_model=embed_model,
        vectorizer_model=vectorizer_model,
        language="chinese",
        min_topic_size=2,  # 允许更小的主题
        verbose=True,
    )
    docs_to_topic, _ = bertopic_model.fit_transform(
        docs, embeddings=pre_embeddings
    )
    docs_info = bertopic_model.get_document_info(docs)
    representative_docs = _get_representive_docs_(docs_info)
    logger.info(f"representative docs {representative_docs}")

    return Command(update={"deduplicated_contents": representative_docs})
