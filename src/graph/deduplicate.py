import logging

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

from src.graph.state import State

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


def deduplicate_node(state: State):
    docs = [state["content"]]
    # embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    embed_model = SentenceTransformer(model_name_or_path="moka-ai/m3e-base")
    pre_embeddings = embed_model.encode(docs, show_progress_bar=True)
    vectorizer_model = CountVectorizer(stop_words=stopwords)
    bertopic_model = BERTopic(
        embedding_model=embed_model,
        vectorizer_model=vectorizer_model,
        language="chinese",
        nr_topics=5,
        top_n_words=5,
        verbose=True,
    )
    docs_to_topic, _ = bertopic_model.fit_transform(
        docs, embeddings=pre_embeddings
    )
    topic_info = bertopic_model.get_topic_info()
    logger.info("topic_info:\n{}", topic_info)
    return state
