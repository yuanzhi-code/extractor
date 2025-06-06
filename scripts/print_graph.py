from src.graph.classify_graph import get_classification_graph


def main():
    graph = get_classification_graph()
    mermaid_string = graph.get_graph().draw_mermaid()
    print(mermaid_string)


if __name__ == "__main__":
    main()
