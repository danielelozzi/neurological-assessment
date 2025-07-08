import cv2
import easyocr
import os
import sys
import csv

def detect_text_ocr(frame, reader, text_to_find='1'):
    results = reader.readtext(frame, allowlist='1')
    for (bbox, text, prob) in results:
        if text_to_find in text:
            return True
    return False

def save_video_segment(input_video_path, output_video_path, start_frame, end_frame, total_frames):
    if start_frame == -1 or end_frame == -1 or start_frame >= end_frame:
        print(f"Segmento non valido per '{os.path.basename(output_video_path)}' (start: {start_frame}, end: {end_frame}). Salto il salvataggio.")
        return
    if start_frame >= total_frames:
        print(f"ATTENZIONE: Il frame di inizio ({start_frame}) è oltre la fine del video ({total_frames}). Salto il salvataggio.")
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

    print(f"Salvataggio del segmento da frame {start_frame} a {end_frame} in '{os.path.basename(output_video_path)}'...")
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame

    while current_frame < end_frame:
        ret, frame = cap.read()
        if not ret: break
        out.write(frame)
        current_frame += 1

    cap.release()
    out.release()
    print(f"Video '{os.path.basename(output_video_path)}' salvato con successo.")

def main(args):
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
        print("GPU non disponibile per EasyOCR, uso la CPU.")
        reader = easyocr.Reader(['en'], gpu=False)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps == 0: raise ValueError("Errore: Impossibile leggere gli FPS del video.")

    t0 = -1
    frame_number = 0
    one_confirmed = False
    consecutive_one_frames = 0
    DETECTION_THRESHOLD = 2

    print(f"Scansione di '{os.path.basename(args.input_video)}' per trovare {DETECTION_THRESHOLD} frame consecutivi con '1'...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        is_one_present = detect_text_ocr(frame, reader, '1')

        if not one_confirmed:
            if is_one_present:
                consecutive_one_frames += 1
            else:
                consecutive_one_frames = 0
            if consecutive_one_frames >= DETECTION_THRESHOLD:
                one_confirmed = True
                print(f"Rilevamento del numero '1' confermato al frame {frame_number}. Attesa della scomparsa.")
        elif one_confirmed and not is_one_present:
            t0 = frame_number 
            print(f"Punto di riferimento trovato! t0 = frame {t0}")
            break
        frame_number += 1
    
    cap.release()
    if t0 == -1: raise RuntimeError("ERRORE: Impossibile trovare il punto di riferimento (scomparsa del numero '1').")

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
        print(f"Punti di taglio salvati in '{cut_points_path}'")
    except IOError as e:
        raise IOError(f"Errore durante il salvataggio di cut_points.csv: {e}")

    output_video_fast = os.path.join(args.output_dir, 'trimmed_video_fast.mp4')
    output_video_slow = os.path.join(args.output_dir, 'trimmed_video_slow.mp4')
    save_video_segment(args.input_video, output_video_fast, fast_start_frame, fast_end_frame, total_frames)
    save_video_segment(args.input_video, output_video_slow, slow_start_frame, slow_end_frame, total_frames)

# Blocco non più necessario, la GUI chiama direttamente main(args)
# if __name__ == '__main__':
#     ...