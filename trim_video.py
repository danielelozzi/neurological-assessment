import cv2
import easyocr
import os
import sys
import csv

# --- MODIFICA RADICALE: Funzione potenziata con pre-elaborazione dell'immagine ---
def detect_text_ocr(frame, reader, text_to_find='1'):
    """
    Usa EasyOCR su un'immagine pre-elaborata per massimizzare l'accuratezza
    in video di bassa qualità, concentrandosi sul centro dello schermo.
    """
    # 1. Definiamo una Zona di Interesse (ROI) al centro del frame
    h, w, _ = frame.shape
    roi_x_start = int(w * 0.25)
    roi_y_start = int(h * 0.25)
    roi_x_end = int(w * 0.75)
    roi_y_end = int(h * 0.75)
    
    roi = frame[roi_y_start:roi_y_end, roi_x_start:roi_x_end]

    # 2. Applichiamo filtri per "pulire" l'immagine
    # Convertiamo in scala di grigi
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Applichiamo una sfumatura per ridurre il rumore
    blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
    
    # Applichiamo un thresholding adattivo per far risaltare il testo
    # È molto efficace in condizioni di luce non uniformi
    processed_roi = cv2.adaptiveThreshold(blurred, 255, 
                                          cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)

    # 3. Eseguiamo l'OCR sull'immagine elaborata
    results = reader.readtext(processed_roi, allowlist='0123456789', detail=0)
    
    # Controlliamo se il testo cercato è nei risultati
    for text in results:
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

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        raise ValueError("Errore: Impossibile leggere la durata del video.")
    stop_frame_threshold = total_frames // 3
    print(f"Video di {total_frames} frame. Il processo si interromperà se l'innesco non viene trovato entro il frame {stop_frame_threshold}.")


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

    detection_goal = 2
    frame_tolerance = 5
    detections_found = 0
    last_detection_frame = -1
    
    print(f"Scansione di '{os.path.basename(args.input_video)}' per trovare {detection_goal} rilevamenti di '1' con una tolleranza di {frame_tolerance} frame...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if not one_confirmed and frame_number > stop_frame_threshold:
            cap.release()
            raise RuntimeError(f"ERRORE: Innesco non trovato dopo aver analizzato 1/3 del video (frame {frame_number}). Processo interrotto.")

        if frame_number % 30 == 0:
            print(f"Scansione in corso... Frame: {frame_number}/{total_frames}", end='\r')

        is_one_present = detect_text_ocr(frame, reader, '1')

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
                print(f"\n{' ' * 70}\rRilevamento del numero '1' confermato intorno al frame {frame_number}. Attesa della sua scomparsa...")
        
        elif one_confirmed and not is_one_present:
            t0 = frame_number
            print(f"Punto di riferimento trovato! t0 = frame {t0}")
            break
        
        frame_number += 1

    print(" " * 70, end='\r')

    cap.release()
    if t0 == -1:
        if frame_number <= stop_frame_threshold:
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