import cv2
import numpy as np
import pandas as pd
import os
import sys
import argparse
#from ultralytics import YOLO

# --- Variabili globali per le dimensioni dell'output ---
output_width = None
output_height = None

#======================================================================
# FUNZIONI DI RILEVAMENTO DELLA PALLA
#======================================================================

def detect_ball_yolo(frame, model, sports_ball_class_id):
    """
    Rileva la palla usando il modello YOLOv8.
    Restituisce la bounding box e le coordinate normalizzate della palla.
    """
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

def detect_ball_hough(frame):
    """
    Rileva la palla usando la Trasformata di Hough per Cerchi di OpenCV.
    Restituisce la bounding box e le coordinate normalizzate della palla.
    """
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (9, 9), 2)
    circles = cv2.HoughCircles(gray_frame, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
                               param1=50, param2=30, minRadius=5, maxRadius=100)
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

#======================================================================
# FUNZIONI AUSILIARIE E PRINCIPALE
#======================================================================

def align_timestamps_and_filter(world_timestamps_path, gaze_data_path):
    """Allinea i timestamp del video con i dati di sguardo."""
    print("Allineamento dei timestamp...")
    try:
        world_timestamps = pd.read_csv(world_timestamps_path)
        # --- MODIFICA CHIAVE: Aggiunge la colonna world_index dall'indice del DataFrame ---
        world_timestamps['world_index'] = world_timestamps.index

        gaze = pd.read_csv(gaze_data_path)
        gaze.rename(columns={'gaze position on surface x [normalized]': 'gaze_x_norm', 'gaze position on surface y [normalized]': 'gaze_y_norm'}, inplace=True)
        gaze_on_surface = gaze[gaze['gaze detected on surface'] == True].copy()
        world_timestamps.rename(columns={'timestamp [ns]': 'world_timestamp_ns'}, inplace=True)
        gaze_on_surface.rename(columns={'timestamp [ns]': 'gaze_timestamp_ns'}, inplace=True)
        world_timestamps['world_timestamp_ns'] = pd.to_datetime(world_timestamps['world_timestamp_ns'], unit='ns')
        gaze_on_surface['gaze_timestamp_ns'] = pd.to_datetime(gaze_on_surface['gaze_timestamp_ns'], unit='ns')
        world_timestamps.sort_values(by='world_timestamp_ns', inplace=True)
        gaze_on_surface.sort_values(by='gaze_timestamp_ns', inplace=True)
        aligned_data = pd.merge_asof(
            world_timestamps, gaze_on_surface,
            left_on='world_timestamp_ns', right_on='gaze_timestamp_ns',
            direction='nearest', tolerance=pd.Timedelta('100ms')
        )
        print("Allineamento dei timestamp completato.")
        return aligned_data
    except (FileNotFoundError, KeyError) as e:
        sys.exit(f"Errore durante l'allineamento dei timestamp: {e}")

def main(args):
    """Funzione principale per raddrizzare la prospettiva, rilevare la palla e verificare la posizione dello sguardo."""
    global output_width, output_height
    
    BBOX_PADDING_FACTOR = 1.20
    
    aligned_gaze_data = align_timestamps_and_filter(args.world_timestamps, args.gaze_csv)
    if aligned_gaze_data.empty: sys.exit("Errore: Dati di allineamento vuoti.")

    try:
        surface_positions = pd.read_csv(args.surface_positions)
        # Questa verifica è ora una salvaguardia, ma non dovrebbe essere necessaria se il file è corretto
        if 'world_index' not in surface_positions.columns:
            print("ATTENZIONE: 'world_index' non trovato in surface_positions.csv. Lo creo dall'indice.")
            surface_positions['world_index'] = surface_positions.index
    except FileNotFoundError: sys.exit(f"Errore: Il file '{args.surface_positions}' non è stato trovato.")

    model, sports_ball_class_id = None, None
    if args.use_yolo:
        try:
            print("Caricamento del modello YOLOv8...")
            model = YOLO(args.yolo_model)
            classes = model.names
            sports_ball_class_id = list(classes.keys())[list(classes.values()).index('sports ball')]
            print("Modello YOLOv8 caricato.")
        except (Exception, ValueError) as e: sys.exit(f"Errore caricamento modello YOLOv8: {e}")
    else:
        print("Modalità di rilevamento: Trasformata di Hough per Cerchi.")

    cap = cv2.VideoCapture(args.input_video)
    if not cap.isOpened(): sys.exit(f"Errore: Impossibile aprire il file video {args.input_video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None
    analysis_results = []

    frame_count = 0
    processed_frame_count = 0
    
    while cap.isOpened():
        ret, original_frame = cap.read()
        if not ret: break

        # Ora 'world_index' è garantito esistere in aligned_gaze_data
        current_frame_gaze_info = aligned_gaze_data[aligned_gaze_data['world_index'] == frame_count]
        if current_frame_gaze_info.empty:
            frame_count += 1
            continue
        gaze_info = current_frame_gaze_info.iloc[0]

        crop_info = surface_positions[surface_positions['world_index'] == frame_count]
        if crop_info.empty or crop_info[['tl x [px]', 'tl y [px]']].isnull().values.any():
            frame_count += 1
            continue

        try:
            src_pts = np.float32([[crop_info[f'{corner} x [px]'].iloc[0], crop_info[f'{corner} y [px]'].iloc[0]] for corner in ['tl', 'tr', 'br', 'bl']])
            center = np.mean(src_pts, axis=0)
            padding_factor = 1.05 
            expanded_src_pts = np.array([center + (p - center) * padding_factor for p in src_pts], dtype=np.float32)
            src_pts = expanded_src_pts

            if output_width is None:
                output_width = int(max(np.linalg.norm(src_pts[0] - src_pts[1]), np.linalg.norm(src_pts[3] - src_pts[2])))
                output_height = int(max(np.linalg.norm(src_pts[0] - src_pts[3]), np.linalg.norm(src_pts[1] - src_pts[2])))
                print(f"Dimensioni del video di output impostate a: {output_width}x{output_height}")
                
            dst_pts = np.float32([[0, 0], [output_width - 1, 0], [output_width - 1, output_height - 1], [0, output_height - 1]])
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_frame = cv2.warpPerspective(original_frame, matrix, (output_width, output_height))
        except Exception as e:
            print(f"Errore trasformazione prospettica al frame {frame_count}: {e}")
            frame_count += 1
            continue
        
        if out is None:
            out = cv2.VideoWriter(args.output_video, fourcc, fps, (output_width, output_height))

        if args.use_yolo:
            ball_bbox, norm_ball_x, norm_ball_y = detect_ball_yolo(warped_frame, model, sports_ball_class_id)
        else:
            ball_bbox, norm_ball_x, norm_ball_y = detect_ball_hough(warped_frame)

        gaze_in_box_status = False 
        
        bbox_corners_norm = {
            'tl_x': None, 'tl_y': None, 'tr_x': None, 'tr_y': None,
            'br_x': None, 'br_y': None, 'bl_x': None, 'bl_y': None
        }
        gaze_color = (0, 0, 255) # Rosso di default

        if ball_bbox is not None:
            x, y, w, h = ball_bbox
            w_new, h_new = w * BBOX_PADDING_FACTOR, h * BBOX_PADDING_FACTOR
            x_new, y_new = x - (w_new - w) / 2, y - (h_new - h) / 2
            enlarged_bbox = (int(x_new), int(y_new), int(w_new), int(h_new))
            
            cv2.rectangle(warped_frame, (enlarged_bbox[0], enlarged_bbox[1]), (enlarged_bbox[0] + enlarged_bbox[2], enlarged_bbox[1] + enlarged_bbox[3]), (255, 0, 0), 2)
            
            ex, ey, ew, eh = enlarged_bbox
            bbox_corners_norm.update({
                'tl_x': ex / output_width, 'tl_y': ey / output_height,
                'tr_x': (ex + ew) / output_width, 'tr_y': ey / output_height,
                'br_x': (ex + ew) / output_width, 'br_y': (ey + eh) / output_height,
                'bl_x': ex / output_width, 'bl_y': (ey + eh) / output_height
            })
            
            current_gaze_x, current_gaze_y = gaze_info['gaze_x_norm'], gaze_info['gaze_y_norm']
            if pd.notna(current_gaze_x) and pd.notna(current_gaze_y):
                gaze_pixel_x, gaze_pixel_y = int(current_gaze_x * output_width), int(current_gaze_y * output_height)
                if (ex <= gaze_pixel_x <= ex + ew) and (ey <= gaze_pixel_y <= ey + eh):
                    gaze_in_box_status = True
                    gaze_color = (255, 255, 0) # Ciano
        
        current_gaze_x, current_gaze_y = gaze_info['gaze_x_norm'], gaze_info['gaze_y_norm']
        if pd.notna(current_gaze_x) and pd.notna(current_gaze_y):
            gaze_pixel_x, gaze_pixel_y = int(current_gaze_x * output_width), int(current_gaze_y * output_height)
            cv2.circle(warped_frame, (gaze_pixel_x, gaze_pixel_y), 10, gaze_color, -1)
        
        analysis_results.append({
            'frame_input': frame_count, 'frame_output': processed_frame_count,
            'ball_center_x_norm': norm_ball_x, 'ball_center_y_norm': norm_ball_y,
            'gaze_x_norm': current_gaze_x, 'gaze_y_norm': current_gaze_y,
            'gaze_in_box': gaze_in_box_status,
            'bbox_tl_x_norm': bbox_corners_norm['tl_x'], 'bbox_tl_y_norm': bbox_corners_norm['tl_y'],
            'bbox_tr_x_norm': bbox_corners_norm['tr_x'], 'bbox_tr_y_norm': bbox_corners_norm['tr_y'],
            'bbox_br_x_norm': bbox_corners_norm['br_x'], 'bbox_br_y_norm': bbox_corners_norm['br_y'],
            'bbox_bl_x_norm': bbox_corners_norm['bl_x'], 'bbox_bl_y_norm': bbox_corners_norm['bl_y'],
        })
        
        out.write(warped_frame)
        processed_frame_count += 1
        
        # cv2.imshow('Video con Analisi', warped_frame) # Commentato per non richiedere GUI
        # if cv2.waitKey(1) & 0xFF == ord('q'): break
        frame_count += 1

    cap.release()
    if out: out.release()
    cv2.destroyAllWindows()
    
    if analysis_results:
        coords_df = pd.DataFrame(analysis_results)
        coords_output_path = os.path.splitext(args.output_video)[0] + "_analysis.csv"
        coords_df.to_csv(coords_output_path, index=False)
        print(f"Dati di analisi dettagliati salvati in {coords_output_path}")

    print(f"Elaborazione completata. Salvati {processed_frame_count} frame analizzati.")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="Rileva una palla, raddrizza la prospettiva e analizza lo sguardo.")
    parser.add_argument('--use_yolo', action='store_true', help="Usa il modello YOLO. Se non specificato, usa Hough Circle Transform.")
    parser.add_argument('--input_video', default=os.path.join(script_dir, 'video.mp4'), help="Percorso del video di input.")
    parser.add_argument('--output_video', default=os.path.join(script_dir, 'output_final_analysis.mp4'), help="Percorso per salvare il video con l'analisi completa.")
    parser.add_argument('--world_timestamps', default=os.path.join(script_dir, 'world_timestamps.csv'), help="Percorso del file world_timestamps.csv.")
    parser.add_argument('--gaze_csv', default=os.path.join(script_dir, 'gaze.csv'), help="Percorso del file gaze.csv.")
    parser.add_argument('--surface_positions', default=os.path.join(script_dir, 'surface_positions.csv'), help="Percorso del file surface_positions.csv con i 4 angoli.")
    parser.add_argument('--yolo_model', default='yolov8x.pt', help="Percorso del modello YOLOv8 (usato solo con --use_yolo).")
    args = parser.parse_args()
    main(args)