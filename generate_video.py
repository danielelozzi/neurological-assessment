import cv2
import numpy as np
import pandas as pd
import os

def draw_text(img, text, pos, font_scale=0.6, color=(255, 255, 255), thickness=1, bg_color=None):
    """Disegna testo con un possibile sfondo per una migliore leggibilità."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
    text_w, text_h = text_size
    
    if bg_color:
        # Disegna un rettangolo di sfondo
        cv2.rectangle(img, (pos[0], pos[1] - text_h - 4), (pos[0] + text_w, pos[1]), bg_color, -1)
    
    # Disegna il testo
    cv2.putText(img, text, (pos[0], pos[1] - 5), font, font_scale, color, thickness, cv2.LINE_AA)

def main(args):
    """
    Genera i video finali con overlay basandosi sui dati di analisi pre-calcolati.
    """
    print("\n--- FASE 3: Generazione Video con Overlay Avanzati ---")

    # Caricamento dei dati necessari
    if not os.path.exists(args.analysis_csv):
        raise FileNotFoundError(f"File di analisi non trovato: {args.analysis_csv}")
    if not os.path.exists(args.input_video):
        raise FileNotFoundError(f"Video di input non trovato: {args.input_video}")
    if not os.path.exists(args.surface_positions):
        raise FileNotFoundError(f"File posizioni superficie non trovato: {args.surface_positions}")

    df_analysis = pd.read_csv(args.analysis_csv)
    df_surface = pd.read_csv(args.surface_positions)
    if 'world_index' not in df_surface.columns:
        df_surface['world_index'] = df_surface.index

    # Unisci i dati di analisi con le posizioni della superficie
    df_merged = pd.merge(df_analysis, df_surface, left_on='frame', right_on='world_index', how='left')

    cap = cv2.VideoCapture(args.input_video)
    if not cap.isOpened():
        raise IOError(f"Impossibile aprire il video {args.input_video}")
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Raggruppa per segmento per creare video separati
    for segment_name, segment_df in df_merged.groupby('segment_name'):
        print(f"  - Elaborazione video per il segmento: '{segment_name}'...")
        
        if segment_df.empty:
            continue

        # Imposta il video writer (le dimensioni sono determinate al primo frame valido)
        out = None
        output_video_path = os.path.join(args.output_dir, f"final_video_{segment_name}.mp4")

        # Itera su ogni frame del segmento
        for _, row in segment_df.iterrows():
            frame_idx = int(row['frame'])
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, original_frame = cap.read()
            if not ret:
                continue

            # Esegui la correzione della prospettiva
            try:
                src_pts = np.array([[row[f'{c} x [px]'], row[f'{c} y [px]']] for c in ['tl', 'tr', 'br', 'bl']], dtype=np.float32)
                
                if out is None: # Inizializza il video writer al primo frame
                    w1 = np.linalg.norm(src_pts[0] - src_pts[1])
                    w2 = np.linalg.norm(src_pts[3] - src_pts[2])
                    output_width = int(max(w1, w2))
                    h1 = np.linalg.norm(src_pts[0] - src_pts[3])
                    h2 = np.linalg.norm(src_pts[1] - src_pts[2])
                    output_height = int(max(h1, h2))
                    if output_width <= 0 or output_height <= 0: continue
                    fourcc = cv2.VideoWriter.fourcc(*'mp4v')
                    out = cv2.VideoWriter(output_video_path, fourcc, fps, (output_width, output_height))

                dst_pts = np.array([[0, 0], [output_width - 1, 0], [output_width - 1, output_height - 1], [0, output_height - 1]], dtype=np.float32)
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped_frame = cv2.warpPerspective(original_frame, matrix, (output_width, output_height))
            except Exception:
                continue

            # --- Disegna gli overlay ---
            
            # 1. Cerchio dello sguardo e box di inseguimento
            gaze_color = (0, 0, 255) # Rosso di default
            if pd.notna(row['gaze_in_box']) and row['gaze_in_box']:
                gaze_color = (0, 255, 255) # Giallo se nel box
            
            if pd.notna(row['gaze_x_norm']) and pd.notna(row['gaze_y_norm']):
                gaze_px = int(row['gaze_x_norm'] * output_width)
                gaze_py = int(row['gaze_y_norm'] * output_height)
                cv2.circle(warped_frame, (gaze_px, gaze_py), 10, gaze_color, -1)

            if pd.notna(row['enlarged_bbox_x']):
                ex, ey, ew, eh = int(row['enlarged_bbox_x']), int(row['enlarged_bbox_y']), int(row['enlarged_bbox_w']), int(row['enlarged_bbox_h'])
                cv2.rectangle(warped_frame, (ex, ey), (ex + ew, ey + eh), (255, 0, 0), 2)

            # Se non siamo in un trial, non disegnamo altro
            if pd.isna(row['trial_id']) or row['trial_id'] == 0:
                if out: out.write(warped_frame)
                continue

            # 2. Linea di escursione direzionale
            if pd.notna(row['dir_ex_line_coord']):
                line_coord = int(row['dir_ex_line_coord'])
                if row['direction_simple'] in ['up', 'down']:
                    cv2.line(warped_frame, (0, line_coord), (output_width, line_coord), (0, 255, 255), 2)
                else: # left, right
                    cv2.line(warped_frame, (line_coord, 0), (line_coord, output_height), (0, 255, 255), 2)

            # 3. Testo percentuale Gaze-in-Box
            if pd.notna(row['running_gaze_in_box_perc']):
                perc_text = f"Inseguimento: {row['running_gaze_in_box_perc']:.0f}%"
                draw_text(warped_frame, perc_text, (10, 30), bg_color=(0,0,0,0.5))

            # 4. Testo successo Escursione
            if pd.notna(row['excursion_success']) and row['excursion_success']:
                draw_text(warped_frame, "SUCCESSO INSEGUIMENTO", (10, 60), color=(0, 255, 0), bg_color=(0,0,0,0.5))

            # 5. Testo successo Escursione Direzionale
            if pd.notna(row['directional_excursion_success']) and row['directional_excursion_success']:
                draw_text(warped_frame, "OBIETTIVO RAGGIUNTO", (10, 90), color=(0, 255, 255), bg_color=(0,0,0,0.5))

            # 6. Nome dell'evento corrente
            if pd.notna(row['direction_simple']):
                event_text = f"EVENTO: {str(row['direction_simple']).upper()}"
                draw_text(warped_frame, event_text, (10, 120), color=(255, 165, 0), bg_color=(0,0,0,0.5))

            if out:
                out.write(warped_frame)

        if out:
            out.release()
            print(f"  -> Video con overlay salvato in: '{output_video_path}'")

    cap.release()
    cv2.destroyAllWindows()
    print("--- Generazione Video Completata ---")