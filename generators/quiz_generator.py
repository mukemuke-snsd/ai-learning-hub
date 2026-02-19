"""测验生成器 - 统一测验（10道选择题）"""

import json
from datetime import date

from config.loader import load_settings, get_data_path
from generators.ai_engine import AIEngine
from tracker.database import Database


class QuizGenerator:
    """统一学习测验生成器 - 基于统一早报生成 10 道选择题"""

    def __init__(self, db: Database = None, module: str = "unified"):
        self.db = db or Database()
        self.ai = AIEngine()
        self.module = module
        self.settings = load_settings()
        learning_cfg = self.settings.get("learning", {})
        self.num_questions = learning_cfg.get("quiz_questions_per_day", 10)
        self.passing_score = learning_cfg.get("passing_score", 60)

    def generate_quiz(self, briefing_content: str,
                      target_date: str = None) -> dict:
        if not target_date:
            target_date = date.today().isoformat()

        system_prompt = """你是一位 AI 学习测评专家。根据提供的学习材料生成测验题目。

必须返回严格的 JSON 格式，结构如下：
{
    "quiz_title": "每日测验",
    "questions": [
        {
            "id": 1,
            "type": "multiple_choice",
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "correct_answer": "A",
            "explanation": "答案解析",
            "difficulty": "easy/medium/hard"
        }
    ]
}"""

        user_prompt = f"""根据以下今日学习简报内容，生成 {self.num_questions} 道选择题。

要求：
- 全部为四选一的选择题（A/B/C/D）
- 知识覆盖：
  - 3-4 题：GEO 核心概念与实践
  - 3-4 题：AI 论文技术趋势
  - 2-3 题：博主方法论与案例
- 难度分布：3 道简单、4 道中等、3 道困难
- 题目应测试对内容的真正理解，而非简单记忆
- 选项应具有一定干扰性，避免明显错误选项
- 所有内容使用中文

学习材料：
{briefing_content[:4000]}"""

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
            f"每题 10 分 | 及格分数：{self.passing_score} 分\n"
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

            for opt in q.get("options", []):
                lines.append(f"- {opt}")
            lines.append("")
            lines.append("---\n")

        return "\n".join(lines)

    def format_answers_for_display(self, quiz_data: dict) -> str:
        lines = ["# 答案与解析\n", "---\n"]

        for q in quiz_data.get("questions", []):
            q_id = q.get("id", "?")
            lines.append(f"### 第 {q_id} 题")
            lines.append(f"\n**题目：{q['question']}**\n")
            lines.append(f"**正确答案：{q.get('correct_answer', '?')}**\n")

            explanation = q.get("explanation", "")
            if explanation:
                lines.append(f"**解析：** {explanation}\n")
            lines.append("---\n")

        return "\n".join(lines)

    def evaluate_answers(self, quiz_data: dict, user_answers: dict) -> dict:
        questions = quiz_data.get("questions", [])
        total_score = 0
        max_score = len(questions) * 10
        results = []

        for q in questions:
            q_id = str(q.get("id", ""))
            user_answer = user_answers.get(q_id, "").strip()
            correct = q.get("correct_answer", "").strip().upper()
            is_correct = user_answer.upper() == correct

            result = {
                "question_id": q_id,
                "question": q["question"],
                "user_answer": user_answer,
                "correct": is_correct,
                "score": 10 if is_correct else 0,
                "max_score": 10,
                "feedback": (
                    "正确！" if is_correct
                    else f"错误。正确答案是 {correct}"
                ),
            }
            if q.get("explanation"):
                result["feedback"] += f"\n解析：{q['explanation']}"

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
                f"{'通过' if passed else '未通过'}"
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
