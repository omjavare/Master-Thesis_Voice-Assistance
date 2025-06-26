"""Main application logic for Whisper Transcription App."""
import flet as ft
from ui.theme_lang import AppThemeLang
from ui.app_ui import configure_page, create_header
from ui.model_selection import ModelSelector
from ui.transcription_ui import (
    create_file_section, 
    create_result_section, 
    create_controls_section, 
    create_model_section
)
from ui.clipboard_history_ui import create_history_dialog
from logic.whisper_service import WhisperService
from logic.audio_recorder import AudioRecorder
from logic.clipboard_history import ClipboardHistory
from logic.live_transcription import LiveTranscription
from logic.entity_extractor import EntityExtractor
from ui.transcription_ui import create_transcription_display
import threading
import time

def configure_page(page):
    """Configure the Flet page with theme, title, and window settings."""
    page.title = "Whisper Transcription App"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_resizable = True
    page.window_width = 800
    page.window_height = 600
    page.padding = 20
    page.spacing = 10
    page.theme = ft.Theme(
        color_scheme_seed=AppThemeLang.PRIMARY_COLOR,
        use_material3=True
    )

class WhisperApp:
    def __init__(self, page: ft.Page):
        try:
            self.page = page
            configure_page(page)
            
            self.file_picker = ft.FilePicker()
            self.page.overlay.append(self.file_picker)
            
            self.header = create_header()
            
            self.clipboard_history = ClipboardHistory()
            
            self.model_selector = ModelSelector(page, self.on_model_change)
            
            def on_recorder_status(status):
                if "error" in status.lower() or "failed" in status.lower():
                    self.status_text.value = status
                    self.status_text.color = AppThemeLang.ERROR_COLOR
                    if self.status_text and self.page:
                        self.page.update()
                elif "saved" in status:
                    self.status_text.value = "Recording saved"
                    self.status_text.color = AppThemeLang.SUCCESS_COLOR
                    if self.status_text and self.page:
                        self.page.update()
            
            self.audio_recorder = AudioRecorder(on_status_update=on_recorder_status)
            
            def start_recording(_):
                self.record_button.visible = False
                self.stop_button.visible = True
                self.selected_file_path.value = ""
                self.selected_file_name.value = "Recording..."
                self.transcribe_button.disabled = True
                self.audio_recorder.start_recording()
                if self.page:
                    self.page.update()
            
            def stop_recording(_):
                self.record_button.visible = True
                self.stop_button.visible = False
                file_path = self.audio_recorder.stop_recording()
                if file_path:
                    self.selected_file_path.value = file_path
                    self.selected_file_name.value = "Recorded Audio"
                    self.update_ui_state()
                else:
                    self.selected_file_name.value = "No file selected"
                if self.page:
                    self.page.update()
            
            self.file_section, self.selected_file_path, self.selected_file_name, self.record_button, self.stop_button, self.select_file_button = create_file_section(
                self.file_picker, 
                lambda: self.update_ui_state(),
                start_recording,
                stop_recording
            )
            
            self.model_section, self.vram_card, self.speed_card = create_model_section(self.model_selector)
            
            self.results_section, self.result_text, self.copy_button, self.history_button = create_result_section()
            
            self.controls_section, self.transcribe_button, self.progress_ring, self.status_text, self.vad_checkbox, self.translate_checkbox, self.live_button = create_controls_section()
            
            self.entity_extractor = EntityExtractor()
            self.transcription_display, self.update_display = create_transcription_display(ft.Text())
            
            self.live_transcription = None
            self.is_live_active = False
            self.live_accumulated_text = ""
            self.transcription_buffer = []
            self.last_update_time = time.time()
            
            def on_live_transcription(text):
                if not text or not isinstance(text, str):
                    print("Invalid transcription data:", text)
                    return
                print(f"Received transcription: {text}")
                self.transcription_buffer.append(text)
                current_time = time.time()
                if current_time - self.last_update_time >= 2.0 or len(self.transcription_buffer) > 5:
                    accumulated_text = " ".join(self.transcription_buffer).strip()
                    if accumulated_text:
                        self.result_text.value = accumulated_text  # Reset to avoid duplication
                        self.copy_button.visible = bool(self.result_text.value)
                        self.live_accumulated_text = accumulated_text
                        try:
                            result = self.entity_extractor.process(accumulated_text)
                            display_text = f"{accumulated_text}\nEntities: {result['entities']}, Intent: {result['intent']}"
                            if self.update_display and self.transcription_display:
                                self.update_display(display_text)
                            print(f"Logged: Entities={result['entities']}, Intent={result['intent']}")
                        except AttributeError as e:
                            print(f"Entity extraction error: {e}")
                            display_text = f"{accumulated_text}\nEntities: {{}}, Intent: unknown"
                            if self.update_display and self.transcription_display:
                                self.update_display(display_text)
                        self.transcription_buffer = []
                        self.last_update_time = current_time
                    if self.page:
                        self.page.update()
            
            self.on_live_transcription = on_live_transcription
            
            def on_live_status(status):
                self.status_text.value = status
                if "error" in status.lower() or "failed" in status.lower():
                    self.status_text.color = AppThemeLang.ERROR_COLOR
                    self.live_button.text = "Start Live"
                    self.live_button.icon = ft.icons.MIC_NONE
                elif "started" in status.lower():
                    self.status_text.color = AppThemeLang.SUCCESS_COLOR
                elif "stopped" in status.lower():
                    self.status_text.color = AppThemeLang.SUCCESS_COLOR
                    self.live_button.text = "Start Live"
                    self.live_button.icon = ft.icons.MIC_NONE
                else:
                    self.status_text.color = AppThemeLang.WARNING_COLOR
                if self.status_text and self.page:
                    self.page.update()
            
            def on_live_error(error):
                self.status_text.value = f"Error: {error}"
                self.status_text.color = AppThemeLang.ERROR_COLOR
                self.live_button.text = "Start Live"
                self.live_button.icon = ft.icons.MIC_NONE
                if self.status_text and self.page:
                    self.page.update()
            
            def toggle_live_transcription(_):
                if not LiveTranscription.is_available():
                    self.status_text.value = "Error: sounddevice library not available"
                    self.status_text.color = AppThemeLang.ERROR_COLOR
                    if self.status_text and self.page:
                        self.page.update()
                    return
                
                model_name = self.model_selector.get_model_name()
                
                if model_name is None:
                    self.status_text.value = "Invalid model selection"
                    self.status_text.color = AppThemeLang.ERROR_COLOR
                    if self.status_text and self.page:
                        self.page.update()
                    return
                
                if self.is_live_active:
                    if self.live_transcription:
                        self.live_transcription.stop()
                    self.is_live_active = False
                    self.transcribe_button.disabled = False
                    self.record_button.disabled = False
                    self.select_file_button.disabled = False
                    self.progress_ring.visible = False
                    
                    self.model_selector.model_type.disabled = False
                    self.model_selector.model_size.disabled = False
                    self.model_selector.device_dropdown.disabled = False
                    self.model_selector.language_dropdown.disabled = self.model_selector.model_type.value == "english_only"
                    self.vad_checkbox.disabled = False
                    self.translate_checkbox.disabled = False
                    self.translate_checkbox.visible = self.model_selector.model_type.value == "multilingual"
                    
                    if self.live_accumulated_text.strip():
                        model_name = self.model_selector.get_model_name() or ""
                        self.clipboard_history.add_item(self.live_accumulated_text, model_name)
                        self.live_accumulated_text = ""
                else:
                    self.result_text.value = ""
                    self.live_accumulated_text = ""
                    self.copy_button.visible = False
                    self.progress_ring.visible = True
                    self.transcription_buffer = []
                    self.last_update_time = time.time()
                    
                    task = "translate" if self.translate_checkbox.value else "transcribe"
                    language = self.model_selector.language_dropdown.value if self.model_selector.language_dropdown.value != "auto" else "en"
                    
                    compute_type = "int8"
                    
                    self.live_transcription = LiveTranscription(
                        on_transcription=self.on_live_transcription,
                        on_status_update=on_live_status,
                        on_error=on_live_error,
                        model_path=model_name,
                        device=self.model_selector.device_dropdown.value,
                        language=language,
                        task=task,
                        compute_type=compute_type,
                        vad_filter=self.vad_checkbox.value,
                    )
                    
                    success = self.live_transcription.start()
                    
                    if success:
                        self.is_live_active = True
                        self.live_button.text = "Stop Live"
                        self.live_button.icon = ft.icons.MIC_OFF
                        self.transcribe_button.disabled = True
                        self.record_button.disabled = True
                        self.select_file_button.disabled = True
                        self.model_selector.model_type.disabled = True
                        self.model_selector.model_size.disabled = True
                        self.model_selector.device_dropdown.disabled = True
                        self.model_selector.language_dropdown.disabled = True
                        self.vad_checkbox.disabled = True
                        self.translate_checkbox.disabled = True
                    else:
                        self.progress_ring.visible = False
                
                if self.page:
                    self.page.update()
            
            self.live_button.on_click = toggle_live_transcription
            
            def translate_checkbox_changed(_):
                if self.translate_checkbox.value:
                    self.model_selector.language_dropdown.value = "auto"
                    self.model_selector.language_dropdown.disabled = True
                else:
                    if self.model_selector.model_type.value == "multilingual":
                        self.model_selector.language_dropdown.disabled = False
                if self.page:
                    self.page.update()
            
            self.translate_checkbox.on_change = translate_checkbox_changed
            
            def on_history_item_copy(text):
                self.result_text.value = text
                self.copy_button.visible = True
                self.status_text.value = "Copied from history!"
                self.status_text.color = AppThemeLang.SUCCESS_COLOR
                if self.status_text and self.page:
                    self.page.update()
                threading.Timer(2.0, self.reset_status).start()
            
            self.history_dialog, self.open_history_dialog = create_history_dialog(
                self.page, 
                self.clipboard_history, 
                on_history_item_copy
            )
            
            self.page.overlay.append(self.history_dialog)
            
            self.history_button.on_click = lambda _: self.open_history_dialog()
            
            def on_status_update(status):
                self.status_text.value = status
                if status == "Transcribing audio..." or status.startswith("Loading model"):
                    self.status_text.color = AppThemeLang.WARNING_COLOR
                elif status == "Transcription complete!":
                    self.status_text.color = AppThemeLang.SUCCESS_COLOR
                if self.status_text and self.page:
                    self.page.update()
            
            def on_result(text):
                self.result_text.value = text
                self.copy_button.visible = bool(text)
                
                if text.strip():
                    model_name = self.model_selector.get_model_name() or ""
                    self.clipboard_history.add_item(text, model_name)
                    
                if self.page:
                    self.page.update()
            
            def on_error(error):
                self.result_text.value = f"Error: {error}"
                self.status_text.value = "Error occurred"
                self.status_text.color = AppThemeLang.ERROR_COLOR
                if self.page:
                    self.page.update()
            
            def on_complete():
                self.progress_ring.visible = False
                if self.page:
                    self.page.update()
            
            def copy_to_clipboard(_):
                text = self.result_text.value
                self.page.set_clipboard(text)
                self.status_text.value = "Copied to clipboard!"
                self.status_text.color = AppThemeLang.SUCCESS_COLOR
                if self.status_text and self.page:
                    self.page.update()
                
                if text.strip():
                    model_name = self.model_selector.get_model_name() or ""
                    self.clipboard_history.add_item(text, model_name)
                
                threading.Timer(2.0, self.reset_status).start()
            
            def reset_status():
                self.status_text.value = "Ready"
                self.status_text.color = AppThemeLang.SUCCESS_COLOR
                if self.status_text and self.page:
                    self.page.update()
            
            self.copy_button.on_click = copy_to_clipboard
            
            self.whisper_service = WhisperService(
                on_status_update=on_status_update,
                on_result=on_result,
                on_error=on_error,
                on_complete=on_complete
            )
            
            def start_transcription(_):
                if not self.selected_file_path.value:
                    self.status_text.value = "Please select an audio file first"
                    self.status_text.color = AppThemeLang.ERROR_COLOR
                    if self.status_text and self.page:
                        self.page.update()
                    return
                
                model_name = self.model_selector.get_model_name()
                
                if model_name is None:
                    self.status_text.value = "Invalid model selection"
                    self.status_text.color = AppThemeLang.ERROR_COLOR
                    if self.status_text and self.page:
                        self.page.update()
                    return
                
                self.result_text.value = ""
                self.copy_button.visible = False
                self.progress_ring.visible = True
                if self.page:
                    self.page.update()
                
                task = "translate" if self.translate_checkbox.value else "transcribe"
                
                self.whisper_service.transcribe(
                    file_path=self.selected_file_path.value,
                    model_name=model_name,
                    device=self.model_selector.device_dropdown.value,
                    use_vad=self.vad_checkbox.value,
                    language=self.model_selector.language_dropdown.value,
                    task=task
                )
            
            self.transcribe_button.on_click = start_transcription

            self.page.add(
                ft.Column(
                    controls=[
                        self.header,
                        self.file_section,
                        self.model_section,
                        self.controls_section,
                        self.results_section,
                        self.transcription_display,
                    ],
                    expand=True,
                    spacing=10,
                )
            )
            
            self.update_ui_state()

        except Exception as e:
            print("Fatal error in WhisperApp init:", e)
            import traceback
            traceback.print_exc()

    def update_ui_state(self):
        """Update UI elements based on current model and file selection."""
        is_valid_model = self.model_selector.is_valid_model()
        has_file = bool(self.selected_file_path.value)
        
        self.transcribe_button.disabled = not is_valid_model or not has_file or self.is_live_active
        
        if not is_valid_model:
            self.transcribe_button.style.bgcolor = {"": AppThemeLang.PRIMARY_COLOR_TRANSLUCENT}
            self.transcribe_button.tooltip = "This model is not available in English-only mode"
        elif not has_file:
            self.transcribe_button.style.bgcolor = {"": AppThemeLang.DISABLED_COLOR}
            self.transcribe_button.tooltip = "Please select an audio file first"
        else:
            self.transcribe_button.style.bgcolor = {"": AppThemeLang.PRIMARY_COLOR}
            self.transcribe_button.tooltip = None
        
        if not is_valid_model:
            self.status_text.value = "Note: Large and Turbo models are only available in multilingual versions"
            self.status_text.color = AppThemeLang.WARNING_COLOR
        else:
            self.status_text.value = "Ready"
            self.status_text.color = AppThemeLang.SUCCESS_COLOR
        
        self.translate_checkbox.visible = self.model_selector.model_type.value == "multilingual"
        if self.model_selector.model_type.value == "english_only":
            self.translate_checkbox.value = False
            
        self.vram_card.content.content.controls[1].value = self.model_selector.get_memory_info()
        self.speed_card.content.content.controls[1].value = self.model_selector.get_speed_info()
        if self.page:
            self.page.update()

    def on_model_change(self):
        """Callback for model change events."""
        self.update_ui_state()

def main(page: ft.Page):
    """Main entry point for the Flet app."""
    WhisperApp(page)

if __name__ == "__main__":
    ft.app(target=main)