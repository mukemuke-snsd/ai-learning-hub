"""测验生成器 - 多模块支持"""

import json
from datetime import date

from config.loader import load_settings, load_module_config, get_data_path
from generators.ai_engine import AIEngine
from tracker.database import Database

MODULE_QUIZ_CONTEXT = {
    "geo": "GEO（Generative Engine Optimization）",
    "ai_papers": "AI 前沿论文与技术趋势",
    "creators": "产品经理 AI 应用与方法论",
}


class QuizGenerator:
    """多模块学习测验生成器"""

    def __init__(self, db: Database = None, module: str = "geo"):
        self.db = db or Database()
        self.ai = AIEngine()
        self.module = module
        self.settings = load_settings()
        learning_cfg = self.settings.get("learning", {})
        self.num_questions = learning_cfg.get("quiz_questions_per_day", 5)
        self.passing_score = learning_cfg.get("passing_score", 60)

    def generate_quiz(self, briefing_content: str,
                      target_date: str = None) -> dict:
        if not target_date:
            target_date = date.today().isoformat()

        context = MODULE_QUIZ_CONTEXT.get(self.module, "AI 学习")

        system_prompt = f"""你是一位{context}学习测评专家。根据提供的学习材料生成测验题目。

必须返回严格的 JSON 格式，结构如下：
{{
    "quiz_title": "测验标题",
    "questions": [
        {{
            "id": 1,
            "type": "multiple_choice",
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "correct_answer": "A",
            "explanation": "答案解析",
            "difficulty": "easy/medium/hard"
        }},
        {{
            "id": 2,
            "type": "true_false",
            "question": "判断题内容",
            "correct_answer": "true",
            "explanation": "答案解析",
            "difficulty": "easy/medium/hard"
        }},
        {{
            "id": 3,
            "type": "short_answer",
            "question": "简答题内容",
            "reference_answer": "参考答案",
            "key_points": ["要点1", "要点2"],
            "difficulty": "medium/hard"
        }}
    ]
}}"""

        user_prompt = f"""根据以下今日学习简报内容，生成 {self.num_questions} 道测验题。

要求：
- 3道选择题（涵盖核心概念、实践应用、行业趋势）
- 1道判断题（测试常见误区）
- 1道简答题（考察深度理解和应用能力）
- 难度分布：1道简单、2道中等、2道困难
- 题目应该测试对内容的真正理解，而不是简单的记忆
- 所有内容使用中文

学习材料：
{briefing_content[:3000]}"""

        quiz_data = self.ai.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        if "error" not in quiz_data:
            quiz_json = json.dumps(quiz_data, ensure_ascii=False, indent=2)
            quiz_id = self.db.save_quiz(target_date, quiz_json, self.module)
            quiz_data["quiz_id"] = quiz_id
            self._save_to_file(target_date, quiz_data)

        return quiz_data

    def format_quiz_for_display(self, quiz_data: dict) -> str:
        lines = []
        title = quiz_data.get("quiz_title", "每日测验")
        lines.append(f"# {title}\n")
        lines.append(
            f"共 {len(quiz_data.get('questions', []))} 题 | "
            f"及格分数：{self.passing_score}分\n"
        )
        lines.append("---\n")

        for q in quiz_data.get("questions", []):
            q_id = q.get("id", "?")
            difficulty = q.get("difficulty", "medium")
            diff_emoji = {
                "easy": "🟢", "medium": "🟡", "hard": "🔴"
            }.get(difficulty, "⚪")

            lines.append(f"### 第 {q_id} 题 {diff_emoji} [{difficulty}]")
            lines.append(f"\n**{q['question']}**\n")

            q_type = q.get("type", "unknown")
            if q_type == "multiple_choice":
                for opt in q.get("options", []):
                    lines.append(f"- {opt}")
                lines.append("")
            elif q_type == "true_false":
                lines.append("- A. 正确（True）")
                lines.append("- B. 错误（False）")
                lines.append("")
            elif q_type == "short_answer":
                lines.append("*请写下你的答案：*\n")
                lines.append("```\n（在此作答）\n```\n")
            lines.append("---\n")

        return "\n".join(lines)

    def format_answers_for_display(self, quiz_data: dict) -> str:
        lines = ["# ✅ 答案与解析\n", "---\n"]

        for q in quiz_data.get("questions", []):
            q_id = q.get("id", "?")
            q_type = q.get("type", "unknown")
            lines.append(f"### 第 {q_id} 题")
            lines.append(f"\n**题目：{q['question']}**\n")

            if q_type == "multiple_choice":
                lines.append(
                    f"**正确答案：{q.get('correct_answer', '?')}**\n"
                )
            elif q_type == "true_false":
                ans = "正确" if q.get("correct_answer") == "true" else "错误"
                lines.append(f"**正确答案：{ans}**\n")
            elif q_type == "short_answer":
                lines.append(
                    f"**参考答案：**\n{q.get('reference_answer', '')}\n"
                )
                for kp in q.get("key_points", []):
                    lines.append(f"- {kp}")
                lines.append("")

            explanation = q.get("explanation", "")
            if explanation:
                lines.append(f"**解析：** {explanation}\n")
            lines.append("---\n")

        return "\n".join(lines)

    def evaluate_answers(self, quiz_data: dict, user_answers: dict) -> dict:
        questions = quiz_data.get("questions", [])
        total_score = 0
        max_score = len(questions) * 20
        results = []

        for q in questions:
            q_id = str(q.get("id", ""))
            q_type = q.get("type", "unknown")
            user_answer = user_answers.get(q_id, "").strip()

            result = {
                "question_id": q_id,
                "question": q["question"],
                "user_answer": user_answer,
                "correct": False,
                "score": 0,
                "max_score": 20,
                "feedback": "",
            }

            if q_type in ("multiple_choice", "true_false"):
                correct = q.get("correct_answer", "").strip().upper()
                is_correct = user_answer.upper() == correct
                result["correct"] = is_correct
                result["score"] = 20 if is_correct else 0
                result["feedback"] = (
                    "✅ 正确！" if is_correct
                    else f"❌ 错误。正确答案是 {correct}"
                )
                if q.get("explanation"):
                    result["feedback"] += f"\n解析：{q['explanation']}"
            elif q_type == "short_answer":
                score, feedback = self._evaluate_short_answer(q, user_answer)
                result["score"] = score
                result["correct"] = score >= 12
                result["feedback"] = feedback

            total_score += result["score"]
            results.append(result)

        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= self.passing_score

        evaluation = {
            "total_score": total_score,
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "passed": passed,
            "results": results,
            "summary": (
                f"得分：{total_score}/{max_score} ({percentage:.1f}%) - "
                f"{'✅ 通过' if passed else '❌ 未通过'}"
            ),
        }

        quiz_id = quiz_data.get("quiz_id")
        if quiz_id:
            self.db.save_quiz_result(
                quiz_id,
                json.dumps(evaluation, ensure_ascii=False),
                percentage,
            )

        return evaluation

    def _evaluate_short_answer(self, question: dict,
                                user_answer: str) -> tuple:
        if not user_answer:
            return 0, "❌ 未作答"

        system_prompt = """你是一位严格但公正的学习评分专家。
请评估学生的简答题回答。返回JSON格式：
{"score": 0-20, "feedback": "评价内容"}
score 评分标准：
- 18-20: 优秀，涵盖所有要点且有深度
- 14-17: 良好，涵盖大部分要点
- 10-13: 及格，基本理解但不够深入
- 5-9: 部分理解，遗漏关键要点
- 0-4: 未能正确回答"""

        user_prompt = (
            f"题目：{question['question']}\n"
            f"参考答案：{question.get('reference_answer', '')}\n"
            f"评分要点：{', '.join(question.get('key_points', []))}\n\n"
            f"学生回答：{user_answer}"
        )

        result = self.ai.generate_json(system_prompt, user_prompt)
        return result.get("score", 0), result.get("feedback", "评分失败")

    def _save_to_file(self, date_str: str, quiz_data: dict):
        quiz_dir = get_data_path("quizzes")
        month_dir = quiz_dir / self.module / date_str[:7]
        month_dir.mkdir(parents=True, exist_ok=True)

        quiz_md = self.format_quiz_for_display(quiz_data)
        (month_dir / f"quiz-{date_str}.md").write_text(
            quiz_md, encoding="utf-8"
        )

        answers_md = self.format_answers_for_display(quiz_data)
        (month_dir / f"answers-{date_str}.md").write_text(
            answers_md, encoding="utf-8"
        )
