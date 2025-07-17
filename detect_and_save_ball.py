import cv2
import numpy as np
import pandas as pd
import os
import sys
from ultralytics import YOLO

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

def detect_ball_hough(frame):
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
        direction='nearest', tolerance=pd.Timedelta('100ms')
    )
    print("Allineamento completato.")
    return aligned_data

def main(args):
    BBOX_PADDING_FACTOR = 1.20
    world_timestamps_path = os.path.join(args.input_dir, 'world_timestamps.csv')
    gaze_csv_path = os.path.join(args.input_dir, 'gaze.csv')
    surface_positions_path = os.path.join(args.input_dir, 'surface_positions.csv')
    input_video_path = os.path.join(args.input_dir, 'video.mp4')
    cut_points_path = os.path.join(args.output_dir, 'cut_points.csv')

    for f in [world_timestamps_path, gaze_csv_path, surface_positions_path, input_video_path, cut_points_path]:
        if not os.path.exists(f): raise FileNotFoundError(f"File di input richiesto non trovato: {f}")

    aligned_gaze_data = align_timestamps_and_filter(world_timestamps_path, gaze_csv_path)
    if aligned_gaze_data.empty: raise ValueError("Errore: Dati di allineamento vuoti.")

    surface_positions = pd.read_csv(surface_positions_path)
    if 'world_index' not in surface_positions.columns:
        surface_positions['world_index'] = surface_positions.index
        
    df_cuts = pd.read_csv(cut_points_path)

    model, sports_ball_class_id = None, None
    if args.use_yolo:
        if not os.path.exists(args.yolo_model): raise FileNotFoundError(f"Modello YOLO non trovato: {args.yolo_model}")
        print(f"Caricamento del modello YOLOv8 da {args.yolo_model}...")
        model = YOLO(args.yolo_model)
        classes = model.names
        sports_ball_class_id = list(classes.keys())[list(classes.values()).index('sports ball')]
        print("Modello YOLOv8 caricato.")
    else:
        print("Modalità di rilevamento: Trasformata di Hough per Cerchi.")

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened(): raise IOError(f"Errore: Impossibile aprire il video {input_video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    os.makedirs(args.output_dir, exist_ok=True)
    analysis_results = []
    
    for _, cut_row in df_cuts.iterrows():
        segment_name = cut_row['segment_name']
        start_frame = int(cut_row['start_frame'])
        end_frame = int(cut_row['end_frame'])
        
        print(f"\n--- Elaborazione del segmento: '{segment_name}' (Frame {start_frame}-{end_frame}) ---")

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame_count = start_frame
        
        output_video_path = os.path.join(args.output_dir, f"final_video_{segment_name}.mp4")
        out = None
        output_width, output_height = None, None

        in_movement = False
        current_movement_direction = ""
        last_known_zone = 'center'

        while frame_count < end_frame:
            ret, original_frame = cap.read()
            if not ret:
                print(f"ATTENZIONE: Interruzione anticipata del video prima del frame {end_frame}.")
                break
            
            current_frame_gaze_info = aligned_gaze_data[aligned_gaze_data['world_index'] == frame_count]
            crop_info = surface_positions[surface_positions['world_index'] == frame_count]

            if current_frame_gaze_info.empty or crop_info.empty or crop_info[['tl x [px]', 'tl y [px]']].isnull().values.any():
                frame_count += 1
                continue
            
            gaze_info = current_frame_gaze_info.iloc[0]

            try:
                src_pts = np.float32([[crop_info[f'{corner} x [px]'].iloc[0], crop_info[f'{corner} y [px]'].iloc[0]] for corner in ['tl', 'tr', 'br', 'bl']])
                
                if output_width is None:
                    output_width = int(max(np.linalg.norm(src_pts[0] - src_pts[1]), np.linalg.norm(src_pts[3] - src_pts[2])))
                    output_height = int(max(np.linalg.norm(src_pts[0] - src_pts[3]), np.linalg.norm(src_pts[1] - src_pts[2])))
                    print(f"Dimensioni video di output per '{segment_name}': {output_width}x{output_height}")
                
                dst_pts = np.float32([[0, 0], [output_width - 1, 0], [output_width - 1, output_height - 1], [0, output_height - 1]])
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped_frame = cv2.warpPerspective(original_frame, matrix, (output_width, output_height))
                warped_frame = cv2.convertScaleAbs(warped_frame)
            except Exception as e:
                print(f"Errore prospettiva al frame {frame_count}: {e}")
                frame_count += 1
                continue
            
            if out is None:
                out = cv2.VideoWriter(output_video_path, fourcc, fps, (output_width, output_height))
            
            if args.use_yolo:
                ball_bbox, norm_ball_x, norm_ball_y = detect_ball_yolo(warped_frame, model, sports_ball_class_id)
            else:
                ball_bbox, norm_ball_x, norm_ball_y = detect_ball_hough(warped_frame)

            current_zone = get_zone(norm_ball_x, norm_ball_y)

            if not in_movement and last_known_zone == 'center' and current_zone not in ['center', 'other']:
                in_movement = True
                current_movement_direction = current_zone.upper()
            elif in_movement and current_zone == 'center':
                in_movement = False
                current_movement_direction = ""
            
            last_known_zone = current_zone
            
            if current_movement_direction:
                cv2.putText(
                    warped_frame, 
                    current_movement_direction,
                    (50, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    2,
                    (0, 255, 255),
                    3,
                    cv2.LINE_AA
                )

            gaze_in_box_status, gaze_color = False, (0, 0, 255)
            if ball_bbox is not None:
                x, y, w, h = ball_bbox
                w_new, h_new = w * BBOX_PADDING_FACTOR, h * BBOX_PADDING_FACTOR
                x_new, y_new = x - (w_new - w) / 2, y - (h_new - h) / 2
                enlarged_bbox = (int(x_new), int(y_new), int(w_new), int(h_new))
                cv2.rectangle(warped_frame, (enlarged_bbox[0], enlarged_bbox[1]), (enlarged_bbox[0] + enlarged_bbox[2], enlarged_bbox[1] + enlarged_bbox[3]), (255, 0, 0), 2)
                
                ex, ey, ew, eh = enlarged_bbox
                if pd.notna(gaze_info['gaze_x_norm']) and pd.notna(gaze_info['gaze_y_norm']):
                    gaze_px, gaze_py = int(gaze_info['gaze_x_norm'] * output_width), int(gaze_info['gaze_y_norm'] * output_height)
                    if (ex <= gaze_px <= ex + ew) and (ey <= gaze_py <= ey + eh):
                        gaze_in_box_status, gaze_color = True, (0, 255, 255)

            if pd.notna(gaze_info['gaze_x_norm']) and pd.notna(gaze_info['gaze_y_norm']):
                gaze_px, gaze_py = int(gaze_info['gaze_x_norm'] * output_width), int(gaze_info['gaze_y_norm'] * output_height)
                cv2.circle(warped_frame, (gaze_px, gaze_py), 10, gaze_color, -1)
            
            result_data = {
                'frame': frame_count,
                'ball_center_x_norm': norm_ball_x, 
                'ball_center_y_norm': norm_ball_y, 
                'gaze_x_norm': gaze_info['gaze_x_norm'], 
                'gaze_y_norm': gaze_info['gaze_y_norm'], 
                'gaze_in_box': gaze_in_box_status
            }
            analysis_results.append(result_data)
            
            out.write(warped_frame)
            frame_count += 1
        
        if out:
            out.release()
            print(f"Video corretto per '{segment_name}' salvato in '{output_video_path}'")
        
    cap.release()
    cv2.destroyAllWindows()
    
    if analysis_results:
        coords_df = pd.DataFrame(analysis_results)
        coords_output_path = os.path.join(args.output_dir, "output_final_analysis_analysis.csv")
        coords_df.to_csv(coords_output_path, index=False)
        print(f"\nDati di analisi dettagliati salvati in {coords_output_path}")

    print(f"\nElaborazione di tutti i segmenti completata.")