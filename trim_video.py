import cv2
import easyocr
import os
import sys
import csv
import tkinter as tk
from tkinter import messagebox
import concurrent.futures

# --- NUOVO: Finestra GUI per l'inserimento manuale dei frame ---
def get_manual_frames_gui():
    """
    Mostra una finestra per permettere all'utente di inserire manualmente i frame
    di inizio per i segmenti 'fast' e 'slow'.
    """
    root = tk.Tk()
    root.withdraw() # Nasconde la finestra principale di Tkinter
    
    # Crea una finestra di dialogo personalizzata
    dialog = tk.Toplevel(root)
    dialog.title("Inserimento Manuale Frame")
    dialog.geometry("400x200")

    tk.Label(dialog, text="La ricerca automatica non ha avuto successo.\nInserisci manualmente i frame di inizio:", wraplength=380).pack(pady=10)

    frame_fast_val = tk.StringVar()
    frame_slow_val = tk.StringVar()

    form_frame = tk.Frame(dialog)
    tk.Label(form_frame, text="Frame Inizio 'Fast':").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    tk.Entry(form_frame, textvariable=frame_fast_val).grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(form_frame, text="Frame Inizio 'Slow':").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    tk.Entry(form_frame, textvariable=frame_slow_val).grid(row=1, column=1, padx=5, pady=5)
    form_frame.pack(pady=5)

    result = {"fast": None, "slow": None, "cancelled": True}

    def on_confirm():
        try:
            fast_start = int(frame_fast_val.get())
            slow_start = int(frame_slow_val.get())
            if fast_start >= 0 and slow_start >= 0:
                result["fast"] = fast_start
                result["slow"] = slow_start
                result["cancelled"] = False
                dialog.destroy()
            else:
                messagebox.showwarning("Input non valido", "I numeri dei frame devono essere positivi.")
        except ValueError:
            messagebox.showwarning("Input non valido", "Per favore, inserisci solo numeri interi.")

    def on_cancel():
        dialog.destroy()

    button_frame = tk.Frame(dialog)
    tk.Button(button_frame, text="Annulla", command=on_cancel).pack(side="right", padx=10)
    tk.Button(button_frame, text="Conferma", command=on_confirm).pack(side="right")
    button_frame.pack(pady=10)
    
    # Centra la finestra e attendi che venga chiusa
    dialog.transient(root)
    dialog.grab_set()
    root.wait_window(dialog)
    
    root.destroy()
    return result

# --- Pipeline di pre-elaborazione ---
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

# --- La funzione ora orchestra i thread paralleli ---
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
                    # --- CORREZIONE QUI ---
                    # Ho sostituito le virgolette doppie interne con quelle singole per risolvere il SyntaxError
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
        manual_frames = get_manual_frames_gui()
        if manual_frames["cancelled"]:
            raise RuntimeError("Processo annullato dall'utente.")

    os.makedirs(args.output_dir, exist_ok=True)
    
    if manual_frames:
        fast_start_frame = manual_frames["fast"]
        slow_start_frame = manual_frames["slow"]
        fast_end_frame = fast_start_frame + int(32 * fps)
        slow_end_frame = slow_start_frame + int(70 * fps)
        print("Punti di taglio calcolati da input manuale.")
    else:
        t0 += int(5 * fps)
        fast_start_frame = t0
        fast_end_frame = t0 + int(32 * fps)
        slow_start_frame = t0 + int((32 + 7) * fps)
        slow_end_frame = slow_start_frame + int(70 * fps)
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
