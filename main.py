"""Whisper Transcription App entry point."""
import flet as ft
from logic.app import WhisperApp
import os

# Set the JAVA_HOME environment variable for the application process
java_home = r'C:\Program Files\Eclipse Adoptium\jdk-21.0.8.9-hotspot'
os.environ['JAVA_HOME'] = java_home

# Add the Java bin directory to the application's PATH
os.environ['PATH'] = f"{java_home}\\bin{os.pathsep}{os.environ['PATH']}"

if __name__ == "__main__":
    ft.app(target=WhisperApp)