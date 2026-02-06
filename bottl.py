import asyncio
import subprocess
import re
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest

# --- THÔNG TIN CHIẾN LƯỢC ---
TOKEN = '8589862869:AAExkuni4vIqw74yL6KWYnm5nvkfJvJNxjA'
BOSS_USER_ID = 7934171537    
API_KEY_LINK4M = "6981ed41aa416431716126eb"
MY_COOKIE = "PH5SESSID=48b49bfe3f518c4b2c3934635788dec2"
THUMB_IMAGE = "https://link4m.com/templates/default/IteckTheme/assets/img/thumb.jpg"

# Lưu tạm 5 link gần nhất vào bộ nhớ (đề phòng Boss xóa tin nhắn)
history_log = []

async def is_boss(update: Update):
    return update.effective_user.id == BOSS_USER_ID

def get_link_pro(url_goc):
    """Xử lý tạo link và bóc tách mã xóa một cách chuyên nghiệp"""
    # Bước 1: Làm sạch link gốc
    url_goc = url_goc.strip()
    if not url_goc.startswith("http"):
        url_goc = "https://" + url_goc
        
    target_url = f"https://link4m.co/st?api={API_KEY_LINK4M}&url={url_goc}"
    
    # Bước 2: Gửi lệnh với User-Agent giả lập trình duyệt cao cấp
    cmd = [
        'curl', '-s', '-k', '-L',
        '--connect-timeout', '30',
        '--cookie', MY_COOKIE,
        '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        target_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8').stdout
        # Tìm link rút gọn (Ưu tiên link4m.co/st/...)
        links = re.findall(r'https?://link4m\.[^\s<>"]+', result)
        
        final_link = None
        for l in links:
            if "/st/" in l:
                final_link = l
                break
        
        if final_link:
            alias = final_link.split('/')[-1]
            return final_link, alias, url_goc
    except:
        pass
    return None, None, url_goc

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_boss(update): return
    
    text = update.message.text.strip()
    # Nếu là tin nhắn text bình thường (không phải lệnh) thì mới xử lý tạo link
    if text.startswith('/'): return

    status = await context.bot.send_message(chat_id=BOSS_USER_ID, text="⚡ **Đang khởi tạo liên kết an toàn...**")

    loop = asyncio.get_event_loop()
    final_link, alias, clean_url = await loop.run_in_executor(None, get_link_pro, text)

    if final_link:
        # Lưu vào lịch sử
        history_log.append({"goc": clean_url, "rut": final_link, "alias": alias})
        if len(history_log) > 5: history_log.pop(0)

        msg = (
            f"💎 **KẾT QUẢ HOÀN TẤT**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔗 **LINK GỐC:**\n`{clean_url}`\n\n"
            f"🚀 **LINK RÚT GỌN:**\n`{final_link}`\n\n"
            f"🗑 **MÃ XÓA NHANH:** `{alias}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Mẹo: Gõ* `/xoa {alias}` *để hủy link này.*"
        )
        await context.bot.send_photo(
            chat_id=BOSS_USER_ID,
            photo=THUMB_IMAGE,
            caption=msg,
            parse_mode=ParseMode.MARKDOWN
        )
        await status.delete()
    else:
        await status.edit_text("⚠️ **Lỗi hệ thống:** Không thể tạo link. Boss hãy kiểm tra lại Cookie hoặc API Key ngay!")

async def delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_boss(update): return
    if not context.args:
        await update.message.reply_text("❌ Boss ơi, thiếu mã rồi. Gõ: `/xoa ABCXYZ` nhé!")
        return

    codes = context.args
    success_count = 0
    
    for code in codes:
        # Gửi lệnh xóa trực tiếp bằng Alias
        cmd = ['curl', '-s', '-X', 'POST', '--cookie', MY_COOKIE, f"https://link4m.com/member/links/delete/{code}"]
        subprocess.run(cmd)
        success_count += 1
        await asyncio.sleep(0.5)

    await context.bot.send_message(
        chat_id=BOSS_USER_ID, 
        text=f"🗑 **Đã hủy thành công:** `{success_count}` link.\n✨ Hệ thống đã sạch sẽ!"
    )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem lại 5 link vừa tạo đề phòng Boss lỡ tay xóa tin nhắn"""
    if not await is_boss(update): return
    if not history_log:
        await update.message.reply_text("📭 Lịch sử trống, Boss chưa tạo link nào.")
        return
    
    msg = "📜 **5 LINK VỪA TẠO GẦN ĐÂY:**\n\n"
    for i, item in enumerate(reversed(history_log), 1):
        msg += f"{i}. `{item['rut']}`\n   ↳ Gốc: `{item['goc'][:30]}...`\n   ↳ Mã xóa: `{item['alias']}`\n\n"
    
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_boss(update): return
    await update.message.reply_text("👑 **XIN CHÀO BOSS!**\n\nHệ thống đã nâng cấp toàn diện:\n1. Gửi link gốc -> Nhận link rút gọn + Mã xóa.\n2. Gõ `/xoa [mã]` -> Hủy link ngay lập tức.\n3. Gõ `/history` -> Xem lại link đã tạo.")

if __name__ == '__main__':
    # Cấu hình request cực mạnh chống lag
    t_request = HTTPXRequest(connect_timeout=60, read_timeout=60, write_timeout=60)
    app = Application.builder().token(TOKEN).request(t_request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("xoa", delete_links))
    app.add_handler(CommandHandler("history", show_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("Bot Siêu Cấp dành cho Boss đã sẵn sàng!")
    app.run_polling(drop_pending_updates=True)
