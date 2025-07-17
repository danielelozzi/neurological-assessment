import cv2
import easyocr
import os
import sys
import csv

def detect_text_ocr(frame, reader, text_to_find='1'):
    """Usa EasyOCR per trovare un testo specifico in un frame."""
    results = reader.readtext(frame, allowlist='1')
    for (bbox, text, prob) in results:
        if text_to_find in text:
            return True
    return False

def main(args):
    """
    Funzione principale che analizza il video, trova i punti di inizio/fine
    dei segmenti 'fast' e 'slow' e salva solo il file 'cut_points.csv'.
    """
    print("\nFASE 1: Ricerca del punto di riferimento t0...")
    if not os.path.exists(args.input_video):
        raise FileNotFoundError(f"Video di input non trovato: {args.input_video}")

    cap = cv2.VideoCapture(args.input_video)
    if not cap.isOpened():
        raise IOError(f"Errore: Impossibile aprire il video '{args.input_video}'")

    try:
        reader = easyocr.Reader(['en'], gpu=True)
        print("EasyOCR inizializzato con GPU.")
    except Exception:
        print("GPU non disponibile per EasyOCR, ripiego su CPU (potrebbe essere più lento).")
        reader = easyocr.Reader(['en'], gpu=False)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        raise ValueError("Errore: Impossibile leggere gli FPS del video.")

    t0 = -1
    frame_number = 0
    one_confirmed = False
    consecutive_one_frames = 0
    DETECTION_THRESHOLD = 2

    print(f"Scansione di '{os.path.basename(args.input_video)}' per trovare {DETECTION_THRESHOLD} frame consecutivi con '1'...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        is_one_present = detect_text_ocr(frame, reader, '1')

        if not one_confirmed:
            if is_one_present:
                consecutive_one_frames += 1
            else:
                consecutive_one_frames = 0
            
            if consecutive_one_frames >= DETECTION_THRESHOLD:
                one_confirmed = True
                print(f"Rilevamento del numero '1' confermato al frame {frame_number}. Attesa della sua scomparsa...")
        
        elif one_confirmed and not is_one_present:
            t0 = frame_number
            print(f"Punto di riferimento trovato! t0 = frame {t0}")
            break
        
        frame_number += 1

    cap.release()
    if t0 == -1:
        raise RuntimeError("ERRORE: Impossibile trovare il punto di riferimento (scomparsa del numero '1'). Analisi interrotta.")

    os.makedirs(args.output_dir, exist_ok=True)
    
    t0 += int(5 * fps)
    fast_start_frame = t0
    fast_end_frame = t0 + int(32 * fps)
    slow_start_frame = t0 + int((32 + 7) * fps)
    slow_end_frame = slow_start_frame + int(70 * fps)
    
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