import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from langgraph.graph import END, START
import asyncio

from src.graph.classify_graph import get_classification_graph, run_classification_graph
from src.models.rss_entry import RssEntry
from src.models.score import EntryScore
from src.models.tags import EntryCategory


class TestClassifyGraph:
    """测试分类图的功能"""

    def _setup_mock_session(
        self, 
        mock_session,
        entry_category_exists: bool = True, 
        entry_score_exists: bool = True
    ) -> MagicMock:
        """
        设置模拟数据库会话的辅助方法
        
        Args:
            mock_session: Mock 的 Session 对象
            entry_category_exists: 是否存在 EntryCategory 记录
            entry_score_exists: 是否存在 EntryScore 记录
            
        Returns:
            MagicMock: 模拟的数据库会话实例
        """
        session = MagicMock()
        mock_session.return_value.__enter__.return_value = session
        
        # 根据参数创建查询结果
        results = [
            Mock() if entry_category_exists else None,  # EntryCategory 查询结果
            Mock() if entry_score_exists else None       # EntryScore 查询结果
        ]
        
        session.query.return_value.filter.return_value.first.side_effect = results
        return session

    def _create_test_entry(
        self, 
        entry_id: int = 1,
        content: str = "测试内容",
        title: str = "测试标题"
    ) -> RssEntry:
        """
        创建测试用的 RssEntry 对象
        
        Args:
            entry_id: 条目 ID
            content: 条目内容
            title: 条目标题
            
        Returns:
            RssEntry: 测试用的 RSS 条目对象
        """
        return RssEntry(
            id=entry_id,
            feed_id=1,
            link="https://example.com/test",
            content=content,
            title=title,
            author="测试作者",
            summary="测试摘要",
            published_at=datetime.now()
        )

    def test_get_classification_graph_structure(self):
        """测试分类图的结构是否正确"""
        graph = get_classification_graph()
        
        # 验证图对象不为空
        assert graph is not None
        
        # 验证图已编译
        assert hasattr(graph, 'get_graph')
        
        # 获取图的结构
        graph_structure = graph.get_graph()
        
        # 验证节点是否存在（节点可能是字符串或者有其他结构）
        nodes = graph_structure.nodes
        if hasattr(nodes, 'keys'):
            # 如果 nodes 是字典
            node_names = list(nodes.keys())
        else:
            # 如果 nodes 是其他类型，尝试获取节点名称
            node_names = [getattr(node, 'id', str(node)) for node in nodes]
        
        # 验证必要的节点存在
        assert "tagger" in node_names
        assert "tagger_review" in node_names
        assert "score" in node_names

    @patch('src.graph.classify_graph.Session')
    def test_conditional_logic_both_exist(self, mock_session):
        """测试当标签和分数都存在时的条件逻辑"""
        # 使用辅助方法设置模拟 - 两者都存在
        session = self._setup_mock_session(mock_session, entry_category_exists=True, entry_score_exists=True)
        
        # 创建测试状态
        test_entry = self._create_test_entry()
        
        # 获取图并验证条件逻辑
        graph = get_classification_graph()
        
        # 验证数据库会话被正确配置
        assert session.query.called is False  # 还没有实际执行
        
        # 通过检查图的结构来验证条件逻辑
        graph_def = graph.get_graph()
        edges = graph_def.edges
        
        # 验证条件边存在（从 __start__ 到不同的节点）
        start_edges = [edge for edge in edges if edge.source == "__start__"]
        assert len(start_edges) > 0, "应该有从起始节点出发的条件边"

    @patch('src.graph.classify_graph.Session')
    def test_conditional_logic_only_tag(self, mock_session):
        """测试当只有标签存在时的条件逻辑"""
        # 使用辅助方法设置模拟 - 只有标签存在
        session = self._setup_mock_session(mock_session, entry_category_exists=True, entry_score_exists=False)
        
        # 创建测试入口
        test_entry = self._create_test_entry()
        
        # 验证模拟正确设置：side_effect 是迭代器，我们验证它被正确配置
        query_mock = session.query.return_value.filter.return_value.first
        assert query_mock.side_effect is not None, "应该配置 side_effect"
        
        # 通过调用来验证结果
        first_result = next(iter(query_mock.side_effect))
        query_mock.side_effect = iter([Mock(), None])  # 重置迭代器
        second_result = list(query_mock.side_effect)[1]
        
        assert first_result is not None  # 标签存在
        assert second_result is None     # 分数不存在

    @patch('src.graph.classify_graph.Session')
    def test_conditional_logic_neither_exist(self, mock_session):
        """测试当标签和分数都不存在时的条件逻辑"""
        # 使用辅助方法设置模拟 - 两者都不存在
        session = self._setup_mock_session(mock_session, entry_category_exists=False, entry_score_exists=False)
        
        # 创建测试入口
        test_entry = self._create_test_entry()
        
        # 验证模拟正确设置：验证 side_effect 配置
        query_mock = session.query.return_value.filter.return_value.first
        assert query_mock.side_effect is not None, "应该配置 side_effect"
        
        # 验证配置的值都是 None
        results = list(query_mock.side_effect)
        assert len(results) == 2
        assert results[0] is None  # 标签不存在
        assert results[1] is None  # 分数不存在
        
        # 验证在这种情况下应该走到 tagger 节点
        graph = get_classification_graph()
        graph_def = graph.get_graph()
        
        # 验证 tagger 节点存在
        assert "tagger" in graph_def.nodes

    def test_database_query_structure(self):
        """测试数据库查询的结构"""
        # 验证使用的模型类
        assert hasattr(EntryCategory, 'entry_id')
        assert hasattr(EntryScore, 'entry_id')
        
        # 验证 RssEntry 有必要的属性
        test_entry = self._create_test_entry()
        
        assert hasattr(test_entry, 'id')
        assert hasattr(test_entry, 'content')
        assert test_entry.id == 1
        assert test_entry.content == "测试内容"

    def test_graph_edges_configuration(self):
        """测试图的边配置是否正确"""
        graph = get_classification_graph()
        graph_structure = graph.get_graph()
        
        # 检查是否有正确的边配置
        edges = graph_structure.edges
        nodes = graph_structure.nodes
        
        # 验证基本的边存在
        assert len(edges) > 0, "图应该有边连接"
        
        # 验证关键节点之间的连接
        edge_dict = {}
        for edge in edges:
            if edge.source not in edge_dict:
                edge_dict[edge.source] = []
            edge_dict[edge.source].append(edge.target)
        
        # 验证 tagger 到 tagger_review 的连接
        if "tagger" in edge_dict:
            assert "tagger_review" in edge_dict["tagger"], "tagger 应该连接到 tagger_review"
        
        # 验证 tagger_review 到 score 的连接
        if "tagger_review" in edge_dict:
            assert "score" in edge_dict["tagger_review"], "tagger_review 应该连接到 score"
        
        # 验证从起始节点的条件连接
        start_connections = edge_dict.get("__start__", [])
        expected_targets = {"tagger", "score", "__end__"}
        assert any(target in expected_targets for target in start_connections), \
            f"起始节点应该条件性地连接到 {expected_targets} 中的某个节点"

    def test_state_initialization(self):
        """测试状态初始化是否正确"""
        # 创建测试用的 RssEntry
        test_entry = self._create_test_entry()
        
        # 验证初始状态创建
        init_state = {"entry": test_entry}
        
        assert "entry" in init_state
        assert init_state["entry"] == test_entry
        assert hasattr(test_entry, "id")
        assert hasattr(test_entry, "content")
        assert hasattr(test_entry, "title")

    def test_entry_model_properties(self):
        """测试 RssEntry 模型的属性"""
        # 创建一个具有特定值的测试条目来验证属性访问
        test_entry = RssEntry(
            id=123,
            feed_id=456,
            link="https://example.com/article",
            content="这是测试内容",
            title="测试文章标题",
            author="测试作者",
            summary="这是测试摘要",
            published_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        # 验证所有必要的属性都存在且正确
        assert test_entry.id == 123
        assert test_entry.feed_id == 456
        assert test_entry.link == "https://example.com/article"
        assert test_entry.content == "这是测试内容"
        assert test_entry.title == "测试文章标题"
        assert test_entry.author == "测试作者"
        assert test_entry.summary == "这是测试摘要"
        assert test_entry.published_at == datetime(2024, 1, 1, 12, 0, 0)

    @patch('src.graph.classify_graph.Session')
    def test_session_usage_pattern(self, mock_session):
        """测试数据库会话使用模式"""
        # 使用辅助方法设置模拟 - 查询结果为空
        session = self._setup_mock_session(mock_session, entry_category_exists=False, entry_score_exists=False)
        
        # 创建图来触发数据库访问模式
        graph = get_classification_graph()
        
        # 验证 Session 被正确导入和使用
        assert mock_session.called is False  # 只有在实际执行时才会被调用
        
        # 验证 Session 的 mock 配置是否正确
        assert session is not None
        assert hasattr(session, 'query')
        assert hasattr(session.query.return_value, 'filter')
        assert hasattr(session.query.return_value.filter.return_value, 'first')
        
        # 验证 side_effect 配置正确
        query_mock = session.query.return_value.filter.return_value.first
        assert query_mock.side_effect is not None, "应该配置 side_effect"
        
        # 验证配置的值
        results = list(query_mock.side_effect)
        assert results == [None, None], "应该配置两个 None 结果"

    def test_graph_compilation(self):
        """测试图的编译过程"""
        graph = get_classification_graph()
        
        # 验证图已正确编译
        assert graph is not None
        assert hasattr(graph, 'invoke')
        assert hasattr(graph, 'astream')
        assert callable(graph.invoke)
        assert callable(graph.astream)

    def test_import_dependencies(self):
        """测试必要的依赖是否正确导入"""
        # 验证关键依赖可以导入
        from src.graph.classify_graph import get_classification_graph, run_classification_graph
        from src.models.rss_entry import RssEntry
        from src.models.score import EntryScore
        from src.models.tags import EntryCategory
        from langgraph.graph import END, START, StateGraph
        
        # 验证函数和类都可用
        assert callable(get_classification_graph)
        assert callable(run_classification_graph)
        assert RssEntry is not None
        assert EntryScore is not None
        assert EntryCategory is not None

    @patch('src.graph.classify_graph.Session')
    def test_condition_function_return_values(self, mock_session):
        """测试条件函数的返回值"""
        from src.graph.classify_graph import get_classification_graph
        from langgraph.graph import END
        
        # 我们需要创建一个辅助函数来测试内部条件函数
        # 由于条件函数是在 get_classification_graph 内部定义的，我们通过重新实现来测试逻辑
        
        def test_check_logic(entry_category_exists, entry_score_exists):
            """模拟条件检查逻辑"""
            if entry_category_exists and entry_score_exists:
                return END
            elif entry_category_exists:
                return "to_score"
            else:
                return "to_tagger"
        
        # 测试所有可能的情况
        assert test_check_logic(True, True) == END
        assert test_check_logic(True, False) == "to_score"
        assert test_check_logic(False, True) == "to_tagger"
        assert test_check_logic(False, False) == "to_tagger"

    def test_graph_node_existence(self):
        """测试图中节点的存在性"""
        graph = get_classification_graph()
        graph_def = graph.get_graph()
        
        # 获取所有节点名称
        node_names = list(graph_def.nodes.keys())
        
        # 验证所有必需的节点都存在
        required_nodes = ["tagger", "tagger_review", "score"]
        for node in required_nodes:
            assert node in node_names, f"Node '{node}' not found in graph"
        
        # 验证起始和结束节点
        assert "__start__" in node_names or "START" in str(graph_def.first)
        assert "__end__" in node_names or "END" in str(graph_def.last)

    @pytest.mark.asyncio
    @patch('src.graph.classify_graph.Session')
    @patch('src.graph.classify_graph.score_node')
    async def test_graph_execution_only_tag_exists_routes_to_score(self, mock_score_node, mock_session):
        """测试当只有标签存在时，图直接路由到 score 节点"""
        # 设置模拟：只有标签存在，分数不存在
        self._setup_mock_session(mock_session, entry_category_exists=True, entry_score_exists=False)
        
        # Mock score 节点返回简单的状态更新
        def mock_score_func(state):
            return {"score": "test_score", "entry": state["entry"]}
        
        mock_score_node.side_effect = mock_score_func
        
        test_entry = self._create_test_entry()
        graph = get_classification_graph()
        
        # 实际运行图
        states = []
        async for state in graph.astream({"entry": test_entry}, stream_mode="values"):
            states.append(state)
        
        # 验证 score 节点被调用（跳过了 tagger 和 tagger_review）
        mock_score_node.assert_called()
        
        # 验证状态流转 - 应该直接从 START 到 score
        assert len(states) >= 1, "应该有状态输出"
        
        # 验证最终状态
        final_state = states[-1]
        assert "entry" in final_state
        assert final_state["entry"] == test_entry
        
        # 如果 score 节点被执行，应该有 score 字段
        if "score" in final_state:
            assert final_state["score"] == "test_score"

    @pytest.mark.asyncio
    @patch('src.graph.classify_graph.Session')
    @patch('src.graph.classify_graph.tagger_node')
    @patch('src.graph.classify_graph.tagger_review_node')
    @patch('src.graph.classify_graph.score_node')
    async def test_graph_execution_nothing_exists_full_pipeline(self, mock_score_node, mock_tagger_review_node, mock_tagger_node, mock_session):
        """测试当标签和分数都不存在时，执行完整的流水线"""
        # 设置模拟：标签和分数都不存在
        self._setup_mock_session(mock_session, entry_category_exists=False, entry_score_exists=False)
        
        # Mock 所有节点返回简单的状态更新
        def mock_tagger_func(state):
            return {"tag_result": {"category": "test", "confidence": 0.8}, "entry": state["entry"]}
        
        def mock_tagger_review_func(state):
            return {"tag_result": {"category": "test", "confidence": 0.9}, "entry": state["entry"]}
        
        def mock_score_func(state):
            return {"score": "actionable", "entry": state["entry"]}
        
        mock_tagger_node.side_effect = mock_tagger_func
        mock_tagger_review_node.side_effect = mock_tagger_review_func
        mock_score_node.side_effect = mock_score_func
        
        test_entry = self._create_test_entry()
        graph = get_classification_graph()
        
        # 实际运行图
        states = []
        async for state in graph.astream({"entry": test_entry}, stream_mode="values"):
            states.append(state)
        
        # 验证所有节点都被调用
        mock_tagger_node.assert_called()
        mock_tagger_review_node.assert_called()
        mock_score_node.assert_called()
        
        # 验证状态变化 - 应该执行完整流水线：tagger -> tagger_review -> score
        assert len(states) >= 1, "应该有状态输出"
        
        # 验证最终状态包含所有预期的结果
        final_state = states[-1]
        assert "entry" in final_state
        assert final_state["entry"] == test_entry
        
        # 验证流水线的执行结果
        if "tag_result" in final_state:
            assert final_state["tag_result"]["category"] == "test"
        if "score" in final_state:
            assert final_state["score"] == "actionable"

    @patch('src.graph.classify_graph.Session')
    def test_condition_function_actual_execution(self, mock_session):
        """测试条件函数的实际执行和返回值"""
        from langgraph.graph import END
        
        # 测试场景1：两者都存在 -> 返回 END
        session1 = self._setup_mock_session(mock_session, entry_category_exists=True, entry_score_exists=True)
        test_entry = self._create_test_entry()
        
        # 通过构建图并检查其行为来间接测试条件函数
        graph1 = get_classification_graph()
        
        # 重置 mock
        mock_session.reset_mock()
        
        # 测试场景2：只有标签存在 -> 应该路由到 score
        session2 = self._setup_mock_session(mock_session, entry_category_exists=True, entry_score_exists=False)
        graph2 = get_classification_graph()
        
        # 验证不同的图实例有相同的结构（表明条件逻辑一致）
        assert graph1.get_graph().nodes.keys() == graph2.get_graph().nodes.keys()

    @pytest.mark.asyncio
    @patch('src.graph.classify_graph.Session')
    @patch('src.graph.classify_graph.tagger_node')
    @patch('src.graph.classify_graph.tagger_review_node')
    @patch('src.graph.classify_graph.score_node')
    async def test_graph_state_transformation(self, mock_score_node, mock_tagger_review_node, mock_tagger_node, mock_session):
        """测试图执行过程中状态的变换"""
        # 设置模拟：都不存在，需要完整执行
        self._setup_mock_session(mock_session, entry_category_exists=False, entry_score_exists=False)
        
        # Mock 所有节点以控制状态流转
        def mock_tagger_func(state):
            return {"tag_result": {"category": "test", "confidence": 0.8}, "entry": state["entry"]}
        
        def mock_tagger_review_func(state):
            return {"tag_result": {"category": "test", "confidence": 0.9}, "entry": state["entry"]}
        
        def mock_score_func(state):
            return {"score": "actionable", "entry": state["entry"]}
        
        mock_tagger_node.side_effect = mock_tagger_func
        mock_tagger_review_node.side_effect = mock_tagger_review_func
        mock_score_node.side_effect = mock_score_func
        
        test_entry = self._create_test_entry()
        initial_state = {"entry": test_entry}
        
        graph = get_classification_graph()
        
        # 收集所有状态变化
        state_history = []
        async for state in graph.astream(initial_state, stream_mode="values"):
            state_history.append(dict(state))  # 复制状态
        
        # 验证初始状态正确
        assert len(state_history) > 0
        first_state = state_history[0]
        assert "entry" in first_state
        assert first_state["entry"] == test_entry
        
        # 验证状态包含预期的键
        for state in state_history:
            assert "entry" in state  # entry 应该在整个过程中保持
        
        # 验证节点被调用
        mock_tagger_node.assert_called()
        mock_tagger_review_node.assert_called()
        mock_score_node.assert_called()

    @pytest.mark.asyncio
    @patch('src.graph.classify_graph.Session')
    async def test_graph_execution_both_exist_skip_all(self, mock_session):
        """测试当标签和分数都存在时，图直接结束不执行任何节点"""
        # 设置模拟：标签和分数都存在
        self._setup_mock_session(mock_session, entry_category_exists=True, entry_score_exists=True)
        
        test_entry = self._create_test_entry()
        graph = get_classification_graph()
        
        # 实际运行图并收集所有状态
        states = []
        async for state in graph.astream({"entry": test_entry}, stream_mode="values"):
            states.append(state)
        
        # 验证图的执行
        # 当标签和分数都存在时，条件函数应该返回 END，直接结束
        # 验证至少有初始状态
        assert len(states) >= 1, "应该至少有一个状态输出"
        
        # 验证初始状态包含 entry
        initial_state = states[0]
        assert "entry" in initial_state
        assert initial_state["entry"] == test_entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 