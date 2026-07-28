"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo các công cụ cho bài toán đặt lịch khám bệnh và tư vấn chuyên khoa.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta

DOCTOR_CATALOG = [
    {
        "name": "BS Nguyễn Văn A",
        "specialty": "Thần kinh",
        "location": "Bệnh viện Đại học VinUni",
        "slots": {
            "2026-07-29": ["09:00", "14:00"],
            "2026-07-30": ["10:30"],
        },
    },
    {
        "name": "BS Trần Thị B",
        "specialty": "Nội tổng quát",
        "location": "Phòng khám VinCare",
        "slots": {
            "2026-07-29": ["08:30", "13:30"],
            "2026-07-30": ["09:30"],
        },
    },
    {
        "name": "BS Lê Minh C",
        "specialty": "Tiêu hóa",
        "location": "Bệnh viện VinHealth",
        "slots": {
            "2026-07-29": ["11:00"],
            "2026-07-30": ["15:00", "16:30"],
        },
    },
    {
        "name": "BS Phạm Thu D",
        "specialty": "Tai Mũi Họng",
        "location": "Phòng khám VinCare",
        "slots": {
            "2026-07-29": ["10:00", "15:30"],
            "2026-07-30": ["09:00"],
        },
    },
]

SPECIALTY_KEYWORDS = {
    "Thần kinh": ["đau đầu", "chóng mặt", "tê tay", "mất ngủ", "hoa mắt"],
    "Tiêu hóa": ["đau bụng", "ợ nóng", "buồn nôn", "tiêu chảy", "khó tiêu"],
    "Tai Mũi Họng": ["đau họng", "nghẹt mũi", "viêm xoang", "ù tai", "ho khan"],
    "Nội tổng quát": ["sốt", "mệt", "yếu", "kiệt sức", "khám tổng quát"],
}


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _parse_date_hint(preferred_date: str) -> str:
    normalized = _normalize(preferred_date)
    today = date(2026, 7, 28)

    if normalized in {"ngày mai", "mai", "tomorrow"}:
        return (today + timedelta(days=1)).isoformat()
    if normalized in {"hôm nay", "today"}:
        return today.isoformat()

    match = re.search(r"(\d{4}-\d{2}-\d{2})", normalized)
    if match:
        return match.group(1)

    return preferred_date.strip()


def assess_symptoms(symptoms: str) -> str:
    """
    Phân loại triệu chứng sơ bộ để đề xuất chuyên khoa phù hợp.

    Args:
        symptoms (str): Mô tả triệu chứng của người dùng.

    Returns:
        str: Kết quả phân loại chứa chuyên khoa đề xuất, mức độ và lý do.
    """
    symptoms_lower = _normalize(symptoms)
    if not symptoms_lower:
        return "LỖI: Thiếu mô tả triệu chứng, vui lòng cung cấp thêm thông tin."

    for specialty, keywords in SPECIALTY_KEYWORDS.items():
        if any(keyword in symptoms_lower for keyword in keywords):
            urgency = "Nên đi khám sớm trong 1-3 ngày tới" if specialty == "Thần kinh" else "Có thể đặt lịch trong tuần"
            return (
                f"Triệu chứng gợi ý chuyên khoa: {specialty}\n"
                f"Mức độ: {urgency}\n"
                f"Lý do: Khớp với cụm dấu hiệu '{specialty.lower()}' trong mô tả của người dùng."
            )

    if any(keyword in symptoms_lower for keyword in ["khó thở", "đau ngực", "ngất"]):
        return (
            "Triệu chứng gợi ý chuyên khoa: Cấp cứu / Nội tổng quát\n"
            "Mức độ: Cần đánh giá y tế ngay\n"
            "Lý do: Có dấu hiệu cảnh báo cần kiểm tra khẩn cấp."
        )

    return (
        "Triệu chứng gợi ý chuyên khoa: Nội tổng quát\n"
        "Mức độ: Cần hỏi thêm chi tiết trước khi chốt chuyên khoa\n"
        "Lý do: Mô tả còn chung chung, chưa đủ tín hiệu để phân loại sâu hơn."
    )


def find_doctor(specialty: str, preferred_location: str = "") -> str:
    """
    Tìm bác sĩ phù hợp theo chuyên khoa và vị trí mong muốn.

    Args:
        specialty (str): Chuyên khoa cần tìm.
        preferred_location (str): Khu vực hoặc cơ sở khám mong muốn.

    Returns:
        str: Kết quả gợi ý bác sĩ phù hợp hoặc thông báo lỗi.
    """
    specialty_lower = _normalize(specialty)
    preferred_location_lower = _normalize(preferred_location)

    candidates = [doctor for doctor in DOCTOR_CATALOG if _normalize(doctor["specialty"]) == specialty_lower]
    if not candidates:
        return f"LỖI: Không tìm thấy bác sĩ cho chuyên khoa '{specialty}'."

    chosen = candidates[0]
    if preferred_location_lower:
        matching = [doctor for doctor in candidates if preferred_location_lower in _normalize(doctor["location"])]
        if matching:
            chosen = matching[0]

    return (
        f"Bác sĩ phù hợp: {chosen['name']}\n"
        f"Chuyên khoa: {chosen['specialty']}\n"
        f"Cơ sở: {chosen['location']}"
    )


def suggest_schedule(doctor_name: str, preferred_date: str, preferred_time: str = "") -> str:
    """
    Đề xuất khung giờ khám phù hợp theo lịch bác sĩ.

    Args:
        doctor_name (str): Tên bác sĩ.
        preferred_date (str): Ngày mong muốn khám.
        preferred_time (str): Giờ mong muốn khám (nếu có).

    Returns:
        str: Lịch trống và slot đề xuất, hoặc lỗi hợp lệ.
    """
    normalized_doctor = _normalize(doctor_name)
    selected_doctor = None
    for doctor in DOCTOR_CATALOG:
        if _normalize(doctor["name"]) == normalized_doctor:
            selected_doctor = doctor
            break

    if selected_doctor is None:
        return f"LỖI: Không tìm thấy bác sĩ '{doctor_name}'."

    date_key = _parse_date_hint(preferred_date)
    slots = selected_doctor["slots"].get(date_key)
    if not slots:
        return f"LỖI: Bác sĩ {selected_doctor['name']} không có lịch trống vào ngày {date_key}."

    slot_choice = slots[0]
    if preferred_time:
        normalized_time = preferred_time.strip()
        matching_times = [slot for slot in slots if slot == normalized_time]
        if matching_times:
            slot_choice = matching_times[0]

    return (
        f"Lịch khám khả dụng cho {selected_doctor['name']}:\n"
        f"Ngày: {date_key}\n"
        f"Các khung giờ: {', '.join(slots)}\n"
        f"Slot đề xuất: {slot_choice}"
    )


def confirm_booking(doctor_name: str, slot: str, patient_name: str, phone: str, visit_date: str) -> str:
    """
    Chốt lịch khám sau khi người dùng xác nhận thông tin.

    Args:
        doctor_name (str): Tên bác sĩ.
        slot (str): Khung giờ đã chọn.
        patient_name (str): Tên người khám.
        phone (str): Số điện thoại liên hệ.
        visit_date (str): Ngày khám.

    Returns:
        str: Mã đặt lịch và thông tin xác nhận, hoặc lỗi hợp lệ.
    """
    normalized_phone = re.sub(r"\D", "", phone or "")
    if not patient_name.strip():
        return "LỖI: Thiếu tên người khám."
    if len(normalized_phone) < 10:
        return "LỖI: Số điện thoại không hợp lệ."
    if not slot.strip():
        return "LỖI: Thiếu khung giờ đặt lịch."

    normalized_doctor = _normalize(doctor_name)
    selected_doctor = None
    for doctor in DOCTOR_CATALOG:
        if _normalize(doctor["name"]) == normalized_doctor:
            selected_doctor = doctor
            break

    if selected_doctor is None:
        return f"LỖI: Không tìm thấy bác sĩ '{doctor_name}' để chốt lịch."

    date_key = _parse_date_hint(visit_date)
    available_slots = selected_doctor["slots"].get(date_key, [])
    if slot not in available_slots:
        return f"LỖI: Khung giờ {slot} không còn khả dụng vào ngày {date_key}."

    booking_seed = f"{selected_doctor['name']}|{date_key}|{slot}|{patient_name}|{normalized_phone}"
    booking_code = hashlib.sha1(booking_seed.encode("utf-8")).hexdigest()[:8].upper()

    return (
        "Đã chốt lịch thành công.\n"
        f"Mã đặt lịch: BK-{booking_code}\n"
        f"Người khám: {patient_name}\n"
        f"Bác sĩ: {selected_doctor['name']} ({selected_doctor['specialty']})\n"
        f"Cơ sở: {selected_doctor['location']}\n"
        f"Thời gian: {date_key} {slot}\n"
        f"Số điện thoại: {normalized_phone}"
    )


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "assess_symptoms": assess_symptoms,
    "find_doctor": find_doctor,
    "suggest_schedule": suggest_schedule,
    "confirm_booking": confirm_booking,
}
