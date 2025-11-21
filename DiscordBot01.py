import discord
from discord.ext import commands

# 1. Definir los intents que activaste en el portal de Discord
# Los intents son necesarios para que el bot pueda recibir ciertos eventos.
intents = discord.Intents.default()
# Asegúrate de activar estos, ya que los marcaste en el portal:
intents.members = True # Para acceder a información de miembros del servidor
intents.presences = True # Para acceder a información de presencia/estado
intents.message_content = True

# 2. Inicializar el Bot (usamos 'commands.Bot' para poder usar comandos fácilmente)
# prefix='!' significa que los comandos deben empezar con "!", ej: !hola
bot = commands.Bot(command_prefix='!', intents=intents)

# 3. Evento de inicio: Se ejecuta cuando el bot se conecta a Discord
@bot.event
async def on_ready():
    print(f'🤖 ¡Bot conectado! Logueado como: {bot.user.name}')
    print(f'ID del Bot: {bot.user.id}')
    # Puedes cambiar el estado del bot aquí:
    await bot.change_presence(activity=discord.Game(name="¡I am online!"))

# 4. Primer Comando simple:
# Se invoca al escribir !hola en un canal de Discord
@bot.command()
async def hola(ctx):
    # 'ctx' (context) contiene información sobre dónde se invocó el comando.
    await ctx.send(f'¡Hola, {ctx.author.mention}! Buenos dias desde el internet.')

import discord
from discord.ext import commands

# ... tu código de intents y bot.run() ...

@bot.command()
async def info(ctx):
    """Muestra información clave sobre el servidor."""
    
    # Crear un objeto Embed
    embed = discord.Embed(
        title=f"Estadísticas de **{ctx.guild.name}**",
        description="Información general del servidor:",
        color=discord.Color.blue() # Puedes usar cualquier color (red, green, gold, etc.)
    )
    
    # Campo 1: Fecha de creación
    # ctx.guild.created_at devuelve un objeto datetime.
    embed.add_field(
        name="🗓️ Creado el", 
        value=ctx.guild.created_at.strftime("%d/%m/%Y"), 
        inline=True
    )
    
    # Campo 2: Propietario del servidor
    embed.add_field(
        name="👑 Propietario", 
        value=ctx.guild.owner.mention, 
        inline=True
    )
    
    # Campo 3: Número de miembros
    embed.add_field(
        name="👥 Miembros", 
        value=f"{ctx.guild.member_count} usuarios", 
        inline=True
    )

    # Puedes añadir un thumbnail (icono del servidor)
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
        
    # Enviar el Embed al canal
    await ctx.send(embed=embed)

# 5. Ejecutar el Bot con tu Token
# El token proviene del archivo .env
import os
from dotenv import load_dotenv
load_dotenv()  # Carga las variables del archivo .env
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    print("❌ ERROR: La variable de entorno DISCORD_TOKEN no está configurada.")
else:
    print("✅ Token encontrado. Iniciando bot...")
    bot.run(TOKEN)
