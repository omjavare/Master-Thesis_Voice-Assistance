"""UI components for the transcription functionality."""
import flet as ft
import os
from ui.theme_lang import AppThemeLang
from ui.components import create_info_card, create_section_title, create_section_container
from flet import Text, Column, Row
from logic.entity_extractor import EntityExtractor

entity_extractor = EntityExtractor()

def create_transcription_display(transcription_text):
    def update_display(transcription):
        processed_text = entity_extractor.preprocess(transcription)
        entities = entity_extractor.extract_entities(processed_text)
        intent = entity_extractor.classify_intent(processed_text)
        transcription_text.value = f"Transcript: {transcription}"
        # Find the second Text widget (entities_text) by index
        if len(transcription_display.controls) > 1:
            transcription_display.controls[1].value = f"Entities: {entities}, Intent: {intent}"
        entity_extractor.log_entities_intents(entities, intent, transcription)
        transcription_text.page.update()

    transcription_display = Column(
        [
            Text(value="Waiting for transcription...", size=20, color="white"),
            Text(value="Entities: {}, Intent: unknown", size=18, color="white"),  # Removed 'id'
        ],
        spacing=10,
    )
    return transcription_display, update_display


def create_file_section(file_picker, file_picker_result_handler, recorder_start_handler, recorder_stop_handler):
    """Create the file selection section.
    
    Args:
        file_picker: FilePicker instance to use for file selection
        file_picker_result_handler: Callback when file is selected
        recorder_start_handler: Callback to start recording
        recorder_stop_handler: Callback to stop recording
        
    Returns:
        Tuple of (section container, file path text, file name text, record button, stop button, select file button)
    """
    selected_file_name = ft.Text("No file selected", size=16)
    selected_file_path = ft.Text("")
    format_hint = ft.Text("Supported formats: wav, mp3, m4a, ogg, flac, opus, amr, mp4", 
                         size=12, color=ft.colors.GREY_500, italic=True)
    
    record_button = ft.ElevatedButton(
        "Start Recording",
        icon=ft.icons.MIC,
        on_click=recorder_start_handler,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=AppThemeLang.ERROR_COLOR,
        ),
    )
    
    stop_button = ft.ElevatedButton(
        "Stop Recording",
        icon=ft.icons.STOP,
        on_click=recorder_stop_handler,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=AppThemeLang.WARNING_COLOR,
        ),
        visible=False,
    )
    
    select_file_button = ft.ElevatedButton(
        "Select Audio File",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["wav", "mp3", "m4a", "ogg", "flac", "opus", "amr", "mp4"]
        ),
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=AppThemeLang.PRIMARY_COLOR,
        ),
    )
    
    file_section = create_section_container(
        ft.Column([
            ft.Row([
                select_file_button,
                ft.VerticalDivider(width=10),
                record_button,
                stop_button,
                selected_file_name,
            ]),
            format_hint
        ])
    )
    
    def handle_file_picker_result(e: ft.FilePickerResultEvent):
        """Process file picker result and update UI."""
        if e.files:
            selected_file_path.value = e.files[0].path
            selected_file_name.value = os.path.basename(e.files[0].path)
            file_picker_result_handler()
    
    file_picker.on_result = handle_file_picker_result
    
    return file_section, selected_file_path, selected_file_name, record_button, stop_button, select_file_button

def create_result_section():
    """Create the transcription result section.
    
    Returns:
        Tuple of (section container, result text field, copy button, history button)
    """
    result_text = ft.TextField(
        multiline=True,
        min_lines=10,
        max_lines=20,
        read_only=True,
        border_color=ft.Colors.GREY_700,
        focused_border_color=AppThemeLang.SECONDARY_COLOR,
        text_size=16,
        expand=True,
    )
    
    copy_button = ft.IconButton(
        icon=ft.icons.COPY,
        tooltip="Copy to clipboard",
        icon_color=AppThemeLang.SECONDARY_COLOR,
        visible=False,
    )
    
    history_button = ft.IconButton(
        icon=ft.icons.HISTORY,
        tooltip="Clipboard history",
        icon_color=AppThemeLang.PRIMARY_COLOR,
    )
    
    results_section = ft.Container(
        content=ft.Column([
            ft.Row([
                create_section_title("Transcription Result"),
                ft.Row([
                    copy_button,
                    history_button,
                ]),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            result_text,
        ]),
        expand=True,
    )
    
    return results_section, result_text, copy_button, history_button

def create_controls_section():
    """Create the transcription controls section.
    
    Returns:
        Tuple of (section container, button, progress ring, status text, vad_checkbox, translate_checkbox, live_button)
    """
    transcribe_button = ft.ElevatedButton(
        "Transcribe",
        icon=ft.Icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=AppThemeLang.PRIMARY_COLOR,
            padding=15,
        ),
        height=50,
    )
    
    live_button = ft.ElevatedButton(
        "Start Live",
        icon=ft.Icons.MIC_NONE,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=AppThemeLang.LIVE_COLOR,
            padding=15,
        ),
        height=50,
    )
    
    progress_ring = ft.ProgressRing(visible=False, color=AppThemeLang.SECONDARY_COLOR)
    status_text = ft.Text("Ready", color=AppThemeLang.SUCCESS_COLOR)
    
    vad_checkbox = ft.Checkbox(
        label="Use VAD filter (remove silence)",
        value=True,
    )
    
    translate_checkbox = ft.Checkbox(
        label="Translate to English",
        value=False,
        tooltip="Convert speech from any language to English text",
        on_change=None,
    )
    
    controls_section = create_section_container(
        ft.Column([
            ft.Row([
                transcribe_button,
                ft.VerticalDivider(width=10),
                live_button,
                progress_ring,
                status_text,
            ]),
            ft.Row([
                vad_checkbox,
                translate_checkbox,
            ]),
        ])
    )
    
    return controls_section, transcribe_button, progress_ring, status_text, vad_checkbox, translate_checkbox, live_button

def create_model_section(model_selector):
    """Create the model selection section.
    
    Args:
        model_selector: ModelSelector instance
        
    Returns:
        Tuple of (section container, VRAM info card, speed info card)
    """
    vram_card = create_info_card("Required VRAM", "~1 GB", ft.Icons.MEMORY)
    speed_card = create_info_card("Relative Speed", "~7x", ft.Icons.SPEED)
    
    model_section = create_section_container(
        ft.Column([
            create_section_title("Model Settings"),
            ft.Row([
                model_selector.model_type,
                model_selector.model_size,
                model_selector.device_dropdown,
                model_selector.language_dropdown,
            ]),
            ft.Row([
                vram_card,
                speed_card,
            ]),
        ])
    )
    
    return model_section, vram_card, speed_card 