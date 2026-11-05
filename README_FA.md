# واسط سالمارک و نشان

این سرویس یک واسط HTTP برای ابزارهای عمومی و فقط‌خواندنی پروژه neshan-mcp است.

## استقرار
1. مخزن GitHub را به Render وصل کنید.
2. Web Service و پلن Free را انتخاب کنید.
3. در Environment متغیر SALMARK_TOKEN را با یک رمز طولانی و تصادفی تنظیم کنید.
4. Deploy را انجام دهید.

## مسیرها
- GET /health بررسی سلامت (بدون احراز هویت)
- GET /tools فهرست ابزارها و schema آن‌ها (با هدر Authorization)
- POST /call اجرای ابزار (با هدر Authorization)

هدر:
Authorization: Bearer YOUR_SALMARK_TOKEN

نمونه قالب درخواست:
{"tool":"ns_search","arguments":{}}

آرگومان واقعی را از خروجی /tools دریافت کنید. این پروژه غیررسمی است و ممکن است با تغییرات نشان از کار بیفتد؛ داده‌ها را پیش از استفاده تجاری بررسی کنید.
