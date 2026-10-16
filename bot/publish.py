import os
import time
import requests
from supabase import create_client

# =========================================================
# CONFIG
# =========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
SITE_URL = os.getenv("SITE_URL")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# ارسال به تلگرام
# =========================================================
def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"❌ Error sending: {e}")
        return {"ok": False}


# =========================================================
# ساخت متن پیام
# =========================================================
def build_message(lesson, course):
    title = lesson.get("title", "")
    excerpt = lesson.get("excerpt", "") or ""
    slug = lesson.get("slug", "")
    duration = lesson.get("duration", "") or ""
    course_title = course.get("title", "") if course else ""

    # حذف HTML از excerpt
    excerpt = excerpt.replace("<", "&lt;").replace(">", "&gt;")

    # لینک به صفحه درس
    link = f"{SITE_URL}/lesson.html?slug={slug}"

    # ساخت پیام
    message = f"""📚 <b>{title}</b>

{course_title and f'📖 <i>{course_title}</i>' or ''}
{duration and f'⏱ {duration}' or ''}

{excerpt[:300]}{'...' if len(excerpt) > 300 else ''}

🔗 <a href="{link}">مطالعه‌ی کامل درس</a>"""

    return message.strip()


# =========================================================
# بررسی دروس جدید
# =========================================================
def check_new_lessons():
    # پست‌های منتشر شده که هنوز به تلگرام نرفتن
    response = (
        supabase.table("lessons")
        .select("*")
        .eq("status", "published")
        .eq("telegram_sent", False)
        .execute()
    )

    lessons = response.data
    if not lessons:
        print("📭 No new lessons")
        return

    print(f"📬 Found {len(lessons)} new lessons")

    for lesson in lessons:
        # گرفتن اطلاعات دوره
        course = None
        if lesson.get("course_id"):
            course_response = (
                supabase.table("courses")
                .select("title, slug")
                .eq("id", lesson["course_id"])
                .maybe_single()
                .execute()
            )
            course = course_response.data

        # ساخت پیام
        message = build_message(lesson, course)

        # ارسال
        print(f"📤 Sending: {lesson.get('title')}")
        result = send_to_telegram(message)

        if result.get("ok"):
            # علامت‌گذاری که فرستاده شد
            supabase.table("lessons").update({"telegram_sent": True}).eq(
                "id", lesson["id"]
            ).execute()
            print(f"✅ Sent: {lesson.get('title')}")
        else:
            print(f"❌ Failed: {result}")

        # تاخیر بین پیام‌ها
        time.sleep(2)


# =========================================================
# Main
# =========================================================
def main():
    print("🤖 Hamsafar Publisher started...")
    try:
        check_new_lessons()
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
