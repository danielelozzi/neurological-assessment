import cv2
import numpy as np
import pandas as pd
import os
import sys
from ultralytics import YOLO

# --- NUOVA FUNZIONE: Esegue un Grid Search per i parametri di Hough ---
def find_optimal_hough_params(sample_frame):
    """
    Esegue una ricerca su una griglia di parametri per trovare la combinazione ottimale
    che rileva esattamente un cerchio in un frame di esempio.
    """
    print("INFO: Avvio ricerca parametri ottimali per Hough Circle...")
    gray_frame = cv2.cvtColor(sample_frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (9, 9), 2)
    height, width, _ = sample_frame.shape

    # 1. Definiamo la griglia di ricerca
    param1_values = [70, 50, 40, 30]  # Soglia Canny (da alta a bassa)
    param2_values = [40, 30, 20, 15]  # Accumulatore (da severo a permissivo)
    radius_ranges_perc = [
        (0.06, 0.12),  # Range "standard" (raggio tra 6% e 12% dell'altezza)
        (0.04, 0.08),  # Range "piccolo"
        (0.10, 0.20)   # Range "grande"
    ]

    # 2. Iteriamo sulla griglia per trovare la prima combinazione valida
    for p1 in param1_values:
        for p2 in param2_values:
            for r_min_perc, r_max_perc in radius_ranges_perc:
                min_r = int(height * r_min_perc)
                max_r = int(height * r_max_perc)
                
                circles = cv2.HoughCircles(gray_frame, cv2.HOUGH_GRADIENT, dp=1.2, 
                                           minDist=height, # Assicura di trovare al massimo un cerchio
                                           param1=p1, param2=p2,
                                           minRadius=min_r, maxRadius=max_r)
                
                if circles is not None and len(circles[0]) == 1:
                    # Successo! Trovata una combinazione che rileva un solo cerchio.
                    optimal_params = {'param1': p1, 'param2': p2, 'minRadius': min_r, 'maxRadius': max_r}
                    print(f"✅ Parametri ottimali trovati: {optimal_params}")
                    return optimal_params

    # 3. Se nessuna combinazione ha funzionato, ritorniamo un default e avvisiamo l'utente
    print("⚠️ ATTENZIONE: Nessuna combinazione di parametri ha prodotto un risultato ottimale. Uso i default.")
    return {'param1': 50, 'param2': 30, 'minRadius': int(height * 0.05), 'maxRadius': int(height * 0.15)}


def get_zone(x, y):
    """Determina in quale zona dello schermo si trova una coordinata normalizzata."""
    if x is None or y is None:
        return 'other'
    if 0.40 < x < 0.60 and 0.40 < y < 0.60:
        return 'center'
    if y <= 0.40:
        return 'up'
    if y >= 0.60:
        return 'down'
    if x <= 0.40:
        return 'left'
    if x >= 0.60:
        return 'right'
    return 'other'

def detect_ball_yolo(frame, model, sports_ball_class_id):
    results = model(frame, verbose=False)
    best_detection = None
    for r in results:
        for box in r.boxes:
            if int(box.cls) == sports_ball_class_id:
                if best_detection is None or box.conf[0] > best_detection.conf[0]:
                    best_detection = box
    if best_detection is not None and best_detection.conf[0] > 0.5:
        x1, y1, x2, y2 = best_detection.xyxy[0]
        ball_bbox = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
        h_frame, w_frame, _ = frame.shape
        norm_ball_x = (x1 + (x2 - x1) / 2) / w_frame
        norm_ball_y = (y1 + (y2 - y1) / 2) / h_frame
        return ball_bbox, norm_ball_x, norm_ball_y
    return None, None, None

# --- MODIFICA: La funzione ora accetta un dizionario di parametri ---
def detect_ball_hough(frame, hough_params):
    """
    Rileva il cerchio usando la Trasformata di Hough con parametri ottimizzati.
    """
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (9, 9), 2)
    
    circles = cv2.HoughCircles(gray_frame, cv2.HOUGH_GRADIENT, dp=1.2, 
                               minDist=int(frame.shape[0]), # Usa l'altezza per minDist
                               param1=hough_params['param1'], 
                               param2=hough_params['param2'], 
                               minRadius=hough_params['minRadius'], 
                               maxRadius=hough_params['maxRadius'])
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        (x, y, r) = circles[0]
        w, h = r * 2, r * 2
        x_tl, y_tl = x - r, y - r
        ball_bbox = (x_tl, y_tl, w, h)
        h_frame, w_frame, _ = frame.shape
        norm_ball_x = x / w_frame
        norm_ball_y = y / h_frame
        return ball_bbox, norm_ball_x, norm_ball_y
    return None, None, None

def align_timestamps_and_filter(world_timestamps_path, gaze_data_path):
    print("Allineamento dei timestamp...")
    world_timestamps = pd.read_csv(world_timestamps_path)
    if '# frame_idx' in world_timestamps.columns:
        world_timestamps.rename(columns={'# frame_idx': 'world_index'}, inplace=True)
    elif 'world_index' not in world_timestamps.columns:
        world_timestamps['world_index'] = world_timestamps.index

    gaze = pd.read_csv(gaze_data_path)
    gaze.rename(columns={'gaze position on surface x [normalized]': 'gaze_x_norm', 'gaze position on surface y [normalized]': 'gaze_y_norm'}, inplace=True)
    gaze_on_surface = gaze[gaze['gaze detected on surface'] == True].copy()

    if 'timestamp [ns]' in world_timestamps.columns:
         world_timestamps.rename(columns={'timestamp [ns]': 'world_timestamp_ns'}, inplace=True)
    if 'timestamp [ns]' in gaze_on_surface.columns:
        gaze_on_surface.rename(columns={'timestamp [ns]': 'gaze_timestamp_ns'}, inplace=True)
    elif 'timestamp [s]' in gaze_on_surface.columns:
        gaze_on_surface['gaze_timestamp_ns'] = (gaze_on_surface['timestamp [s]'] * 1e9).astype('int64')

    world_timestamps['world_timestamp_dt'] = pd.to_datetime(world_timestamps['world_timestamp_ns'], unit='ns')
    gaze_on_surface['gaze_timestamp_dt'] = pd.to_datetime(gaze_on_surface['gaze_timestamp_ns'], unit='ns')

    world_timestamps.sort_values(by='world_timestamp_dt', inplace=True)
    gaze_on_surface.sort_values(by='gaze_timestamp_dt', inplace=True)

    aligned_data = pd.merge_asof(
        world_timestamps, gaze_on_surface,
        left_on='world_timestamp_dt', right_on='gaze_timestamp_dt',
        direction='nearest', tolerance=pd.Timedelta('20ms')
    )
    print("Allineamento completato.")
    return aligned_data


def main(args):
    # --- CORREZIONE: Ho riorganizzato la logica per renderla più robusta ---

    world_timestamps_path = os.path.join(args.input_dir, 'world_timestamps.csv')
    gaze_csv_path = os.path.join(args.input_dir, 'gaze.csv')
    surface_positions_path = os.path.join(args.input_dir, 'surface_positions.csv')
    input_video_path = os.path.join(args.input_dir, 'video.mp4')
    cut_points_path = os.path.join(args.output_dir, 'cut_points.csv')

    # Validazione dei file di input
    for f in [world_timestamps_path, gaze_csv_path, surface_positions_path, input_video_path, cut_points_path]:
        if not os.path.exists(f):
            raise FileNotFoundError(f"File di input richiesto non trovato: {f}")

    # Preparazione dei dati
    aligned_gaze_data = align_timestamps_and_filter(world_timestamps_path, gaze_csv_path)
    if aligned_gaze_data.empty:
        raise ValueError("Errore: Dati di allineamento vuoti.")

    surface_positions = pd.read_csv(surface_positions_path)
    if 'world_index' not in surface_positions.columns:
        surface_positions['world_index'] = surface_positions.index

    df_cuts = pd.read_csv(cut_points_path)

    # Configurazione del modello di rilevamento
    model, sports_ball_class_id = None, None
    if args.use_yolo:
        if not os.path.exists(args.yolo_model):
            raise FileNotFoundError(f"Modello YOLO non trovato: {args.yolo_model}")
        print(f"Caricamento del modello YOLOv8 da {args.yolo_model}...")
        model = YOLO(args.yolo_model)
        classes = model.names
        sports_ball_class_id = list(classes.keys())[list(classes.values()).index('sports ball')]
        print("Modello YOLOv8 caricato.")
    else:
        print("Modalità di rilevamento: Trasformata di Hough per Cerchi (con ricerca parametri automatica).")

    # Inizializzazione video
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise IOError(f"Errore: Impossibile aprire il video {input_video_path}")    
    analysis_results = []

    # --- NUOVA OTTIMIZZAZIONE ---
    # Inizializziamo i parametri Hough una sola volta per evitare di ricalcolarli per ogni segmento.
    global_hough_params, global_params_found = None, False

    # Ciclo principale sui segmenti (fast/slow)
    for _, cut_row in df_cuts.iterrows():
        segment_name = cut_row['segment_name']
        start_frame = int(cut_row['start_frame'])
        end_frame = int(cut_row['end_frame'])

        print(f"\n--- Elaborazione del segmento: '{segment_name}' (Frame {start_frame}-{end_frame}) ---")
        output_width, output_height = 0, 0 # Verranno determinate al primo frame valido
        frame_count = start_frame
        while frame_count < end_frame:
            # --- CORREZIONE LOGICA ---
            # 1. Imposta la posizione esatta del frame che vogliamo leggere.
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            # 2. Leggi SUBITO DOPO il frame a quella posizione.
            ret, original_frame = cap.read()
            if not ret:
                print(f"ATTENZIONE: Interruzione anticipata del video prima del frame {end_frame}.")
                break

            # Recupera informazioni su sguardo e superficie per il frame corrente
            current_frame_gaze_info = aligned_gaze_data[aligned_gaze_data['world_index'] == frame_count]
            crop_info = surface_positions[surface_positions['world_index'] == frame_count]

            # Salta il frame se mancano dati essenziali
            if current_frame_gaze_info.empty or crop_info.empty or crop_info[['tl x [px]', 'tl y [px]']].isnull().values.any():
                print(f"INFO: Dati di sguardo o superficie mancanti per il frame {frame_count}. Salto.")
                frame_count += 1
                continue
            
            gaze_info = current_frame_gaze_info.iloc[0]
            warped_frame = None

            # Tenta di eseguire la correzione della prospettiva
            try:
                src_pts = np.array([[crop_info[f'{corner} x [px]'].iloc[0], crop_info[f'{corner} y [px]'].iloc[0]] for corner in ['tl', 'tr', 'br', 'bl']], dtype=np.float32)
                
                if output_width == 0: # Calcola le dimensioni solo una volta
                    w1 = np.linalg.norm(src_pts[0] - src_pts[1])
                    w2 = np.linalg.norm(src_pts[3] - src_pts[2])
                    output_width = int(max(w1, w2))

                    h1 = np.linalg.norm(src_pts[0] - src_pts[3])
                    h2 = np.linalg.norm(src_pts[1] - src_pts[2])
                    output_height = int(max(h1, h2))

                    if output_width <= 0 or output_height <= 0:
                        print(f"ATTENZIONE: Dimensioni del frame non valide ({output_width}x{output_height}), salto il frame {frame_count}")
                        frame_count += 1
                        continue

                # Ora che le dimensioni sono note, calcola la trasformazione
                dst_pts = np.array([[0, 0], [output_width - 1, 0], [output_width - 1, output_height - 1], [0, output_height - 1]], dtype=np.float32)
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped_frame = cv2.warpPerspective(original_frame, matrix, (output_width, output_height))

            except Exception as e:
                print(f"Errore di elaborazione prospettiva al frame {frame_count}: {e}")
                frame_count += 1
                continue

            # --- Da qui in poi, siamo sicuri che 'warped_frame' e 'out' sono validi ---

            # Rilevamento della palla (YOLO o Hough)
            if not args.use_yolo and not global_params_found:
                global_hough_params = find_optimal_hough_params(warped_frame)
                global_params_found = True

            ball_bbox, norm_ball_x, norm_ball_y = None, np.nan, np.nan
            if args.use_yolo:
                ball_bbox, norm_ball_x, norm_ball_y = detect_ball_yolo(warped_frame, model, sports_ball_class_id)
            else:
                ball_bbox, norm_ball_x, norm_ball_y = detect_ball_hough(warped_frame, global_hough_params)

            # Logica per disegnare overlay (direzione, gaze, box)
            gaze_in_box_status, gaze_color = False, (0, 0, 255)
            enlarged_bbox_coords = {'x': np.nan, 'y': np.nan, 'w': np.nan, 'h': np.nan}
            if ball_bbox is not None:
                x, y, w, h = ball_bbox
                w_new, h_new = w * args.bbox_padding_factor, h * args.bbox_padding_factor
                x_new, y_new = x - (w_new - w) / 2, y - (h_new - h) / 2
                enlarged_bbox = (int(x_new), int(y_new), int(w_new), int(h_new))
                enlarged_bbox_coords = {'x': enlarged_bbox[0], 'y': enlarged_bbox[1], 'w': enlarged_bbox[2], 'h': enlarged_bbox[3]}
                
                ex, ey, ew, eh = enlarged_bbox
                if pd.notna(gaze_info['gaze_x_norm']) and pd.notna(gaze_info['gaze_y_norm']):
                    gaze_px, gaze_py = int(gaze_info['gaze_x_norm'] * output_width), int(gaze_info['gaze_y_norm'] * output_height)
                    if (ex <= gaze_px <= ex + ew) and (ey <= gaze_py <= ey + eh):
                        gaze_in_box_status, gaze_color = True, (0, 255, 255)
            
            # Calcolo delle dimensioni normalizzate della palla
            norm_ball_w, norm_ball_h = np.nan, np.nan
            if ball_bbox is not None:
                _, _, w, h = ball_bbox
                norm_ball_w = w / output_width
                norm_ball_h = h / output_height
            
            # Salvataggio dei risultati di analisi per questo frame
            result_data = {
                'frame': frame_count, 'ball_center_x_norm': norm_ball_x, 'ball_center_y_norm': norm_ball_y,
                'ball_w_norm': norm_ball_w, 'ball_h_norm': norm_ball_h, 'gaze_x_norm': gaze_info['gaze_x_norm'],
                'gaze_y_norm': gaze_info['gaze_y_norm'], 'gaze_in_box': gaze_in_box_status,
                'enlarged_bbox_x': enlarged_bbox_coords['x'], 'enlarged_bbox_y': enlarged_bbox_coords['y'],
                'enlarged_bbox_w': enlarged_bbox_coords['w'], 'enlarged_bbox_h': enlarged_bbox_coords['h'],
                'segment_name': segment_name
            }
            analysis_results.append(result_data)

            frame_count += 1

    # Chiusura finale
    cap.release()

    if analysis_results:
        coords_df = pd.DataFrame(analysis_results)
        coords_output_path = os.path.join(args.output_dir, "output_final_analysis_analysis.csv")
        coords_df.to_csv(coords_output_path, index=False)
        print(f"\nDati di analisi dettagliati salvati in {coords_output_path}")

    print(f"\nElaborazione di tutti i segmenti completata.")