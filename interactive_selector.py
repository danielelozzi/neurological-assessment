# interactive_selector.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
import pandas as pd

class InteractiveVideoSelector(tk.Toplevel):
    """
    Una finestra di annotazione video generica per definire eventi o segmenti.
    Permette di scorrere il video, definire l'inizio e la fine di un evento,
    etichettarlo e salvarlo in una lista.
    """
    def __init__(self, parent, video_path, event_types, title="Selettore Video Interattivo"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.video_path = video_path
        self.event_types = event_types
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        # Variabili di stato
        self.is_playing = False
        self.current_frame_num = 0
        self.temp_start_frame = None
        self.defined_events = []
        self.result = None # Conterrà la lista di eventi al termine

        # --- GUI ---
        main_frame = tk.Frame(self)
        main_frame.pack(padx=10, pady=10)

        # Video
        self.video_label = tk.Label(main_frame)
        self.video_label.pack()

        # Slider
        self.slider_var = tk.DoubleVar()
        self.slider = ttk.Scale(main_frame, from_=0, to=self.total_frames - 1, orient="horizontal", variable=self.slider_var, command=self.seek)
        self.slider.pack(fill="x", expand=True, pady=5)

        # Controlli
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(pady=5)
        self.play_pause_button = tk.Button(controls_frame, text="Play", width=10, command=self.toggle_play_pause)
        self.play_pause_button.grid(row=0, column=0, padx=5)
        self.frame_info_label = tk.Label(controls_frame, text=f"Frame: 0 / {self.total_frames}")
        self.frame_info_label.grid(row=0, column=1, padx=10)

        # Annotazione
        annotation_frame = tk.Frame(main_frame)
        annotation_frame.pack(pady=10)
        
        tk.Label(annotation_frame, text="Tipo Evento:").grid(row=0, column=0, padx=5)
        self.event_type_var = tk.StringVar(value=self.event_types[0])
        self.event_menu = ttk.Combobox(annotation_frame, textvariable=self.event_type_var, values=self.event_types, state="readonly")
        self.event_menu.grid(row=0, column=1, padx=5)
        
        self.start_button = tk.Button(annotation_frame, text="1. Imposta Inizio", command=self.mark_start)
        self.start_button.grid(row=1, column=0, pady=10, padx=5)
        self.end_button = tk.Button(annotation_frame, text="2. Imposta Fine e Salva", state="disabled", command=self.mark_end_and_save)
        self.end_button.grid(row=1, column=1, pady=10, padx=5)
        self.status_label = tk.Label(annotation_frame, text="In attesa di 'Inizio'...")
        self.status_label.grid(row=2, column=0, columnspan=2)

        # Lista eventi definiti
        events_list_frame = tk.Frame(main_frame)
        events_list_frame.pack(fill="x", expand=True, pady=5)
        tk.Label(events_list_frame, text="Eventi Definiti:").pack(anchor="w")
        self.events_listbox = tk.Listbox(events_list_frame, height=5)
        self.events_listbox.pack(fill="x", expand=True)
        tk.Button(events_list_frame, text="Rimuovi Selezionato", command=self.remove_selected_event).pack(anchor="e", pady=2)

        # Azioni finali
        action_frame = tk.Frame(main_frame)
        action_frame.pack(pady=10)
        tk.Button(action_frame, text="Fatto, Chiudi", command=self.confirm).pack(side="left", padx=5)
        tk.Button(action_frame, text="Annulla", command=self.cancel).pack(side="left", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.update()
        self.show_first_frame()
        self.update_video_loop()

    def show_first_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.show_frame(frame)

    def update_video_loop(self):
        if self.is_playing:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame_num = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.slider_var.set(self.current_frame_num)
                self.show_frame(frame)
            else:
                self.toggle_play_pause()
        self.after(int(1000 / self.fps) if self.fps > 0 else 33, self.update_video_loop)

    def show_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        w, h = img.size
        max_h = 600
        if h > max_h:
            ratio = max_h / h
            img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image=img)
        self.video_label.config(image=photo)
        self.video_label.image = photo # type: ignore
        self.frame_info_label.config(text=f"Frame: {self.current_frame_num} / {self.total_frames}")

    def seek(self, value):
        if not self.is_playing:
            self.current_frame_num = int(float(value))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_num)
            ret, frame = self.cap.read()
            if ret:
                self.show_frame(frame)

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        self.play_pause_button.config(text="Pause" if self.is_playing else "Play")

    def mark_start(self):
        self.temp_start_frame = self.current_frame_num
        self.end_button.config(state="normal")
        self.status_label.config(text=f"Inizio impostato a {self.temp_start_frame}. Cerca la fine e salva.")

    def mark_end_and_save(self):
        if self.temp_start_frame is None:
            return
        
        end_frame = self.current_frame_num
        if end_frame <= self.temp_start_frame:
            messagebox.showwarning("Errore", "Il frame di fine deve essere successivo a quello di inizio.")
            return

        event = {
            "label": self.event_type_var.get(),
            "start": self.temp_start_frame,
            "end": end_frame
        }
        self.defined_events.append(event)
        self.update_listbox()
        
        # Reset per il prossimo evento
        self.temp_start_frame = None
        self.end_button.config(state="disabled")
        self.status_label.config(text="Evento salvato! In attesa di un nuovo 'Inizio'.")

    def remove_selected_event(self):
        selected_indices = self.events_listbox.curselection()
        if not selected_indices:
            return
        # Rimuovi partendo dalla fine per non sballare gli indici
        for i in sorted(selected_indices, reverse=True):
            del self.defined_events[i]
        self.update_listbox()

    def update_listbox(self):
        self.events_listbox.delete(0, tk.END)
        for event in self.defined_events:
            self.events_listbox.insert(tk.END, f"{event['label']}: Frame {event['start']} -> {event['end']}")

    def confirm(self):
        if not self.defined_events:
            if not messagebox.askyesno("Attenzione", "Nessun evento definito. Vuoi chiudere comunque?"):
                return
        self.result = self.defined_events
        self.cap.release()
        self.destroy()

    def cancel(self):
        self.result = None
        self.cap.release()
        self.destroy()

   

class SingleFrameSelector(tk.Toplevel):
    """
    Una finestra di dialogo con un video player semplificato per selezionare
    un singolo frame e restituirne il numero.
    """
    def __init__(self, parent, video_path, title="Seleziona un Frame"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        # Variabili di stato
        self.is_playing = False
        self.current_frame_num = 0
        self.result = None  # Conterrà il frame selezionato

        # --- GUI ---
        main_frame = tk.Frame(self)
        main_frame.pack(padx=10, pady=10)

        self.video_label = tk.Label(main_frame)
        self.video_label.pack()

        self.slider_var = tk.DoubleVar()
        self.slider = ttk.Scale(main_frame, from_=0, to=self.total_frames - 1, orient="horizontal", variable=self.slider_var, command=self.seek)
        self.slider.pack(fill="x", expand=True, pady=5)

        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(pady=10)

        self.play_pause_button = tk.Button(controls_frame, text="Play", width=10, command=self.toggle_play_pause)
        self.play_pause_button.grid(row=0, column=0, padx=5)
        self.frame_info_label = tk.Label(controls_frame, text=f"Frame: 0 / {self.total_frames}")
        self.frame_info_label.grid(row=0, column=1, padx=10)

        action_frame = tk.Frame(main_frame)
        action_frame.pack(pady=10)
        tk.Button(action_frame, text="Usa Questo Frame", command=self.confirm, font=("", 12, "bold")).pack(side="left", padx=10)
        tk.Button(action_frame, text="Annulla", command=self.cancel).pack(side="left", padx=10)

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.show_first_frame()
        self.update_video_loop()

    def show_first_frame(self):
        ret, frame = self.cap.read()
        if ret: self.show_frame(frame)

    def update_video_loop(self):
        if self.is_playing:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame_num = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.slider_var.set(self.current_frame_num)
                self.show_frame(frame)
            else:
                self.toggle_play_pause()
        self.after(int(1000 / self.fps) if self.fps > 0 else 33, self.update_video_loop)

    def show_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        w, h = img.size
        max_h = 720
        if h > max_h:
            ratio = max_h / h
            img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image=img)
        self.video_label.config(image=photo)
        self.video_label.image = photo # type: ignore
        self.frame_info_label.config(text=f"Frame: {self.current_frame_num} / {self.total_frames}")

    def seek(self, value):
        if not self.is_playing:
            self.current_frame_num = int(float(value))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_num)
            ret, frame = self.cap.read()
            if ret: self.show_frame(frame)

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        self.play_pause_button.config(text="Pause" if self.is_playing else "Play")

    def confirm(self):
        self.result = self.current_frame_num
        self.cap.release()
        self.destroy()

    def cancel(self):
        self.result = None
        self.cap.release()
        self.destroy()