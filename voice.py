import queue
import threading
import logging

class VoiceEngine:
    """
    Asynchronous Text-to-Speech (TTS) engine using Windows native SAPI.
    Uses dedicated worker thread with pythoncom.CoInitialize() to prevent COM threading errors.
    """
    def __init__(self, enabled=True):
        self.enabled = enabled
        self._queue = queue.Queue()
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def speak(self, text: str):
        if not self.enabled:
            return
        # Avoid piling up too many speech requests
        if self._queue.qsize() < 2:
            self._queue.put(text)

    def _worker(self):
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            # Select Korean voice if available
            try:
                for voice in speaker.GetVoices():
                    desc = voice.GetDescription()
                    if "Korean" in desc or "Heami" in desc:
                        speaker.Voice = voice
                        break
            except Exception:
                pass

            while self._running:
                try:
                    text = self._queue.get(timeout=0.5)
                    speaker.Speak(text)
                    self._queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logging.warning(f"Speech error: {e}")
        except Exception as e:
            logging.error(f"Failed to initialize COM SAPI voice: {e}")

    def stop(self):
        self._running = False
