import asyncio
import os
import re
from typing import Dict, Any, List

class LLMJudge:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        # Định nghĩa rubrics chi tiết cho các tiêu chí: Accuracy, Professionalism, Safety
        self.rubrics = {
            "accuracy": "Chấm điểm từ 1-5 dựa trên độ chính xác so với Ground Truth. 1: Sai hoàn toàn. 5: Chính xác hoàn hảo.",
            "tone": "Chấm điểm từ 1-5 dựa trên sự chuyên nghiệp của ngôn ngữ. 1: Thô lỗ/không phù hợp. 5: Rất chuyên nghiệp."
        }

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        EXPERT TASK: Gọi ít nhất 2 model (ví dụ GPT-4o và Claude).
        Tính toán sự sai lệch. Nếu lệch > 1 điểm, cần logic xử lý.
        """
        prompt = (f"Question: {question}\n"
                  f"Ground Truth: {ground_truth}\n"
                  f"Answer: {answer}\n\n"
                  f"Rate the answer from 1 to 5 based on accuracy compared to the ground truth. "
                  f"Output ONLY an integer between 1 and 5.")

        async def get_openai_score(model_name="gpt-4o") -> int:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                content = response.choices[0].message.content.strip()
                match = re.search(r'\d+', content)
                return int(match.group()) if match else 3
            except Exception as e:
                print(f"OpenAI error: {e}")
                return 3
        
        async def get_claude_score() -> int:
            try:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=10,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                content = response.content[0].text.strip()
                match = re.search(r'\d+', content)
                return int(match.group()) if match else 3
            except Exception as e:
                print(f"Claude error: {e}")
                return 3

        # Call both GPT-4o and Claude concurrently
        score_a, score_b = await asyncio.gather(
            get_openai_score("gpt-4o"), 
            get_claude_score()
        )
        
        individual_scores = {"gpt-4o": score_a, "claude-3-5": score_b}
        
        # Conflict resolution logic: if difference is > 1
        if abs(score_a - score_b) > 1:
            score_c = await get_openai_score("gpt-4-turbo") # third judge
            individual_scores["gpt-4-turbo (tie-breaker)"] = score_c
            final_score = (score_a + score_b + score_c) / 3.0
        else:
            final_score = (score_a + score_b) / 2.0

        agreement = 1.0 if score_a == score_b else (0.5 if abs(score_a - score_b) == 1 else 0.0)
        
        return {
            "final_score": final_score,
            "agreement_rate": agreement,
            "individual_scores": individual_scores
        }

    async def check_position_bias(self, response_a: str, response_b: str, question: str = "", ground_truth: str = "") -> Dict[str, Any]:
        """
        Nâng cao: Thực hiện đổi chỗ response A và B để xem Judge có thiên vị vị trí không.
        """
        prompt_forward = (f"Question: {question}\n"
                          f"Ground Truth: {ground_truth}\n"
                          f"Response A: {response_a}\n"
                          f"Response B: {response_b}\n\n"
                          f"Which response is better? Output ONLY 'A' or 'B'.")
                          
        prompt_backward = (f"Question: {question}\n"
                           f"Ground Truth: {ground_truth}\n"
                           f"Response A: {response_b}\n"
                           f"Response B: {response_a}\n\n"
                           f"Which response is better? Output ONLY 'A' or 'B'.")
        
        async def ask_judge(prompt: str) -> str:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=10
                )
                content = response.choices[0].message.content.strip().upper()
                if "A" in content and "B" not in content:
                    return "A"
                elif "B" in content and "A" not in content:
                    return "B"
                return "A" if "A" in content else "B"
            except Exception:
                return "A"
        
        pref_forward, pref_backward = await asyncio.gather(
            ask_judge(prompt_forward), 
            ask_judge(prompt_backward)
        )
        
        # If pref_forward is 'A', judge picked response_a.
        # If pref_backward is 'B', judge picked response_a (which was at position B).
        bias_detected = False
        consistent = False
        
        if pref_forward == pref_backward:
            bias_detected = True # Chose the same position regardless of content
        else:
            consistent = True # Chose different positions, meaning it consistently chose the same actual response
            
        return {
            "forward_choice_position": pref_forward,
            "backward_choice_position": pref_backward,
            "bias_detected": bias_detected,
            "consistent": consistent
        }

    @staticmethod
    def calculate_cohens_kappa(scores_a: List[int], scores_b: List[int]) -> float:
        """
        Tính Cohen's Kappa thật dựa trên 2 danh sách điểm đánh giá để xem mức độ đồng thuận.
        """
        if not scores_a or len(scores_a) != len(scores_b):
            return 0.0
            
        n = len(scores_a)
        categories = list(set(scores_a + scores_b))
        
        # Observed agreement (Po)
        po = sum(1 for a, b in zip(scores_a, scores_b) if a == b) / n
        
        # Expected agreement (Pe)
        pe = 0.0
        for c in categories:
            prob_a = scores_a.count(c) / n
            prob_b = scores_b.count(c) / n
            pe += prob_a * prob_b
            
        if pe == 1.0:
            return 1.0
            
        kappa = (po - pe) / (1.0 - pe)
        return kappa

    @staticmethod
    def calculate_agreement_rate(scores_a: List[int], scores_b: List[int]) -> float:
        """
        Tính tỉ lệ đồng thuận tuyệt đối.
        """
        if not scores_a or len(scores_a) != len(scores_b):
            return 0.0
        return sum(1 for a, b in zip(scores_a, scores_b) if a == b) / len(scores_a)

if __name__ == "__main__":
    from dotenv import load_dotenv
    import json
    
    # Load environment variables from .env
    load_dotenv()
    
    async def run_tests():
        judge = LLMJudge()
        
        print("=== Testing evaluate_multi_judge ===")
        question = "What is the capital of France?"
        ground_truth = "The capital of France is Paris."
        answer = "Paris is the capital."
        
        print(f"Question: {question}\nAnswer: {answer}\nGround Truth: {ground_truth}\n")
        eval_result = await judge.evaluate_multi_judge(question, answer, ground_truth)
        print("Evaluation Result:", json.dumps(eval_result, indent=2))
        
        print("\n=== Testing check_position_bias ===")
        response_a = "Paris is the capital of France."
        response_b = "I am not sure, but I think it might be London."
        print(f"Response A: {response_a}\nResponse B: {response_b}\n")
        
        bias_result = await judge.check_position_bias(response_a, response_b, question, ground_truth)
        print("Bias Check Result:", json.dumps(bias_result, indent=2))
        
        print("\n=== Testing calculate_cohens_kappa ===")
        # Simulated scores from two judges
        scores_judge1 = [5, 4, 3, 5, 2]
        scores_judge2 = [5, 4, 4, 5, 1]
        
        kappa = LLMJudge.calculate_cohens_kappa(scores_judge1, scores_judge2)
        agreement = LLMJudge.calculate_agreement_rate(scores_judge1, scores_judge2)
        print(f"Scores 1: {scores_judge1}\nScores 2: {scores_judge2}")
        print(f"Cohen's Kappa: {kappa:.4f}")
        print(f"Agreement Rate: {agreement:.4f}")

    asyncio.run(run_tests())
