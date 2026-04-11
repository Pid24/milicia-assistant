"""Test edge-tts voice - quick demo."""
import asyncio
import io
import os
import sys
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import edge_tts

VOICE = "id-ID-GadisNeural"

async def generate_and_play(text, rate="+0%", pitch="+0Hz"):
    print(f"Generating: '{text}' (voice={VOICE}, rate={rate}, pitch={pitch})")
    communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=rate, pitch=pitch)
    audio_data = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.write(chunk["data"])
    
    audio_bytes = audio_data.getvalue()
    print(f"  Audio size: {len(audio_bytes)} bytes")
    
    fp = io.BytesIO(audio_bytes)
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(fp, "mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    print("  Done playing!")

async def main():
    # Test 1: Normal speed
    await generate_and_play("Halo Rofid! Ini suara baru Milicia, lebih natural kan?")
    time.sleep(0.5)
    
    # Test 2: Slightly faster
    await generate_and_play("Aku sekarang pakai suara Microsoft Neural, jauh lebih bagus dari Google TTS.", rate="+5%")
    time.sleep(0.5)
    
    # Test 3: Casual
    await generate_and_play("Selamat siang! Sistem Milicia sudah online dan siap membantu kamu.")

if __name__ == "__main__":
    asyncio.run(main())
