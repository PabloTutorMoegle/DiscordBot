import discord
from discord.ext import commands
import aiohttp
import random
import sqlite3 
import csv
import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables desde .env al entorno

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Discord token not found. Añade DISCORD_TOKEN a tu archivo .env")

catApiKey = os.getenv("CATAPIKEY")

# Nombre del archivo de la base de datos
DB_FILE = "pokemon_collection.db"

# =======================================================
# =======================================================
# 📚 Funciones de Base de Datos (SQLite)
# =======================================================
# =======================================================

def setup_db():
    """Inicializa la base de datos y crea la tabla 'user_cards' si no existe.
    Ya no se usa 'card_id': cada carta se identifica por su nombre (card_name).
    Almacenamos: nombre, tipo y url de imagen. Cada usuario sólo puede tener
    una fila por (user_id, card_name) — no se permiten duplicados."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_cards (
            user_id INTEGER NOT NULL,
            card_name TEXT NOT NULL,
            pokemon_type TEXT,
            image_url TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (user_id, card_name)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Base de datos {DB_FILE} inicializada (sin card_id).")

def add_card_to_collection(user_id, card_name, pokemon_type, image_url):
    """Añade una carta (identificada por su nombre) a la colección de un usuario
    sólo si no la tiene ya. Devuelve True si se insertó, False si el usuario ya tenía esa carta."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # Comprobar existencia primero para evitar duplicados
        c.execute("SELECT 1 FROM user_cards WHERE user_id = ? AND card_name = ?", (user_id, card_name))
        if c.fetchone():
            return False  # Ya existe, no se añade

        # Insertar la nueva carta (count se mantiene en 1)
        c.execute(
            "INSERT INTO user_cards (user_id, card_name, pokemon_type, image_url, count) VALUES (?, ?, ?, ?, 1)",
            (user_id, card_name, pokemon_type, image_url)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def get_user_collection(user_id):
    """Obtiene la colección de cartas de un usuario.
    Devuelve lista de tuplas (card_name, count, image_url). Con la regla de no duplicados,
    'count' será 1 para cada fila."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT card_name, count, image_url FROM user_cards WHERE user_id = ? ORDER BY card_name", (user_id,))
    collection = c.fetchall()
    conn.close()
    return collection

# -------------------------------------------------------

# 🚨 Ejecutar la inicialización de la DB ANTES de conectar el bot
setup_db()

# Definir los intents
intents = discord.Intents.default()
intents.members = True 
intents.presences = True
intents.message_content = True

# Inicializar el Bot
bot = commands.Bot(command_prefix='!', intents=intents)


# =======================================================
# =======================================================
# Eventos del bot
# =======================================================
# =======================================================


# =======================================================
# Evento de inicio
# =======================================================
@bot.event
async def on_ready():
    print(f'🤖 ¡Bot conectado! Logueado como: {bot.user.name}')
    print(f'ID del Bot: {bot.user.id}')
    await bot.change_presence(activity=discord.Game(name="¡I am online!"))

# =======================================================
# Evento de bienvenida (solo envía al canal de texto llamado "welcome")
# =======================================================
@bot.event
async def on_member_join(member):
    """Envía un mensaje únicamente al canal de texto llamado 'welcome'. Si no existe o no hay permiso, no hace nada."""
    guild = member.guild
    welcome_text = f'¡Bienvenido al servidor, {member.mention}! 🎉'

    try:
        # Buscar canal llamado "welcome" (insensible a mayúsculas)
        welcome_channel = next((ch for ch in guild.text_channels if ch.name.lower() == "welcome"), None)

        # Si existe y el bot tiene permiso para enviar mensajes, enviar; si no, no hacer nada
        if welcome_channel and welcome_channel.permissions_for(guild.me).send_messages:
            await welcome_channel.send(welcome_text)
    except Exception as e:
        # Silenciar errores para no intentar otros canales/DMs
        print(f"on_member_join unexpected error: {e}")


# =======================================================
# =======================================================
# Comandos del bot
# =======================================================
# =======================================================

# =======================================================
# Remove default help command to allow a custom one
# =======================================================
bot.remove_command('help')

# =======================================================
# Comando simple para saludar
# =======================================================
@bot.command()
async def hola(ctx):
    await ctx.send(f'¡Hey, {ctx.author.mention}! Moerning from the internet.')

# =======================================================
# Comando de ayuda para ver los posibles comandos
# =======================================================
@bot.command()
async def help(ctx):
    """Muestra una lista de comandos disponibles."""
    embed = discord.Embed(
        title="Commands",
        description="Here you have a list of commands you can use:",
        color=discord.Color.green()
    )
    
    embed.add_field(name="!hola", value="Say hi to Bot01.", inline=False)
    embed.add_field(name="!info", value="Shows server information.", inline=False)
    embed.add_field(name="!kitty", value="Sends a random picture of a cat.", inline=False)
    embed.add_field(name="!pokemon", value="Sends a random Pokémon card.", inline=False)
    embed.add_field(name="**!collection**", value="Shows your Pokémon card collection. 🎒", inline=False)
    
    await ctx.send(embed=embed)

# =======================================================
# Comando para mostrar información del servidor
# =======================================================
@bot.command()
async def info(ctx):
    """Muestra información clave sobre el servidor."""
    
    embed = discord.Embed(
        title=f"Statics from **{ctx.guild.name}**",
        description="General information about the server:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🗓️ Created on", 
        value=ctx.guild.created_at.strftime("%d/%m/%Y"), 
        inline=True
    )
    
    embed.add_field(
        name="👑 Owner", 
        value=ctx.guild.owner.mention, 
        inline=True
    )
    
    embed.add_field(
        name="👥 Members", 
        value=f"{ctx.guild.member_count} users", 
        inline=True
    )

    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
        
    await ctx.send(embed=embed)

# =======================================================
# Comnado para mandar foto de gato sacada de la API
# =======================================================
@bot.command()
async def kitty(ctx):
    """Envía una foto de un gato usando The Cat API."""
    url = "https://api.thecatapi.com/v1/images/search"
    headers = {
        "x-api-key": catApiKey
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                cat_image_url = data[0]['url']
                
                embed = discord.Embed(
                    title="Here you have a kitty 🐱",
                    color=discord.Color.purple()
                )
                embed.set_image(url=cat_image_url)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("Sorry! I couldn't get a kitty image right now.")


# =======================================================
# Comando para mandar carta Pokémon sacada de la API (MODIFICADO para guardar)
# =======================================================
@bot.command()
async def pokemon(ctx):
    """Elige aleatoriamente un Pokémon desde pokemon_con_imagenes.csv, lo muestra y lo guarda (la DB decide si ya existe)."""

    loading = await ctx.send("⌛ Entrando en los arbustos a buscar un Pokémon...")

    csv_path = os.path.join(os.path.dirname(__file__), "pokemon_con_imagenes.csv")

    rows = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            # Intentar DictReader primero (maneja cabeceras)
            reader = csv.DictReader(f)
            if reader.fieldnames:
                # Normalizar las claves de cabecera para mapear a 'name','type','image'
                for r in reader:
                    norm = {"name": "", "type": "", "image": ""}
                    for k, v in r.items():
                        if k is None:
                            continue
                        nk = k.strip().lower().replace(" ", "").replace("_", "")
                        val = (v or "").strip()
                        if "name" in nk:
                            norm["name"] = val
                        elif "type" in nk:
                            norm["type"] = val
                        elif "image" in nk or "link" in nk or "url" in nk or "imagen" in nk or "img" in nk:
                            norm["image"] = val
                    # Si aún no se detectó la imagen, buscar cualquier valor que parezca URL
                    if not norm["image"]:
                        for v in r.values():
                            if isinstance(v, str) and (v.strip().startswith("http://") or v.strip().startswith("https://")):
                                norm["image"] = v.strip()
                                break
                    # Si no hay nombre, intentar tomar la primera columna no vacía
                    if not norm["name"]:
                        for v in r.values():
                            if isinstance(v, str) and v.strip():
                                norm["name"] = v.strip()
                                break
                    rows.append(norm)
            else:
                # Fallback a reader posicional
                f.seek(0)
                for r in csv.reader(f):
                    if not r:
                        continue
                    rows.append({"name": r[0].strip(), "type": r[1].strip() if len(r) > 1 else "", "image": r[2].strip() if len(r) > 2 else ""})
    except FileNotFoundError:
        await loading.edit(content=f"Archivo CSV no encontrado: {csv_path}")
        return
    except Exception as e:
        await loading.edit(content=f"Error leyendo CSV: {e}")
        return

    if not rows:
        await loading.edit(content="El CSV está vacío o no contiene filas válidas.")
        return

    choice = random.choice(rows)
    card_name = (choice.get("name") or choice.get("Name") or choice.get("nombre") or "").strip()
    pokemon_type = (choice.get("type") or choice.get("Type") or choice.get("tipo") or "").strip()
    pokemonImage = (choice.get("image") or choice.get("img") or choice.get("imagen") or "").strip()

    if not card_name and isinstance(choice, (list, tuple)) and len(choice) > 0:
        card_name = choice[0].strip()
        pokemon_type = choice[1].strip() if len(choice) > 1 else ""
        pokemonImage = choice[2].strip() if len(choice) > 2 else ""
        print(card_name, pokemonImage)

    if not card_name:
        await loading.edit(content="No se pudo determinar el nombre del Pokémon desde el CSV.")
        return
    if not pokemonImage:
        await loading.edit(content=f"No se encontró imagen para '{card_name}' en el CSV.")
        return

    # Mostrar la carta primero
    embed = discord.Embed(
        title=f"🎴 {card_name}",
        description=f"Tipo: {pokemon_type}" if pokemon_type else None,
        color=discord.Color.green()
    )
    embed.set_image(url=pokemonImage)
    await loading.edit(content=None, embed=embed)

    # Guardar en la DB usando la función existente (ella decide si ya existe)
    try:
        added = add_card_to_collection(ctx.author.id, card_name, pokemon_type, pokemonImage)
    except Exception as e:
        await ctx.send(f"Error al guardar la carta en la base de datos: {e}")
        return

# =======================================================
# Nuevo Comando para ver la colección
# =======================================================
@bot.command()
async def collection(ctx):
    """Muestra cuántos pokémon tiene el usuario en total."""
    user_collection = get_user_collection(ctx.author.id)
    total_cards = sum(count for _, count, _ in user_collection) if user_collection else 0
    await ctx.send(f"🎒 {ctx.author.mention} tienes {total_cards} de 151 pokémon en tu colección.")


# =======================================================
# Ejecutar el Bot con tu Token
# =======================================================
bot.run(TOKEN)