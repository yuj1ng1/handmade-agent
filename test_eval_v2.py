from langchain_rag import LangChainRag

def evaluate_recall(rag, eval_cases, top_k=2):
    hit_count = 0

    for case in eval_cases:
        question = case["question"]
        expected_section = case["expected_section"]

        documents = rag.retrieve_reranked(
            question,
            candidate_k=10,
            top_k=top_k
        )

        sections = []

        for document in documents:
            sections.append(
                document.metadata.get("section")
            )

        success = expected_section in sections

        if success:
            hit_count += 1

        print("问题：", question)
        print("期望章节：", expected_section)
        print("实际章节：", sections)
        print("是否命中：", success)
        print("------")

    recall = hit_count / len(eval_cases)

    print("Recall@", top_k, "=", recall)

    return recall

def judge_answerable(question,documents):
    if not documents:
        return False
    context=self.format_documents

test_questions = [
    # ====================
    # 1. 明确有答案
    # ====================
    {
        "question": "风险人群筛查怎么判断是否逗留？",
        "expected": True,
        "type": "positive"
    },
    {
        "question": "最大子数组和的实现思路是什么？",
        "expected": True,
        "type": "positive"
    },
    {
        "question": "瑞瑞木板为什么要使用优先队列？",
        "expected": True,
        "type": "positive"
    },
    {
        "question": "邻域均值为什么使用二维前缀和？",
        "expected": True,
        "type": "positive"
    },
    {
        "question": "相反数的时间复杂度是多少？",
        "expected": True,
        "type": "positive"
    },

    # ====================
    # 2. 明显无答案
    # ====================
    {
        "question": "Redis 主从复制怎么配置？",
        "expected": False,
        "type": "easy_negative"
    },
    {
        "question": "Docker Compose 怎么部署 MySQL？",
        "expected": False,
        "type": "easy_negative"
    },
    {
        "question": "FastAPI 怎么实现 JWT 登录认证？",
        "expected": False,
        "type": "easy_negative"
    },

    # ====================
    # 3. 困难负样本
    # ====================
    {
        "question": "风险人群筛查如何使用多线程提高运行速度？",
        "expected": False,
        "type": "hard_negative"
    },
    {
        "question": "最大子数组和怎么返回最大子数组的起点和终点？",
        "expected": False,
        "type": "hard_negative"
    },
    {
        "question": "瑞瑞木板能不能给出贪心算法最优性的严格数学证明？",
        "expected": False,
        "type": "hard_negative"
    },
    {
        "question": "邻域均值如何使用 CUDA 在 GPU 上加速？",
        "expected": False,
        "type": "hard_negative"
    },
    {
        "question": "相反数如何使用哈希表实现 O(N) 的完整代码？",
        "expected": False,
        "type": "hard_negative"
    },
    {
        "question": "稀疏向量如何使用 CSR 格式进行存储？",
        "expected": False,
        "type": "hard_negative"
    },
    {
        "question": "学生排队如何改成支持多人同时移动？",
        "expected": False,
        "type": "hard_negative"
    },
]

rag = LangChainRag()

for case in test_questions:
    question = case["question"]

    candidates = rag.retrieve_candidates(
        question,
        k=10
    )

    reranked = rag.rerank_documents(
        question,
        candidates
    )

    print("问题：", question)
    print("类型：", case["type"])
    print("预期有答案：", case["expected"])

    if reranked:
        best_document, best_score = reranked[0]

        print("Top1 score：", best_score)
        print(
            "Top1 section：",
            best_document.metadata.get("section")
        )
        print(
            "Top1 内容：",
            best_document.page_content[:150]
        )
    else:
        print("没有检索结果")

    print("------")