import cv2
import easyocr
import os
import sys
import csv
import tkinter as tk
from tkinter import messagebox, ttk # Aggiunto ttk per lo slider
from PIL import Image, ImageTk      # Aggiunto per gestire le immagini in Tkinter
import concurrent.futures

# --- NUOVO: Selettore di frame interattivo con video ---

class InteractiveFrameSelector:
    """
    Mostra una finestra con un video player per permettere all'utente di selezionare
    interattivamente i frame di inizio per i segmenti 'fast' e 'slow'.
    """
    def __init__(self, parent, video_path):
        self.top = tk.Toplevel(parent)
        self.top.title("Selezione Frame Interattiva")

        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        # Variabili di stato
        self.fast_start_frame = None
        self.slow_start_frame = None
        self.is_playing = False
        self.current_frame_num = 0
        self.result = {"fast": None, "slow": None, "cancelled": True}

        # --- Creazione Widget GUI ---
        
        # Frame principale
        main_frame = tk.Frame(self.top)
        main_frame.pack(padx=10, pady=10)

        # Etichetta per mostrare il video
        self.video_label = tk.Label(main_frame)
        self.video_label.pack()

        # Slider (Scrubber) per la navigazione
        self.slider_var = tk.DoubleVar()
        self.slider = ttk.Scale(main_frame, from_=0, to=self.total_frames -1, orient="horizontal", variable=self.slider_var, command=self.seek)
        self.slider.pack(fill="x", expand=True, pady=5)

        # Frame per i controlli
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(pady=5)

        self.play_pause_button = tk.Button(controls_frame, text="Play", width=10, command=self.toggle_play_pause)
        self.play_pause_button.grid(row=0, column=0, padx=5)

        self.frame_info_label = tk.Label(controls_frame, text=f"Frame: 0 / {self.total_frames}")
        self.frame_info_label.grid(row=0, column=1, padx=10)

        # Frame per i pulsanti di selezione
        selection_frame = tk.Frame(main_frame)
        selection_frame.pack(pady=10)

        tk.Button(selection_frame, text="Imposta Inizio FAST", command=self.set_fast_frame).grid(row=0, column=0, padx=10)
        self.fast_frame_label = tk.Label(selection_frame, text="FAST: Non impostato", fg="red")
        self.fast_frame_label.grid(row=0, column=1)

        tk.Button(selection_frame, text="Imposta Inizio SLOW", command=self.set_slow_frame).grid(row=1, column=0, padx=10, pady=5)
        self.slow_frame_label = tk.Label(selection_frame, text="SLOW: Non impostato", fg="red")
        self.slow_frame_label.grid(row=1, column=1)

        # Pulsanti di conferma/annullamento
        action_frame = tk.Frame(main_frame)
        action_frame.pack(pady=10)
        self.confirm_button = tk.Button(action_frame, text="Conferma", command=self.confirm, state="disabled")
        self.confirm_button.pack(side="left", padx=5)
        tk.Button(action_frame, text="Annulla", command=self.cancel).pack(side="left", padx=5)
        
        # Gestione chiusura finestra
        self.top.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Mostra il primo frame e avvia il ciclo di aggiornamento
        self.update_frame()
        # Leggi e mostra il primo frame esplicitamente all'inizio
        ret, frame = self.cap.read()
        if ret:
            self.show_frame(frame)

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        self.play_pause_button.config(text="Pause" if self.is_playing else "Play")

    def seek(self, value):
        if not self.is_playing:
            self.current_frame_num = int(float(value))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_num)
            # Leggi il frame corrispondente e mostralo subito
            ret, frame = self.cap.read()
            if ret:
                self.show_frame(frame)

    def set_fast_frame(self):
        self.fast_start_frame = self.current_frame_num
        self.fast_frame_label.config(text=f"FAST: Frame {self.fast_start_frame}", fg="green")
        self.check_confirm_state()

    def set_slow_frame(self):
        self.slow_start_frame = self.current_frame_num
        self.slow_frame_label.config(text=f"SLOW: Frame {self.slow_start_frame}", fg="green")
        self.check_confirm_state()
        
    def check_confirm_state(self):
        if self.fast_start_frame is not None and self.slow_start_frame is not None:
            self.confirm_button.config(state="normal")

    def update_frame(self):
        if self.is_playing:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame_num = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.slider_var.set(self.current_frame_num)
                self.show_frame(frame)
            else: # Fine del video
                self.is_playing = False
                self.play_pause_button.config(text="Play")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_num = 0
                self.slider_var.set(0)
        
        # Richiama questa funzione periodicamente per creare un loop
        self.top.after(int(1000/self.fps) if self.fps > 0 else 33, self.update_frame)

    def show_frame(self, frame):
        # Converte il frame di OpenCV (BGR) in un'immagine per Tkinter (RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        # Ridimensiona l'immagine per adattarla allo schermo se necessario
        w, h = img.size
        max_h = 720
        if h > max_h:
            ratio = max_h / h
            new_w, new_h = int(w * ratio), int(h * ratio)
            # CORREZIONE 1: Usa Image.Resampling.LANCZOS
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(image=img)
        self.video_label.config(image=photo)
        
        # CORREZIONE 2: Mantiene un riferimento per evitare la garbage collection e dice a Pylance di ignorare il falso positivo
        self.video_label.image = photo # type: ignore
        
        self.frame_info_label.config(text=f"Frame: {self.current_frame_num} / {self.total_frames}")

    def confirm(self):
        self.result["fast"] = self.fast_start_frame
        self.result["slow"] = self.slow_start_frame
        self.result["cancelled"] = False
        self.top.destroy()
        self.cap.release()

    def cancel(self):
        self.top.destroy()
        self.cap.release()

def select_frames_interactively_gui(video_path):
    """Funzione di avvio per il selettore interattivo."""
    root = tk.Tk()
    root.withdraw() # Nasconde la finestra principale di Tk
    selector = InteractiveFrameSelector(root, video_path)
    # Centra la finestra
    selector.top.update_idletasks()
    ws = selector.top.winfo_screenwidth()
    hs = selector.top.winfo_screenheight()
    x = (ws/2) - (selector.top.winfo_width()/2)
    y = (hs/2) - (selector.top.winfo_height()/2)
    selector.top.geometry('%dx%d+%d+%d' % (selector.top.winfo_width(), selector.top.winfo_height(), x, y))
    
    selector.top.transient(root)
    selector.top.grab_set()
    root.wait_window(selector.top)
    root.destroy()
    return selector.result

# --- Pipeline di pre-elaborazione OCR ---
def preprocess_adaptive_gaussian(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

def preprocess_median_blur(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    return cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

def preprocess_simple_binary_otsu(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    return thresh

# --- Worker per l'esecuzione parallela dell'OCR ---
def run_ocr_on_pipeline(args):
    """
    Funzione eseguita da ogni thread. Prende un frame, una pipeline,
    esegue l'OCR e ritorna True se trova il testo.
    """
    frame, pipeline_func, reader, text_to_find = args
    try:
        # Estrai ROI
        h, w, _ = frame.shape
        roi = frame[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
        
        # Applica pipeline
        processed_roi = pipeline_func(roi)
        
        # Esegui OCR
        results = reader.readtext(processed_roi, allowlist='0123456789', detail=0)
        
        for text in results:
            if text_to_find in text:
                return True
        return False
    except Exception:
        return False

# --- Funzione che orchestra i thread paralleli per OCR ---
def detect_text_ocr(frame, reader, text_to_find='1', executor=None):
    """
    Prova diverse pipeline in parallelo per massimizzare il rilevamento.
    """
    if executor is None:
        # Esecuzione non parallela se non viene fornito un executor
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            return detect_text_ocr(frame, reader, text_to_find, ex)

    pipelines = [
        preprocess_adaptive_gaussian,
        preprocess_median_blur,
        preprocess_simple_binary_otsu,
    ]
    
    # Crea un task per ogni pipeline
    args_list = [(frame, p, reader, text_to_find) for p in pipelines]
    
    # Esegue i task in parallelo
    results = executor.map(run_ocr_on_pipeline, args_list)
    
    # Ritorna True se ALMENO UNO dei risultati è True
    return any(results)

def main(args):
    print("\nFASE 1: Ricerca del punto di riferimento t0...")
    if not os.path.exists(args.input_video):
        raise FileNotFoundError(f"Video di input non trovato: {args.input_video}")

    cap = cv2.VideoCapture(args.input_video)
    if not cap.isOpened():
        raise IOError(f"Errore: Impossibile aprire il video '{args.input_video}'")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        raise ValueError("Errore: Impossibile leggere la durata del video.")
    
    stop_frame_threshold = total_frames // 6
    print(f"Video di {total_frames} frame. Timeout automatico impostato al frame {stop_frame_threshold}.")

    try:
        reader = easyocr.Reader(['en'], gpu=True)
        print("EasyOCR inizializzato con GPU.")
    except Exception:
        print("GPU non disponibile per EasyOCR, ripiego su CPU (potrebbe essere più lento).")
        reader = easyocr.Reader(['en'], gpu=False)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: raise ValueError("Errore: Impossibile leggere gli FPS del video.")

    t0 = -1
    frame_number = 0
    one_confirmed = False
    detection_goal, frame_tolerance, detections_found, last_detection_frame = 2, 5, 0, -1
    
    print(f"Avvio ricerca automatica parallela...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or (not one_confirmed and frame_number > stop_frame_threshold):
                break

            if frame_number % 15 == 0:
                print(f"Scansione in corso... Frame: {frame_number}/{total_frames}", end='\r')

            is_one_present = detect_text_ocr(frame, reader, '1', executor)

            if not one_confirmed:
                if is_one_present:
                    if last_detection_frame == -1 or (frame_number - last_detection_frame) > frame_tolerance + 1:
                        detections_found = 1
                    else:
                        detections_found += 1
                    last_detection_frame = frame_number
                
                if detections_found >= detection_goal:
                    one_confirmed = True
                    print(f"\n{' ' * 70}\rRilevamento del numero '1' confermato. Attesa della sua scomparsa...")
            
            elif one_confirmed and not is_one_present:
                t0 = frame_number
                print(f"Punto di riferimento automatico trovato! t0 = frame {t0}")
                break
            
            frame_number += 1

    print(" " * 70, end='\r')
    cap.release()

    manual_frames = None
    if t0 == -1:
        print("Ricerca automatica fallita. Apertura interfaccia per inserimento manuale...")
        manual_frames = select_frames_interactively_gui(args.input_video)
        if manual_frames["cancelled"]:
            raise RuntimeError("Processo annullato dall'utente.")

    os.makedirs(args.output_dir, exist_ok=True)
    
    if manual_frames and not manual_frames["cancelled"]:
        fast_start_frame = manual_frames["fast"]
        slow_start_frame = manual_frames["slow"]
        fast_end_frame = fast_start_frame + int(32 * fps) if fps > 0 else fast_start_frame + 960
        slow_end_frame = slow_start_frame + int(70 * fps) if fps > 0 else slow_start_frame + 2100
        print("Punti di taglio calcolati da input manuale.")
    else:
        t0 += int(5 * fps) if fps > 0 else 150
        fast_start_frame = t0
        fast_end_frame = t0 + int(32 * fps) if fps > 0 else t0 + 960
        slow_start_frame = t0 + int((32 + 7) * fps) if fps > 0 else t0 + 1170
        slow_end_frame = slow_start_frame + int(70 * fps) if fps > 0 else slow_start_frame + 2100
        print("Punti di taglio calcolati da ricerca automatica.")

    cut_points_path = os.path.join(args.output_dir, 'cut_points.csv')
    try:
        with open(cut_points_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['segment_name', 'start_frame', 'end_frame'])
            writer.writerow(['fast', fast_start_frame, fast_end_frame])
            writer.writerow(['slow', slow_start_frame, slow_end_frame])
        print(f"Punti di taglio salvati correttamente in: '{cut_points_path}'")
    except IOError as e:
        raise IOError(f"Errore durante il salvataggio di cut_points.csv: {e}")

    print("La creazione dei video 'trimmed' è stata saltata per ottimizzare il processo.")