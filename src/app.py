"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import re
import sys
from datetime import date, timedelta
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def extract_patient_name(user_query: str) -> str:
    match = re.search(r"tôi tên\s+([A-ZÀ-Ỵ][\wÀ-ỹ\-' ]+)", user_query, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(".,")
    return "Người dùng"


def extract_phone(user_query: str) -> str:
    match = re.search(r"\b0\d{9}\b", user_query)
    if match:
        return match.group(0)
    return ""


def extract_date_hint(user_query: str) -> str:
    normalized = _normalize(user_query)
    if "ngày mai" in normalized or "mai" in normalized:
        return "ngày mai"
    if "hôm nay" in normalized:
        return "hôm nay"
    match = re.search(r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})", normalized)
    if match:
        return match.group(1)
    return "ngày mai"


def extract_time_hint(user_query: str) -> str:
    match = re.search(r"\b(\d{1,2})(?::(\d{2})|h(\d{2})?)\b", user_query, flags=re.IGNORECASE)
    if not match:
        return ""
    hour = int(match.group(1))
    minute = match.group(2) or match.group(3) or "00"
    return f"{hour:02d}:{minute}"


def extract_specialty_from_text(text: str) -> str:
    match = re.search(r"Triệu chứng gợi ý chuyên khoa:\s*(.+)", text)
    if match:
        return match.group(1).splitlines()[0].strip()
    return "Nội tổng quát"


def extract_doctor_from_text(text: str) -> str:
    match = re.search(r"Bác sĩ phù hợp:\s*(.+)", text)
    if match:
        return match.group(1).splitlines()[0].strip()
    return ""


def extract_slot_from_text(text: str) -> str:
    match = re.search(r"Slot đề xuất:\s*(\d{2}:\d{2})", text)
    if match:
        return match.group(1)
    return ""


def classify_intent(user_query: str) -> str:
    normalized = _normalize(user_query)
    if any(keyword in normalized for keyword in ["đặt lịch", "chốt lịch", "hẹn khám", "đặt hẹn", "sđt"]):
        return "booking"
    if any(keyword in normalized for keyword in ["triệu chứng", "đau", "sốt", "chóng mặt", "khó thở", "ho", "đau bụng", "nghẹt mũi"]):
        return "triage"
    return "general"


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    intent = classify_intent(user_query)
    step = 0

    if intent == "general":
        print("🧠 Thought: Đây là câu hỏi sức khỏe chung, không cần gọi tool.")
        print("🏁 Final Answer: Bạn nên duy trì ăn uống điều độ, ngủ đủ giấc và đi khám khi triệu chứng kéo dài hoặc nặng lên.")
        return

    symptoms_obs = ""
    specialty = ""
    doctor_name = ""
    visit_date = extract_date_hint(user_query)
    preferred_time = extract_time_hint(user_query)
    patient_name = extract_patient_name(user_query)
    phone = extract_phone(user_query)

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        if step == 1:
            symptoms_text = user_query
            print("🧠 Thought: Tôi cần phân loại triệu chứng để xác định chuyên khoa phù hợp.")
            print(f"🛠️ Action: assess_symptoms['{symptoms_text}']")
            symptoms_obs = AVAILABLE_TOOLS["assess_symptoms"](symptoms_text)
            print(f"👁️ Observation: {symptoms_obs}")

            if symptoms_obs.startswith("LỖI:"):
                print("🏁 Final Answer: Tôi cần bạn mô tả triệu chứng rõ hơn để tư vấn chuyên khoa an toàn hơn.")
                return

            specialty = extract_specialty_from_text(symptoms_obs)
            if intent == "booking" and step < MAX_ITERATIONS:
                continue

            print("🧠 Thought: Tôi đã có chuyên khoa phù hợp và có thể gợi ý bác sĩ.")
            print(f"🛠️ Action: find_doctor['{specialty}', '']")
            doctor_obs = AVAILABLE_TOOLS["find_doctor"](specialty, "")
            print(f"👁️ Observation: {doctor_obs}")
            if doctor_obs.startswith("LỖI:"):
                print("🏁 Final Answer: Hiện tôi chưa tìm được bác sĩ phù hợp, bạn vui lòng cung cấp thêm triệu chứng hoặc cơ sở mong muốn.")
                return

            doctor_name = extract_doctor_from_text(doctor_obs)
            if intent == "triage":
                print(f"🏁 Final Answer: Triệu chứng của bạn gợi ý chuyên khoa {specialty}. Tôi đề xuất bác sĩ {doctor_name} để bạn đặt lịch sớm.")
                return

        if step == 2 and intent == "booking":
            print("🧠 Thought: Tôi đã có chuyên khoa, giờ cần chọn bác sĩ phù hợp.")
            print(f"🛠️ Action: find_doctor['{specialty}', '']")
            doctor_obs = AVAILABLE_TOOLS["find_doctor"](specialty, "")
            print(f"👁️ Observation: {doctor_obs}")
            if doctor_obs.startswith("LỖI:"):
                print("🏁 Final Answer: Hiện tôi chưa tìm được bác sĩ phù hợp, bạn vui lòng thử lại với mô tả triệu chứng cụ thể hơn.")
                return
            doctor_name = extract_doctor_from_text(doctor_obs)
            continue

        if step == 3 and intent == "booking":
            print("🧠 Thought: Tôi cần đề xuất lịch khám phù hợp theo ngày và giờ người dùng mong muốn.")
            print(f"🛠️ Action: suggest_schedule['{doctor_name}', '{visit_date}', '{preferred_time}']")
            schedule_obs = AVAILABLE_TOOLS["suggest_schedule"](doctor_name, visit_date, preferred_time)
            print(f"👁️ Observation: {schedule_obs}")
            if schedule_obs.startswith("LỖI:"):
                print("🛡️ GUARDRAIL TRIGGERED: Không có lịch hợp lệ để chốt. Dừng an toàn và yêu cầu người dùng đổi khung giờ/ngày khám.")
                return

            slot = extract_slot_from_text(schedule_obs)
            if not slot:
                print("🛡️ GUARDRAIL TRIGGERED: Không xác định được slot hợp lệ. Dừng an toàn.")
                return

            continue

        if step == 4 and intent == "booking":
            slot = extract_slot_from_text(AVAILABLE_TOOLS["suggest_schedule"](doctor_name, visit_date, preferred_time))
            print("🧠 Thought: Tôi đã đủ thông tin để chốt lịch khám.")
            print(f"🛠️ Action: confirm_booking['{doctor_name}', '{slot}', '{patient_name}', '{phone}', '{visit_date}']")
            booking_obs = AVAILABLE_TOOLS["confirm_booking"](doctor_name, slot, patient_name, phone, visit_date)
            print(f"👁️ Observation: {booking_obs}")
            if booking_obs.startswith("LỖI:"):
                print("🛡️ GUARDRAIL TRIGGERED: Không chốt được lịch do dữ liệu đầu vào chưa hợp lệ.")
                return
            print(f"🏁 Final Answer: {booking_obs}")
            return

    print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    for test_case in tests:
        print("\n==================================================")
        print(f"🧪 TEST CASE #{test_case['id']} - {test_case['category']}")
        print(f"❓ Câu hỏi: {test_case['question']}")
        print(f"🎯 Kỳ vọng: {test_case['expected_behavior']}")
        print("==================================================")

        print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
        run_baseline_chatbot(test_case["question"], provider)

        print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
        run_react_agent(test_case["question"], provider)
