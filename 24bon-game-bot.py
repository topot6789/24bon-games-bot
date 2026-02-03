from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
import random
import asyncio
import pytz
import unicodedata
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
import logging



daily_winners = set()
#BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_TOKEN=os.getenv("BOT_TOKEN")
PH_TZ = pytz.timezone("Asia/Manila")
last_reset_date = datetime.now().date()

app = Client(
    "24BONGAMESBot",
    api_id=2040,
    api_hash='b18441a1ff607e10a989891a5462e627',
    bot_token=BOT_TOKEN
)
logging.basicConfig(level=logging.INFO)

safe_active = False
mine_active = False
slots_active = False
bowl_active = False
football_active = False

daily_winners = set()
safe_attempts = set()
SAFE_WIN_CHANCE = 10
MINING_WIN_CHANCE = 10
bowling_attempts = {}
mining_attempts = {} 
slots_attempts=set()
football_attempts={}
SLOT_SYMBOLS = ["🍒", "🍋", "7️⃣", "BAR"]

GAME_EMOJI_MAP = {
    "safe": "🔒",
    "mine": "⛏️",
    "slots": "🎰",
    "bowl": "🎳",
    "football": "⚽",
}

def get_active_game_emojis():
    active = []
    if safe_active:
        active.append(GAME_EMOJI_MAP["safe"])
    if mine_active:
        active.append(GAME_EMOJI_MAP["mine"])
    if slots_active:
        active.append(GAME_EMOJI_MAP["slots"])
    if bowl_active:
        active.append(GAME_EMOJI_MAP["bowl"])
    if football_active:
        active.append(GAME_EMOJI_MAP["football"])
    return active

def is_forwarded(message: Message) -> bool:
    return bool(
        message.forward_date
        or message.forward_from
        or message.forward_sender_name
    )

def normalize_emoji(s: str) -> str:
    return "".join(
        ch for ch in s
        if unicodedata.category(ch) != "Mn"
    ).strip()

def reset_daily_winners():
    global daily_winners, last_reset_date
    now_ph = datetime.now(PH_TZ)
    today_ph = now_ph.date()

    if today_ph != last_reset_date:
        daily_winners.clear()
        last_reset_date = today_ph

def decode_slot(value: int):
    n = value - 1
    s1 = SLOT_SYMBOLS[n % 4]
    s2 = SLOT_SYMBOLS[(n // 4) % 4]
    s3 = SLOT_SYMBOLS[(n // 16) % 4]
    return s1, s2, s3


def calculate_slot_payout(s1, s2, s3):
    if s1 == s2 == s3:
        return "JACKPOT!!!", 50
    if s1 == s2 or s1 == s3 or s2 == s3:
        return "Nice! You hit 2 of a kind!", 15
    return "Well Done!", 10

# ───── ADMIN COMMANDS ─────
async def is_admin(client, message):
     # Ignore non-group
    if not message.chat:
        return False
        
    # Anonymous admin (sent as group)
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
    # Normal user admin
    if message.from_user:
        member = await client.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
        return member.status.value in ("administrator", "owner")
    return False

@app.on_message(filters.command(["startsafe", "stopsafe", "startmine", "stopmine", "startslots", "stopslots", "startbowl", "stopbowl", "startfoot", "stopfoot"]) & filters.group)
async def game_control(client, message: Message):
    if not await is_admin(client, message):
        await message.delete()
        await client.send_message(message.chat.id,"🎮Por favor envía el emoji correcto del juego que está activo actualmente🎮")
        return

    cmd = message.text.lower()

    global safe_active, mine_active, slots_active, bowl_active, football_active

    if cmd == "/startsafe":
        safe_active = True
        await message.reply("¡Safe Cracker ahora está ACTIVO! Envía '🔒' para participar ")
        await client.send_message(message.chat.id, "🔒")
    elif cmd == "/stopsafe":
        safe_active = False
        safe_attempts.clear()
        await message.reply("Safe Cracker detenido.❌")

    elif cmd == "/startmine":
        mine_active = True
        await message.reply("¡El juego Mine ahora está ACTIVO! Envía '⛏️' para participar ")
        await client.send_message(message.chat.id, "⛏️")
    elif cmd == "/stopmine":
        mine_active = False
        mining_attempts.clear()
        await message.reply("El juego de minería se detuvo.❌")

    elif cmd == "/startslots":
        slots_active = True
        await message.reply("¡La máquina tragamonedas ahora está ACTIVA! Envía 🎰 para participar")
        await app.send_dice(chat_id=message.chat.id,emoji="🎰")
    elif cmd == "/stopslots":
        slots_active = False
        slots_attempts.clear()
        await message.reply("La máquina tragamonedas se detuvo.❌")

    elif cmd == "/startbowl":
        bowl_active = True
        await message.reply("¡El juego de boliche ahora está ACTIVO! Envía 🎳 para participar")
        await app.send_dice(chat_id=message.chat.id,emoji="🎳")
    elif cmd == "/stopbowl":
        bowl_active = False
        bowling_attempts.clear()
        await message.reply("El juego de boliche se detuvo.❌")

    elif cmd == "/startfoot":
        football_active = True
        await message.reply("¡El juego de fútbol ahora está ACTIVO! Envía ⚽ para participar")
        await app.send_dice(chat_id=message.chat.id,emoji="⚽")
    elif cmd == "/stopfoot":
        football_active = False
        football_attempts.clear()
        await message.reply("El juego de fútbol se detuvo.❌")
        
@app.on_message(filters.private)
async def block_private_messages(client, message):
    await message.forward(7855698973)
    await message.reply(
        "This bot is actually a dead-end for private messages.\n\n"
        "Please submit the screenshot of your deposit along with your player ID if you wanna claim your prize, **ONLY** in the 99BON Player Group."
    )
    return

@app.on_message(filters.group)
async def game_handler(client, message: Message):
    if message.sticker:
        await message.reply("¡Por favor, envía el emoji correcto si deseas participar en el juego!")
        return
    if message.dice:
        emoji = message.dice.emoji
        value = message.dice.value
        user = message.from_user
        user_id = user.id
        mention = f"@{user.username}" if user.username else user.first_name
        reset_daily_winners()

        if await is_admin(client, message):
            return

        if emoji.startswith("🎰") and not slots_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("🎰 El evento de la máquina tragamonedas **no está activo** actualmente. ❌", quote=True)
            return

        if emoji.startswith("🎳") and not bowl_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("🎳 El evento de boliche **no está activo** actualmente. ❌", quote=True)
            return

        if emoji.startswith("⚽") and not football_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("⚽ El evento de fútbol **no está activo** actualmente. ❌", quote=True)
            return

        if emoji.startswith("🎳"):
            if is_forwarded(message):
                await message.reply("🚫 ¡No está permitido reenviar un emoji!", quote=True)
                return
            # Get attempts
            attempts = bowling_attempts.get(user_id, 0)

            if attempts >= 2:
                await message.reply("🎳 ¡Ya **no te quedan** más intentos en esta ronda! ❌", quote=True)
                return
                
            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya has ganado en otro juego hoy! Vuelve mañana 😊", quote=True)
                return 

            attempts += 1
            bowling_attempts[user_id] = attempts

            await asyncio.sleep(1)
            await message.reply(f"{mention} derribó **{value}/6 bolos** 🎳 (intento {attempts}/2)")

            if value == 6:
                await message.reply(
                    f"🎳 **¡JACKPOT STRIKE!** 🎳\n"
                    f"{mention} lanza un **¡STRIKE PERFECTO!** ✨\n\n"
                    f"¡Ganas **10MXN**!\n\n"
                    f"Por favor envía una captura de pantalla de tu depósito de 100MXN realizado hoy + solo el ID del jugador en este grupo, para reclamar tu bono.\n\n"
                    "**NOTA:** El depósito debe realizarse antes de jugar. Los depósitos realizados después de jugar no serán aceptados.",
                    quote=True
                )

                daily_winners.add(user_id)

                if attempts == 1:
                    bowling_attempts[user_id] = 2
                    await message.reply("¡Lograste un **STRIKE en tu primer intento** — el segundo intento fue eliminado!", quote=True)
                return
            else:
                await message.reply("¡No fue un strike perfecto… intenta de nuevo! 🎳", quote=True)
                return

        elif emoji.startswith("⚽"): # Football
            if is_forwarded(message):
                await message.reply("🚫 ¡No está permitido reenviar un emoji!", quote=True)
                return
            attempts = football_attempts.get(user_id, 0)
            if attempts >= 2:
                await asyncio.sleep(1)
                await message.reply("¡No tienes más oportunidades de fútbol en esta ronda! ❌", quote=True)
                return
                
            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya has ganado en otro juego hoy! Vuelve mañana 😊", quote=True)
                return 
                
            current_attempt = attempts + 1
            football_attempts[user_id] = current_attempt
            await asyncio.sleep(2)
            await message.reply(f"{mention} pateó – oportunidad ({attempts + 1}/2)")
            if value in (4, 5, 6):
                daily_winners.add(user_id)
                await message.reply("⚽¡GOL!⚽\n\n"
                    f"{mention} ¡GANA 10MXN ! 🎉\n\n"
                    f"Por favor envía una captura de pantalla de tu depósito de 100MXN realizado hoy junto con tu ID de jugador solo en este grupo, para reclamar tu premio.\n\n"
                    "**NOTA**: El depósito debe realizarse antes de jugar. Los depósitos realizados después de jugar no serán aceptados.")
            #   daily_winners.add(user_id)

                if current_attempt == 1:
                    await message.reply("¡Ganaste en tu primer intento — tu segunda oportunidad ha sido eliminada!", quote=True)
                    football_attempts[user_id] = 2
            else:
                await message.reply("¡Mejor suerte la próxima vez!", quote=True)

        elif emoji.startswith("🎰"): # Slot Machine
            if is_forwarded(message):
                await message.reply("🚫 ¡No está permitido reenviar un emoji!", quote=True)
                return
            if user_id in slots_attempts:
                await message.reply("¡Ya usaste tu 1 giro de tragamonedas en esta ronda!", quote=True)
                return
            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya has ganado en otro juego hoy! Vuelve mañana 😊", quote=True)
                return 
                
            slots_attempts.add(user_id)
            
            s1, s2, s3 = decode_slot(value)

            status, payout = calculate_slot_payout(s1, s2, s3) 

            await asyncio.sleep(1)            
            msg = (
                f"🎰 **Máquina Tragamonedas** 🎰\n"
                f"**{status}**\n"
                f"Recompensa: {payout}MXN\n\n"
                "Por favor envía una captura de pantalla de tu depósito de 300MXN realizado hoy junto con tu ID de jugador solo en este grupo, para reclamar tu premio.\n\n"
                "**NOTA:** El depósito debe realizarse antes de jugar. Los depósitos realizados después de jugar no serán aceptados."
            )
            await message.reply(msg, quote=True)
            daily_winners.add(user_id)

    elif message.text:
        emoji = normalize_emoji(message.text)
        user = message.from_user
        user_id = user.id
        mention = f"@{user.username}" if user.username else user.first_name
        reset_daily_winners()
        
        if await is_admin(client, message):
            return

        if emoji.startswith("🔒") and not safe_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("El evento Safe Cracker **no está activo** actualmente. ❌", quote=True)
            return

        if emoji.startswith("⛏️") or emoji.startswith("⛏") and not mine_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("El evento de minería **no está activo** actualmente. ❌", quote=True)
            return

        if emoji.startswith("🔒"):
            if user_id in safe_attempts:
                return await message.reply("⏳ ¡Ya intentaste abrir la caja fuerte en esta ronda!")
                
            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya has ganado en otro juego hoy! Vuelve mañana 😊", quote=True)
                return

            safe_attempts.add(user_id)

            opened = (random.randint(1, SAFE_WIN_CHANCE) == 1)

            if opened == 0:
                await asyncio.sleep(1)
                return await message.reply(
                    f"🔐 {mention} intentó abrir la caja fuerte...\n"
                    f"pero está **BLOQUEADA!** ❌"
                )
            await asyncio.sleep(1)
            daily_winners.add(user_id)
            return await message.reply(
                f"💥🔓 **¡CAJA FUERTE ABIERTA!**\n"
                f"{mention} gana **20MXN!** 🎉\n\n"
                "Por favor envía una captura de pantalla de tu depósito de 100MXN realizado hoy + solo el ID del jugador en este grupo, para reclamar tu bono.\n\n"
                "**NOTA:** El depósito debe realizarse antes de jugar. Los depósitos realizados después de jugar no serán aceptados."
            )

        elif emoji.startswith("⛏️") or emoji.startswith("⛏") :

            attempts = mining_attempts.get(user_id, 0)

            if attempts >= 2:
                return await message.reply("⛏️ ¡Ya usaste **2 intentos de minería** en esta ronda!", quote=True)

            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya has ganado en otro juego hoy! Vuelve mañana 😊", quote=True)
                return 
                
            attempts += 1
            mining_attempts[user_id] = attempts

            await asyncio.sleep(1)
            progress = await message.reply(f"⛏️ Intento de minería {attempts}/2...")

            win = (random.randint(1, MINING_WIN_CHANCE) == 1)

            if win:
                await asyncio.sleep(1)
                await progress.edit_text(
                    f"💎 **¡DIAMANTE ENCONTRADO!** 💎\n\n"
                    f"{mention} GANA **20MXN!** 🎉\n\n"
                    f"Por favor envía una captura de pantalla de tu depósito de 100MXN realizado hoy + solo el ID del jugador en este grupo, para reclamar tu bono.\n\n"
                    "**NOTA:** El depósito debe realizarse antes de jugar. Los depósitos realizados después de jugar no serán aceptados."
                )
                daily_winners.add(user_id)
                return

            await asyncio.sleep(1)
            await progress.edit_text(
                "😕 Solo rocas… nada valioso. 😕\n"
                "¡Intenta de nuevo!" if attempts < 2 else "🪨 No se encontró ningún diamante. ¡Mejor suerte la próxima vez!"
            )

app.run()