# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 *Multi-step Reasoning* | 5/5 | Cần phân loại triệu chứng, chọn chuyên khoa, dò lịch trống và chốt lịch theo từng bước. |
| 🛠️ *Tool Interaction* | 5/5 | Cần tích hợp tool tư vấn triệu chứng, tìm bác sĩ, đề xuất lịch và xác nhận đặt lịch. |
| 🔀 *Dynamic Decision* | 4/5 | Lịch khám thay đổi theo ngày, giờ và dữ liệu đầu vào của người dùng. |
| ⏳ *Long Horizon* | 5/5 | Quy trình gồm nhiều bước nối tiếp: tư vấn triệu chứng, chọn bác sĩ, đề xuất lịch, chốt lịch. |
| *TỔNG ĐIỂM FIT* | *19/20* | *KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!* |

---


## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Thời tiết ở Hà Nội hôm nay thế nào và tôi nên mặc gì đi chơi?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Tôi không có truy cập Internet thời gian thực nên không biết thời tiết hôm nay ở Hà Nội."*
* **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế của người dùng.

### 🧠 ReAct Agent:
* **Thought 1**: Cần tra cứu thời tiết Hà Nội.
* **Action 1**: `get_weather['Hà Nội']`
* **Observation 1**: `Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%.`
* **Thought 2**: Đã có thông tin 28°C nắng nhẹ, đưa ra lời khuyên trang phục.
* **Final Answer**: *"Thời tiết Hà Nội hôm nay 28°C, nắng nhẹ. Bạn nên mặc quần áo thoáng mát!"*
* **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ sự kết hợp giữa suy luận và công cụ.

---
## 3. Các trường hợp tool có thể bị lỗi (Failure Modes)

| Bước | Trường hợp có thể lỗi | Lý do |
| :--- | :--- | :--- |
| *Tư vấn triệu chứng* | Người dùng mô tả quá mơ hồ, thiếu thời gian khởi phát hoặc mức độ triệu chứng | Tool khó suy luận đúng chuyên khoa nên dễ tư vấn sai hướng hoặc trả lời chung chung. |
| *Tư vấn triệu chứng* | Có dấu hiệu nguy hiểm như khó thở, đau ngực, ngất nhưng mô tả không rõ | Agent có thể bỏ sót mức độ khẩn cấp nếu không hỏi làm rõ trước khi đưa ra khuyến nghị. |
| *Chọn bác sĩ* | Không có bác sĩ đúng chuyên khoa trong catalog | Tool không tìm được ứng viên phù hợp, phải fallback sang gợi ý chuyên khoa gần nhất hoặc yêu cầu bổ sung thông tin. |
| *Chọn bác sĩ* | Dữ liệu bác sĩ thiếu chuyên khoa, cơ sở hoặc lịch trực | Agent khó đối chiếu tiêu chí chọn bác sĩ, dẫn tới chọn nhầm hoặc không chọn được bác sĩ nào. |
| *Đề xuất lịch* | Không có slot trống phù hợp với ngày/giờ người dùng mong muốn | Tool không thể đưa ra lịch hợp lệ, cần đề xuất khung giờ thay thế. |
| *Đề xuất lịch* | Lịch bác sĩ thay đổi đồng thời trong lúc tra cứu | Kết quả đề xuất có thể bị stale, khiến slot vừa gợi ý xong đã bị người khác đặt mất. |
| *Chốt lịch* | Người dùng đổi ý ở bước xác nhận cuối | Tool cần dừng thao tác đặt lịch, nếu không sẽ tạo booking ngoài ý muốn của người dùng. |
| *Chốt lịch* | API đặt lịch lỗi, timeout hoặc trả về trạng thái không rõ ràng | Agent không biết lịch đã được tạo thành công hay chưa, dễ gây đặt trùng hoặc bỏ lỡ xác nhận. |
| *Chốt lịch* | Thông tin đầu vào không hợp lệ, ví dụ sai ngày giờ hoặc thiếu số điện thoại | Hệ thống không thể tạo booking hợp lệ và phải yêu cầu người dùng cung cấp lại dữ liệu. |
