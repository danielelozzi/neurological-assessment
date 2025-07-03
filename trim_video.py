import cv2
import easyocr
import os
import sys
import argparse
import csv

# --- FUNZIONI AUSILIARIE ---

def detect_text_ocr(frame, reader, text_to_find='1'):
    """Rileva se un testo specifico è presente nel frame usando EasyOCR."""
    # L'allowlist è ottimizzata per cercare solo il carattere '1'
    results = reader.readtext(frame, allowlist='1')
    for (bbox, text, prob) in results:
        if text_to_find in text:
            return True
    return False

def save_video_segment(input_video_path, output_video_path, start_frame, end_frame, total_frames):
    """Taglia un segmento di video da un file di input e lo salva in un file di output."""
    if start_frame == -1 or end_frame == -1 or start_frame >= end_frame:
        print(f"Segmento non valido per '{output_video_path}' (start: {start_frame}, end: {end_frame}). Salto il salvataggio.")
        return
        
    if start_frame >= total_frames:
        print(f"ATTENZIONE: Il frame di inizio ({start_frame}) è oltre la fine del video ({total_frames}). Salto il salvataggio di '{output_video_path}'.")
        return
    
    if end_frame > total_frames:
        print(f"ATTENZIONE: Il frame di fine ({end_frame}) è stato corretto per corrispondere alla fine del video ({total_frames}).")
        end_frame = total_frames

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Errore: Impossibile aprire il video di input '{input_video_path}'")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    print(f"Salvataggio del segmento da frame {start_frame} a {end_frame} in '{output_video_path}'...")
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame

    while current_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        current_frame += 1

    cap.release()
    out.release()
    print(f"Video '{output_video_path}' salvato con successo.")

# --- FUNZIONE PRINCIPALE ---

def main(args):
    """
    Script principale che analizza il video originale per trovare un punto
    di riferimento (t0), e poi taglia due segmenti ("fast" e "slow")
    basati su durate fisse da quel punto.
    """
    # --- FASE 1: Ricerca del punto di riferimento t0 dal video originale ---
    print("\nFASE 1: Ricerca del punto di riferimento t0 dal video originale...")
    cap = cv2.VideoCapture(args.input_video)
    if not cap.isOpened():
        sys.exit(f"Errore: Impossibile aprire il video '{args.input_video}'")
    
    try:
        # Inizializza EasyOCR, usando la GPU se disponibile
        reader = easyocr.Reader(['en'], gpu=True)
    except Exception as e:
        sys.exit(f"Errore durante l'inizializzazione di EasyOCR. Dettagli: {e}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps == 0:
        sys.exit("Errore: Impossibile leggere gli FPS del video.")

    t0 = -1
    frame_number = 0
    
    # Variabili per un rilevamento robusto del numero '1'
    one_confirmed = False
    consecutive_one_frames = 0
    DETECTION_THRESHOLD = 2 # Numero di frame consecutivi richiesti per la conferma

    print(f"Scansione di '{args.input_video}' per trovare {DETECTION_THRESHOLD} frame consecutivi con il numero '1'...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        is_one_present = detect_text_ocr(frame, reader, '1')

        # Logica per la conferma robusta del numero '1'
        if not one_confirmed:
            if is_one_present:
                consecutive_one_frames += 1
            else:
                # Se la sequenza si interrompe, resetta il contatore
                consecutive_one_frames = 0
            
            if consecutive_one_frames >= DETECTION_THRESHOLD:
                one_confirmed = True
                print(f"Rilevamento del numero '1' confermato al frame {frame_number}. Ora in attesa della sua scomparsa.")

        # Se '1' è stato confermato e ora scompare, quello è il nostro t0
        elif one_confirmed and not is_one_present:
            t0 = frame_number 
            print(f"Punto di riferimento trovato! t0 = frame {t0}")
            break

        frame_number += 1
    
    cap.release()

    if t0 == -1:
        sys.exit("ERRORE: Impossibile trovare il punto di riferimento (scomparsa del numero '1' dopo una rilevazione stabile). Elaborazione interrotta.")

    # --- FASE 2: Calcolo dei punti di taglio basati su t0 e salvataggio dei metadati ---
    
    print("\nFASE 2: Calcolo dei punti di taglio basati su t0...")

    # Calcolo dei frame per il segmento "fast": da t0 per 30 secondi
    t0 += int(5 * fps)
    fast_start_frame = t0 
    fast_end_frame = t0 + int(32 * fps)
    
    # Calcolo dei frame per il segmento "slow": da t0+30+7 secondi per 67 secondi
    slow_start_frame = t0 + int((32 + 7) * fps)
    slow_end_frame = slow_start_frame + int(70 * fps)

    print(f"Segmento 'fast': da frame {fast_start_frame} a {fast_end_frame}")
    print(f"Segmento 'slow': da frame {slow_start_frame} a {slow_end_frame}")

    # Salvataggio dei punti di taglio in un file CSV per l'analisi successiva
    print("\nSalvataggio dei punti di taglio...")
    cut_points_path = os.path.join(args.output_dir, 'cut_points.csv')
    try:
        with open(cut_points_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['segment_name', 'start_frame', 'end_frame'])
            writer.writerow(['fast', fast_start_frame, fast_end_frame])
            writer.writerow(['slow', slow_start_frame, slow_end_frame])
        print(f"Punti di taglio salvati in '{cut_points_path}'")
    except IOError as e:
        sys.exit(f"Errore durante il salvataggio di cut_points.csv: {e}")

    # --- FASE 3: Creazione dei video finali tagliando dal video originale ---
    
    print("\nFASE 3: Creazione dei video finali tagliati...")
    # Taglia entrambi i segmenti dal video di input originale
    save_video_segment(args.input_video, args.output_video_fast, fast_start_frame, fast_end_frame, total_frames)
    save_video_segment(args.input_video, args.output_video_slow, slow_start_frame, slow_end_frame, total_frames)

    print("\nElaborazione di taglio completata.")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="Trova un punto di riferimento in un video e taglia due segmenti ('fast' e 'slow') con durate fisse dal video originale.")
    
    # MODIFICATO: L'input ora è il video originale 'video.mp4'
    parser.add_argument('--input_video', default=os.path.join(script_dir, 'output_final_analysis.mp4'), help="Percorso del video originale da analizzare e tagliare.")
    
    parser.add_argument('--output_dir', default='.', help="Cartella di output per i file generati (CSV e video tagliati).")
    parser.add_argument('--output_video_fast', default=os.path.join(script_dir, 'trimmed_video_fast.mp4'), help="Percorso del video 'fast' tagliato.")
    parser.add_argument('--output_video_slow', default=os.path.join(script_dir, 'trimmed_video_slow.mp4'), help="Percorso del video 'slow' tagliato.")
    
    args = parser.parse_args()
    
    # Crea la cartella di output se non esiste
    os.makedirs(args.output_dir, exist_ok=True)
    
    main(args)