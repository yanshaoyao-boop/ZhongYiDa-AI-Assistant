import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.chat_intelligence import (  # noqa: E402
    build_document_search_query,
    build_document_clarification_message,
    build_document_source_footer,
    build_intent_clarification_message,
    infer_knowledge_category,
    rerank_similar_documents,
    should_ask_document_clarification,
    summarize_document_sources,
)


class ChatIntelligenceTestCase(unittest.TestCase):
    def test_build_document_search_query_uses_recent_context_for_short_followup(self):
        history = [
            {"role": "user", "content": "把公司的考勤制度发我看下"},
            {"role": "assistant", "content": "好的，我来帮你找。"},
        ]

        query = build_document_search_query(
            message="迟到呢",
            history=history,
            company_intro_keywords=["公司", "介绍", "简介"],
        )

        self.assertIn("考勤制度", query)
        self.assertIn("迟到呢", query)

    def test_build_document_search_query_expands_company_intro_short_prompt(self):
        query = build_document_search_query(
            message="介绍下你们公司",
            history=[],
            company_intro_keywords=["公司", "介绍", "简介"],
        )

        self.assertIn("介绍下你们公司", query)
        self.assertIn("公司简介", query)
        self.assertIn("核心业务", query)

    def test_build_document_search_query_expands_oral_company_culture_prompt(self):
        query = build_document_search_query(
            message="公司的企业文化最新的有吗",
            history=[],
            company_intro_keywords=["公司", "介绍", "简介"],
        )

        self.assertIn("完整企业文化", query)
        self.assertIn("当前生效", query)
        self.assertIn("使命", query)
        self.assertIn("愿景", query)
        self.assertIn("价值观", query)

    def test_build_document_search_query_expands_finance_info_without_order_sheet_noise(self):
        query = build_document_search_query(
            message="公司的银行账号多少",
            history=[],
            company_intro_keywords=["公司", "介绍", "简介"],
        )

        self.assertIn("银行账号", query)
        self.assertIn("开户银行", query)
        self.assertNotIn("下单表", query)

    def test_build_document_search_query_expands_warehouse_address_lookup(self):
        query = build_document_search_query(
            message="公司的仓库地址多少",
            history=[],
            company_intro_keywords=["公司", "介绍", "简介"],
        )

        self.assertIn("仓库地址", query)
        self.assertIn("海外仓地址", query)

    def test_rerank_similar_documents_promotes_keyword_hits(self):
        docs = [
            {
                "document": "仓库操作规范与打包流程",
                "metadata": {"source": "仓库SOP.docx"},
                "distance": 0.11,
            },
            {
                "document": "考勤制度中规定迟到三次需要提交说明，请假需提前申请。",
                "metadata": {"source": "考勤制度.docx"},
                "distance": 0.18,
            },
        ]

        reranked = rerank_similar_documents("考勤迟到规则", docs)

        self.assertEqual(reranked[0]["metadata"]["source"], "考勤制度.docx")

    def test_summarize_document_sources_deduplicates_and_limits(self):
        docs = [
            {"metadata": {"source": "考勤制度.docx"}},
            {"metadata": {"source": "考勤制度.docx"}},
            {"metadata": {"source": "请假流程.pdf"}},
            {"metadata": {"source": "客服话术手册.docx"}},
        ]

        summary = summarize_document_sources(docs, limit=2)

        self.assertEqual(summary, "考勤制度.docx、请假流程.pdf")

    def test_should_ask_document_clarification_for_ambiguous_short_message_without_context(self):
        self.assertTrue(
            should_ask_document_clarification(
                message="这个呢",
                history=[],
            )
        )

    def test_should_not_ask_document_clarification_when_recent_context_is_specific(self):
        history = [
            {"role": "user", "content": "考勤制度里迟到和请假分别怎么规定？"},
            {"role": "assistant", "content": "我来帮你查制度。"},
        ]

        self.assertFalse(
            should_ask_document_clarification(
                message="这个呢",
                history=history,
            )
        )

    def test_build_document_clarification_message_guides_user_to_add_topic(self):
        message = build_document_clarification_message()

        self.assertIn("补充一下你想查的主题", message)
        self.assertIn("制度", message)

    def test_build_document_source_footer_uses_summarized_sources(self):
        footer = build_document_source_footer(
            [
                {"metadata": {"source": "考勤制度.docx"}},
                {"metadata": {"source": "请假流程.pdf"}},
            ]
        )

        self.assertEqual(footer, "\n\n参考来源：考勤制度.docx、请假流程.pdf")

    def test_build_intent_clarification_message_for_quote_when_core_fields_missing(self):
        message = build_intent_clarification_message(
            intent="quote",
            message="报价多少",
            history=[],
        )

        self.assertIn("补充", message)
        self.assertIn("仓库", message)
        self.assertIn("重量", message)

    def test_build_intent_clarification_message_for_address_when_target_missing(self):
        message = build_intent_clarification_message(
            intent="address",
            message="偏远吗",
            history=[],
        )

        self.assertIn("邮编", message)
        self.assertIn("完整地址", message)

    def test_build_intent_clarification_message_skips_quote_when_key_fields_exist(self):
        message = build_intent_clarification_message(
            intent="quote",
            message="ONT8 100kg 报价多少",
            history=[],
        )

        self.assertEqual(message, "")

    def test_infer_knowledge_category_returns_admin_for_hr_queries(self):
        self.assertEqual(infer_knowledge_category("考勤制度和请假流程怎么规定"), "admin")

    def test_infer_knowledge_category_returns_admin_for_attendance_deduction_queries(self):
        self.assertEqual(
            infer_knowledge_category("我本月迟到4次，每次5分钟，累计20分钟无漏打卡，我要被扣多少钱"),
            "admin",
        )

    def test_infer_knowledge_category_returns_admin_for_person_role_lookup_queries(self):
        self.assertEqual(infer_knowledge_category("林楠楠是什么职位"), "admin")
        self.assertEqual(infer_knowledge_category("这个事情找谁对接"), "admin")

    def test_infer_knowledge_category_returns_admin_for_finance_info_queries(self):
        self.assertEqual(infer_knowledge_category("公司的银行账号多少"), "admin")

    def test_infer_knowledge_category_returns_admin_for_warehouse_address_queries(self):
        self.assertEqual(infer_knowledge_category("公司的仓库地址多少"), "admin")

    def test_infer_knowledge_category_returns_admin_for_company_culture_queries(self):
        self.assertEqual(infer_knowledge_category("公司的企业文化最新的有吗"), "admin")
        self.assertEqual(infer_knowledge_category("咱们公司的使命愿景价值观是什么"), "admin")

    def test_infer_knowledge_category_returns_biz_for_operation_queries(self):
        self.assertEqual(infer_knowledge_category("物流报价和仓库操作SOP"), "biz")

    def test_infer_knowledge_category_returns_none_for_generic_queries(self):
        self.assertIsNone(infer_knowledge_category("你能做什么"))


if __name__ == "__main__":
    unittest.main()
