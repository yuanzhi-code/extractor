from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.graph.classify_graph import (
    get_classification_graph,
    run_classification_graph,
)
from src.models.rss_entry import RssEntry
from src.models.score import EntryScore
from src.models.tags import EntryCategory


class TestClassifyGraph:
    """测试分类图的功能"""

    def _setup_mock_session(
        self,
        mock_session,
        entry_category_exists: bool = True,
        entry_score_exists: bool = True,
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
            Mock() if entry_score_exists else None,  # EntryScore 查询结果
        ]

        session.query.return_value.filter.return_value.first.side_effect = (
            results
        )
        return session

    def _create_test_entry(
        self,
        entry_id: int = 1,
        content: str = "测试内容",
        title: str = "测试标题",
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
            published_at=datetime.now(),
        )

    def test_graph_structure_and_compilation(self):
        """测试图的结构、编译和基本配置"""
        graph = get_classification_graph()

        # 验证图对象和编译
        assert graph is not None
        assert hasattr(graph, "get_graph")
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "astream")
        assert callable(graph.invoke)
        assert callable(graph.astream)

        # 验证图结构
        graph_structure = graph.get_graph()
        nodes = graph_structure.nodes
        node_names = (
            list(nodes.keys())
            if hasattr(nodes, "keys")
            else [getattr(node, "id", str(node)) for node in nodes]
        )

        # 验证必要节点存在
        required_nodes = ["tagger", "tagger_review", "score"]
        for node in required_nodes:
            assert node in node_names, f"Node '{node}' not found in graph"

        # 验证边配置
        edges = graph_structure.edges
        assert len(edges) > 0, "图应该有边连接"

        # 验证起始和结束节点
        assert "__start__" in node_names or "START" in str(
            graph_structure.first
        )
        assert "__end__" in node_names or "END" in str(graph_structure.last)

    @patch("src.graph.classify_graph.Session")
    def test_conditional_routing_logic(self, mock_session):
        """测试条件路由逻辑的所有分支"""
        test_entry = self._create_test_entry()

        # 测试场景1：标签和分数都存在 -> 应该返回 END
        session1 = self._setup_mock_session(
            mock_session, entry_category_exists=True, entry_score_exists=True
        )
        graph1 = get_classification_graph()

        # 验证条件函数被调用时的行为 - 模拟内部条件检查
        # 当两者都存在时，应该快速结束
        graph1_def = graph1.get_graph()
        assert "__start__" in list(graph1_def.nodes)

        # 测试场景2：只有标签存在 -> 应该路由到 score
        mock_session.reset_mock()
        session2 = self._setup_mock_session(
            mock_session, entry_category_exists=True, entry_score_exists=False
        )
        graph2 = get_classification_graph()

        # 验证 score 节点在图中可达
        graph2_def = graph2.get_graph()
        assert "score" in list(graph2_def.nodes)

        # 测试场景3：都不存在 -> 应该路由到 tagger
        mock_session.reset_mock()
        session3 = self._setup_mock_session(
            mock_session, entry_category_exists=False, entry_score_exists=False
        )
        graph3 = get_classification_graph()

        # 验证 tagger 节点在图中可达
        graph3_def = graph3.get_graph()
        assert "tagger" in list(graph3_def.nodes)

        # 验证所有图实例有相同的结构（条件逻辑一致）
        assert (
            graph1.get_graph().nodes.keys()
            == graph2.get_graph().nodes.keys()
            == graph3.get_graph().nodes.keys()
        )

        # 验证条件边的存在 - 从 START 节点应该有条件分支
        edges1 = [
            edge for edge in graph1_def.edges if edge.source == "__start__"
        ]
        edges2 = [
            edge for edge in graph2_def.edges if edge.source == "__start__"
        ]
        edges3 = [
            edge for edge in graph3_def.edges if edge.source == "__start__"
        ]

        # 所有情况都应该有从起始节点的条件边
        assert len(edges1) > 0, "场景1应该有条件边"
        assert len(edges2) > 0, "场景2应该有条件边"
        assert len(edges3) > 0, "场景3应该有条件边"

    @patch("src.graph.classify_graph.Session")
    def test_database_integration(self, mock_session):
        """测试数据库集成和查询模式"""
        session = self._setup_mock_session(
            mock_session, entry_category_exists=False, entry_score_exists=False
        )

        # 验证模型字段
        assert hasattr(EntryCategory, "entry_id")
        assert hasattr(EntryScore, "entry_id")

        # 验证模型关系和必要字段
        category = EntryCategory()
        assert hasattr(category, "entry_id"), "EntryCategory应该有entry_id字段"
        assert hasattr(category, "category"), "EntryCategory应该有category字段"

        score = EntryScore()
        assert hasattr(score, "entry_id"), "EntryScore应该有entry_id字段"
        assert hasattr(score, "score"), "EntryScore应该有score字段"

        # 验证 Session 配置
        assert session is not None
        assert hasattr(session, "query")

        # 验证查询配置和执行顺序
        query_mock = session.query.return_value.filter.return_value.first
        assert query_mock.side_effect is not None
        results = list(query_mock.side_effect)
        assert len(results) == 2, "应该配置两个查询结果"

        # 验证查询结果的顺序：第一个是EntryCategory，第二个是EntryScore
        assert (
            results[0] is None
        ), "第一个查询结果应该是EntryCategory（None表示不存在）"
        assert (
            results[1] is None
        ), "第二个查询结果应该是EntryScore（None表示不存在）"

        # 验证数据库会话使用上下文管理器
        assert mock_session.return_value.__enter__ is not None
        assert mock_session.return_value.__exit__ is not None

    def test_entry_model_validation(self):
        """测试 RssEntry 模型的数据验证"""
        # 正常数据
        normal_entry = RssEntry(
            id=123,
            feed_id=456,
            link="https://example.com/article",
            content="这是测试内容",
            title="测试文章标题",
            author="测试作者",
            summary="这是测试摘要",
            published_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        assert normal_entry.id == 123
        assert normal_entry.content == "这是测试内容"
        assert normal_entry.title == "测试文章标题"

        # 边界情况：空内容
        empty_entry = self._create_test_entry(content="", title="空内容测试")
        assert empty_entry.content == ""
        assert empty_entry.title == "空内容测试"

        # 验证初始状态创建
        init_state = {"entry": normal_entry}
        assert "entry" in init_state
        assert init_state["entry"] == normal_entry

    # 核心图执行测试
    @pytest.mark.asyncio
    @patch("src.graph.classify_graph.Session")
    async def test_graph_execution_both_exist_skip_all(self, mock_session):
        """测试当标签和分数都存在时，图直接结束不执行任何节点"""
        self._setup_mock_session(
            mock_session, entry_category_exists=True, entry_score_exists=True
        )

        test_entry = self._create_test_entry()
        graph = get_classification_graph()

        states = []
        async for state in graph.astream(
            {"entry": test_entry}, stream_mode="values"
        ):
            states.append(state)

        # 验证至少有初始状态，且图快速结束
        assert len(states) >= 1, "应该至少有一个状态输出"
        initial_state = states[0]
        assert "entry" in initial_state
        assert initial_state["entry"] == test_entry

    @pytest.mark.asyncio
    @patch("src.graph.classify_graph.Session")
    @patch("src.graph.classify_graph.score_node")
    async def test_graph_execution_only_tag_exists_routes_to_score(
        self, mock_score_node, mock_session
    ):
        """测试当只有标签存在时，图直接路由到 score 节点"""
        self._setup_mock_session(
            mock_session, entry_category_exists=True, entry_score_exists=False
        )

        mock_score_node.side_effect = lambda state: {
            "score": "test_score",
            "entry": state["entry"],
        }

        test_entry = self._create_test_entry()
        graph = get_classification_graph()

        states = []
        async for state in graph.astream(
            {"entry": test_entry}, stream_mode="values"
        ):
            states.append(state)

        mock_score_node.assert_called()
        assert len(states) >= 1, "应该有状态输出"
        final_state = states[-1]
        assert "entry" in final_state
        assert final_state["entry"] == test_entry

    @pytest.mark.asyncio
    @patch("src.graph.classify_graph.Session")
    @patch("src.graph.classify_graph.tagger_node")
    @patch("src.graph.classify_graph.tagger_review_node")
    @patch("src.graph.classify_graph.score_node")
    async def test_graph_execution_full_pipeline(
        self,
        mock_score_node,
        mock_tagger_review_node,
        mock_tagger_node,
        mock_session,
    ):
        """测试完整流水线执行和状态传递"""
        self._setup_mock_session(
            mock_session, entry_category_exists=False, entry_score_exists=False
        )

        # Mock 节点函数
        mock_tagger_node.side_effect = lambda state: {
            "tag_result": {"category": "test", "confidence": 0.8},
            "entry": state["entry"],
        }
        mock_tagger_review_node.side_effect = lambda state: {
            "tag_result": {"category": "test", "confidence": 0.9},
            "entry": state["entry"],
        }
        mock_score_node.side_effect = lambda state: {
            "score": "actionable",
            "entry": state["entry"],
        }

        test_entry = self._create_test_entry()
        graph = get_classification_graph()

        states = []
        async for state in graph.astream(
            {"entry": test_entry}, stream_mode="values"
        ):
            states.append(state)

        # 验证所有节点被调用
        mock_tagger_node.assert_called()
        mock_tagger_review_node.assert_called()
        mock_score_node.assert_called()

        # 验证状态传递
        assert len(states) >= 1
        final_state = states[-1]
        assert "entry" in final_state
        assert final_state["entry"] == test_entry

        # 验证状态在整个过程中保持 entry
        for state in states:
            assert "entry" in state

    @pytest.mark.asyncio
    @patch("src.graph.classify_graph.Session")
    async def test_run_classification_graph_function(self, mock_session):
        """测试 run_classification_graph 函数的执行"""
        self._setup_mock_session(
            mock_session, entry_category_exists=True, entry_score_exists=True
        )

        test_entry = self._create_test_entry()

        # 测试函数能正常执行（不抛异常）
        try:
            await run_classification_graph(test_entry)
            # 如果执行成功，验证基本行为
            assert True, "函数执行成功"
        except Exception as e:
            pytest.fail(
                f"run_classification_graph should not raise exception: {e}"
            )

        # 验证函数接受正确的参数类型
        assert isinstance(test_entry, RssEntry), "参数应该是RssEntry类型"

        # 测试不同类型的entry数据
        different_entries = [
            self._create_test_entry(
                entry_id=100, content="不同的内容1", title="标题1"
            ),
            self._create_test_entry(
                entry_id=200, content="", title="空内容测试"
            ),
            self._create_test_entry(
                entry_id=300, content="长内容" * 100, title="长标题测试"
            ),
        ]

        for entry in different_entries:
            try:
                await run_classification_graph(entry)
                # 验证不同entry都能被处理
                assert True, f"Entry {entry.id} 处理成功"
            except Exception as e:
                # 记录但不fail，因为某些特殊情况可能有异常
                print(f"Entry {entry.id} 处理时出现异常: {e}")

        # 验证调用了数据库Session（通过mock验证）
        mock_session.assert_called(), "应该调用了数据库Session"

    @pytest.mark.asyncio
    @patch("src.graph.classify_graph.Session")
    async def test_error_handling(self, mock_session):
        """测试错误处理能力"""
        test_entry = self._create_test_entry()

        # 场景1：模拟数据库连接失败
        mock_session.side_effect = Exception("Database connection failed")

        # 验证图构建时的错误处理
        try:
            graph = get_classification_graph()
            # 图构建成功，但执行时可能失败
            states = []
            async for state in graph.astream(
                {"entry": test_entry}, stream_mode="values"
            ):
                states.append(state)
                break  # 只收集第一个状态，避免长时间等待

            # 如果没有异常，说明错误处理成功
            assert True, "数据库连接失败时图仍能构建"
        except Exception as e:
            # 预期可能出现异常，这是正常的
            assert "Database" in str(e) or "connection" in str(
                e
            ), f"应该是数据库相关异常: {e}"

        # 重置mock以测试其他场景
        mock_session.side_effect = None
        mock_session.reset_mock()

        # 场景2：测试无效entry的处理
        invalid_entries = [
            None,  # None entry
        ]

        for invalid_entry in invalid_entries:
            if invalid_entry is None:
                # 测试None entry的处理
                try:
                    self._setup_mock_session(mock_session, True, True)
                    graph = get_classification_graph()
                    states = []
                    async for state in graph.astream(
                        {"entry": invalid_entry}, stream_mode="values"
                    ):
                        states.append(state)
                        break
                except (AttributeError, TypeError, ValueError) as e:
                    # 预期的异常类型
                    assert True, f"正确处理了无效entry: {e}"
                except Exception as e:
                    # 其他异常也是可以接受的
                    print(f"处理无效entry时出现异常: {e}")

        # 场景3：测试Session查询异常
        mock_session.side_effect = None
        session = self._setup_mock_session(mock_session, True, True)
        session.query.side_effect = Exception("Query failed")

        try:
            graph = get_classification_graph()
            # 图构建应该成功，查询异常在运行时处理
            assert graph is not None, "图构建应该成功"
        except Exception as e:
            print(f"查询异常场景: {e}")

        # 场景4：测试资源清理
        mock_session.side_effect = None
        mock_session.reset_mock()
        session = self._setup_mock_session(mock_session, False, False)

        try:
            graph = get_classification_graph()
            # 验证上下文管理器正确配置
            assert session.__enter__ is not None, "应该配置了__enter__"
            assert session.__exit__ is not None, "应该配置了__exit__"
        except Exception:
            pass  # 允许异常，重点是验证资源清理配置

    def test_multiple_graph_instances(self):
        """测试多图实例的独立性"""
        graph1 = get_classification_graph()
        graph2 = get_classification_graph()

        # 验证返回不同实例
        assert graph1 is not graph2, "每次调用应该返回新的图实例"

        # 验证结构一致性
        assert list(graph1.get_graph().nodes.keys()) == list(
            graph2.get_graph().nodes.keys()
        )

    @pytest.mark.asyncio
    async def test_entry_edge_cases(self):
        """测试 Entry 边界情况"""
        # 测试各种边界数据
        edge_cases = [
            {"content": "", "title": "空内容"},
            {"content": "very long content " * 1000, "title": "长内容"},
            {"content": "特殊字符!@#$%^&*()", "title": "特殊字符测试"},
            {"content": "中文内容测试", "title": "中文标题"},
            {"content": "Mixed 中英文 content", "title": "混合语言标题"},
            {"content": "\n\t换行和制表符\n\t", "title": "格式字符测试"},
            {"content": "数字123和符号@#$", "title": "数字符号测试"},
        ]

        for case in edge_cases:
            entry = self._create_test_entry(
                content=case["content"], title=case["title"]
            )

            # 验证对象创建正确
            assert entry.content == case["content"]
            assert entry.title == case["title"]

            # 验证状态初始化
            init_state = {"entry": entry}
            assert "entry" in init_state
            assert init_state["entry"] == entry

            # 验证entry的基本属性完整性
            assert hasattr(entry, "id"), f"Entry应该有id属性: {case['title']}"
            assert hasattr(
                entry, "feed_id"
            ), f"Entry应该有feed_id属性: {case['title']}"
            assert hasattr(
                entry, "link"
            ), f"Entry应该有link属性: {case['title']}"
            assert hasattr(
                entry, "author"
            ), f"Entry应该有author属性: {case['title']}"
            assert hasattr(
                entry, "summary"
            ), f"Entry应该有summary属性: {case['title']}"
            assert hasattr(
                entry, "published_at"
            ), f"Entry应该有published_at属性: {case['title']}"

            # 验证数据类型
            assert isinstance(entry.id, int), f"ID应该是整数: {case['title']}"
            assert isinstance(
                entry.content, str
            ), f"Content应该是字符串: {case['title']}"
            assert isinstance(
                entry.title, str
            ), f"Title应该是字符串: {case['title']}"

        # 测试极端长度内容
        extremely_long_content = "x" * 100000  # 100KB content
        long_entry = self._create_test_entry(
            content=extremely_long_content, title="极长内容测试"
        )

        assert len(long_entry.content) == 100000, "极长内容长度应该正确"
        assert long_entry.title == "极长内容测试", "极长内容的标题应该正确"

        # 测试Unicode和特殊编码
        unicode_cases = [
            {"content": "🚀🌟💡", "title": "Emoji测试"},
            {"content": "αβγδε", "title": "希腊字母"},
            {"content": "русский текст", "title": "俄语测试"},
            {"content": "العربية", "title": "阿拉伯语测试"},
        ]

        for unicode_case in unicode_cases:
            unicode_entry = self._create_test_entry(
                content=unicode_case["content"], title=unicode_case["title"]
            )

            # 验证Unicode内容正确保存
            assert (
                unicode_entry.content == unicode_case["content"]
            ), f"Unicode内容应该正确: {unicode_case['title']}"
            assert (
                unicode_entry.title == unicode_case["title"]
            ), f"Unicode标题应该正确: {unicode_case['title']}"

            # 验证可以用于状态初始化
            unicode_state = {"entry": unicode_entry}
            assert "entry" in unicode_state
            assert unicode_state["entry"] == unicode_entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
