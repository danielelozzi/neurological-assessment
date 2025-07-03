import pandas as pd
import numpy as np
import os
import argparse
import cv2
import matplotlib.pyplot as plt
import seaborn as sns

# Costanti per l'analisi
VELOCITY_THRESHOLD = 0.001
FPS = 30 
PUPIL_COL_NAME = 'pupil_diameter_mean'

def get_video_dimensions(video_path):
    """Apre un video per leggerne le dimensioni."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ATTENZIONE: Impossibile aprire il video {video_path} per leggere le dimensioni. Le heatmap potrebbero non essere generate.")
        return None, None
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def load_data(args):
    """Carica e unisce tutti i dati necessari, calcolando la media della pupilla."""
    try:
        base_dir = args.data_dir
        analysis_path = os.path.join(base_dir, os.path.splitext(args.intermediate_video_name)[0] + "_analysis.csv")
        df_analysis = pd.read_csv(analysis_path)

        pupil_path = os.path.join(base_dir, '3d_eye_states.csv')
        df_pupil = pd.read_csv(pupil_path)
        
        left_col, right_col = 'pupil diameter left [mm]', 'pupil diameter right [mm]'
        if left_col in df_pupil.columns and right_col in df_pupil.columns:
            df_pupil[PUPIL_COL_NAME] = df_pupil[[left_col, right_col]].mean(axis=1) #
        else:
            print(f"ATTENZIONE: Colonne '{left_col}' o '{right_col}' non trovate. L'analisi della pupilla sarà vuota.")
            df_pupil[PUPIL_COL_NAME] = np.nan

        df_pupil = df_pupil.rename(columns={'timestamp [ns]': 'pupil_timestamp_ns'})
        df_pupil['pupil_timestamp_ns'] = pd.to_datetime(df_pupil['pupil_timestamp_ns'], unit='ns')
        
        df_timestamps = pd.read_csv(os.path.join(base_dir, 'world_timestamps.csv'))
        df_timestamps['world_index'] = df_timestamps.index
        df_timestamps = df_timestamps.rename(columns={'timestamp [ns]': 'world_timestamp_ns'})
        df_timestamps['world_timestamp_ns'] = pd.to_datetime(df_timestamps['world_timestamp_ns'], unit='ns')
        
        df_aligned_pupil = pd.merge_asof(
            df_timestamps.sort_values('world_timestamp_ns'),
            df_pupil.sort_values('pupil_timestamp_ns'),
            left_on='world_timestamp_ns', right_on='pupil_timestamp_ns',
            direction='nearest', tolerance=pd.Timedelta('100ms')
        )
        
        df_analysis = df_analysis.merge(
            df_aligned_pupil[['world_index', PUPIL_COL_NAME]],
            left_on='frame_input', right_on='world_index', how='left'
        )

        df_cuts = pd.read_csv(os.path.join(base_dir, 'cut_points.csv'))
        return df_analysis, df_cuts
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Errore nel caricamento dei file: {e}. Eseguire prima gli altri script.")

def segment_movements(df_segment):
    """Segmenta i movimenti della palla e restituisce una lista di dataframe, uno per ogni movimento."""
    df_segment['vx'] = df_segment['ball_center_x_norm'].diff()
    df_segment['vy'] = df_segment['ball_center_y_norm'].diff()
    df_segment['speed'] = np.sqrt(df_segment['vx']**2 + df_segment['vy']**2)

    conditions = [
        (df_segment['speed'] < VELOCITY_THRESHOLD),
        (df_segment['speed'] >= VELOCITY_THRESHOLD) & (df_segment['vx'].abs() > df_segment['vy'].abs()) & (df_segment['vx'] > 0),
        (df_segment['speed'] >= VELOCITY_THRESHOLD) & (df_segment['vx'].abs() > df_segment['vy'].abs()) & (df_segment['vx'] < 0),
        (df_segment['speed'] >= VELOCITY_THRESHOLD) & (df_segment['vy'].abs() >= df_segment['vx'].abs()) & (df_segment['vy'] > 0),
        (df_segment['speed'] >= VELOCITY_THRESHOLD) & (df_segment['vy'].abs() >= df_segment['vx'].abs()) & (df_segment['vy'] < 0)
    ]
    directions = ['still', 'right', 'left', 'down', 'up']
    df_segment['direction'] = np.select(conditions, directions, default='still')
    
    df_segment['block'] = (df_segment['direction'] != df_segment['direction'].shift()).cumsum()
    
    movement_segments = []
    for block_num, group in df_segment[df_segment['direction'] != 'still'].groupby('block'):
        if len(group) < 3: continue 
        movement_segments.append(group.copy())
        
    return movement_segments

def generate_heatmap(gaze_data, output_path, title, width, height):
    """Genera e salva una heatmap dei punti di sguardo."""
    if gaze_data.empty or gaze_data[['gaze_x_norm', 'gaze_y_norm']].isnull().all().all():
        print(f"Nessun dato di sguardo per la heatmap '{title}'. Salto.")
        return
    
    plt.figure(figsize=(10, (height/width)*10))
    sns.kdeplot(
        x=gaze_data['gaze_x_norm'] * width,
        y=gaze_data['gaze_y_norm'] * height,
        fill=True,
        thresh=0.05,
        cmap="viridis",
        cbar=True
    ).set(xlim=(0, width), ylim=(height, 0))
    plt.title(title)
    plt.xlabel("Larghezza (pixel)")
    plt.ylabel("Altezza (pixel)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"Heatmap salvata in: {output_path}")

def generate_pupil_plot(movements_by_direction, output_path, title):
    """Genera e salva un grafico con l'andamento medio della pupilla per direzione."""
    plt.figure(figsize=(12, 7))
    
    for direction, segments in movements_by_direction.items():
        if not segments: continue
        
        # Normalizza i dati sulla pupilla su una base temporale comune (0-100)
        resampled_pupils = []
        normalized_time = np.linspace(0, 100, 101)
        
        for seg in segments:
            pupil_data = seg[PUPIL_COL_NAME].dropna()
            if len(pupil_data) < 2: continue
            
            original_time = np.linspace(0, 100, len(pupil_data))
            resampled_pupil = np.interp(normalized_time, original_time, pupil_data)
            resampled_pupils.append(resampled_pupil)
            
        if not resampled_pupils: continue
        
        mean_pupil_trend = np.mean(resampled_pupils, axis=0)
        std_pupil_trend = np.std(resampled_pupils, axis=0)
        
        plt.plot(normalized_time, mean_pupil_trend, label=f'Movimento {direction}')
        plt.fill_between(normalized_time, mean_pupil_trend - std_pupil_trend, mean_pupil_trend + std_pupil_trend, alpha=0.2)

    plt.title(title)
    plt.xlabel("Tempo Normalizzato del Movimento (%)")
    plt.ylabel("Diametro Medio Pupilla (mm)")
    plt.legend()
    plt.grid(True, linestyle='--')
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"Grafico pupillometria salvato in: {output_path}")

def main(args):
    """Funzione principale per generare il report Excel e le visualizzazioni."""
    print("Caricamento e unione dei dati di analisi...")
    df_analysis, df_cuts = load_data(args)
    
    video_path = os.path.join(args.data_dir, args.intermediate_video_name)
    vid_width, vid_height = get_video_dimensions(video_path)
    if vid_width is None: return

    # Crea la cartella per i grafici se non esiste
    plot_dir = os.path.join(args.data_dir, "report_plots")
    os.makedirs(plot_dir, exist_ok=True)
    
    writer = pd.ExcelWriter(args.output_excel, engine='openpyxl')
    
    for _, row in df_cuts.iterrows():
        segment_name = row['segment_name']
        start_frame, end_frame = int(row['start_frame']), int(row['end_frame'])
        
        if pd.isna(start_frame) or pd.isna(end_frame) or start_frame == -1:
            print(f"Segmento '{segment_name}' non valido. Salto.")
            continue
        
        print(f"\n--- Analisi del segmento: {segment_name.upper()} (Frame {start_frame}-{end_frame}) ---")
        
        df_segment_data = df_analysis[
            (df_analysis['frame_input'] >= start_frame) & 
            (df_analysis['frame_input'] < end_frame)
        ].copy()
        
        if df_segment_data.empty:
            print("Nessun dato trovato per questo segmento.")
            continue
            
        # 1. Heatmap generale del segmento
        heatmap_path = os.path.join(plot_dir, f"heatmap_generale_{segment_name}.png")
        generate_heatmap(df_segment_data, heatmap_path, f"Heatmap Generale - Segmento {segment_name.capitalize()}", vid_width, vid_height)

        # 2. Segmentazione e analisi dei micro-movimenti
        movement_blocks = segment_movements(df_segment_data)
        if not movement_blocks:
            print("Nessun movimento significativo trovato in questo segmento.")
            continue
            
        movements_by_direction = {'up': [], 'down': [], 'left': [], 'right': []}
        all_metrics = []

        for move in movement_blocks:
            direction = move['direction'].iloc[0]
            if direction in movements_by_direction:
                movements_by_direction[direction].append(move)
            
            # Calcolo metriche per il report Excel (come prima)
            start_f, end_f = move.iloc[0], move.iloc[-1]
            dist = np.sqrt((end_f['ball_center_x_norm'] - start_f['ball_center_x_norm'])**2 + (end_f['ball_center_y_norm'] - start_f['ball_center_y_norm'])**2)
            duration_s = (len(move) - 1) / FPS
            gaze_entered = move[move['gaze_in_box']]
            latency_s = (gaze_entered.iloc[0]['frame_output'] - start_f['frame_output']) / FPS if not gaze_entered.empty else np.nan
            
            all_metrics.append({
                'direction': direction,
                'ball_speed': dist / duration_s if duration_s > 0 else 0,
                'gaze_latency_s': latency_s,
                'gaze_in_box_count': move['gaze_in_box'].sum(),
                'avg_pupil_dilation_mm': move[PUPIL_COL_NAME].mean()
            })
        
        # 3. Heatmap per ogni direzione
        for direction, segments in movements_by_direction.items():
            if segments:
                combined_df = pd.concat(segments)
                heatmap_dir_path = os.path.join(plot_dir, f"heatmap_{segment_name}_{direction}.png")
                generate_heatmap(combined_df, heatmap_dir_path, f"Heatmap Movimento '{direction.capitalize()}' - Segmento {segment_name.capitalize()}", vid_width, vid_height)

        # 4. Grafico pupillometria per il segmento
        pupil_plot_path = os.path.join(plot_dir, f"pupillometria_{segment_name}.png")
        generate_pupil_plot(movements_by_direction, pupil_plot_path, f"Andamento Medio Pupilla - Segmento {segment_name.capitalize()}")

        # 5. Salvataggio dati Excel
        df_metrics = pd.DataFrame(all_metrics)
        df_summary = df_metrics.groupby('direction').agg(
            avg_ball_speed=('ball_speed', 'mean'),
            avg_gaze_latency_s=('gaze_latency_s', 'mean'),
            avg_gaze_in_box_count=('gaze_in_box_count', 'mean'),
            avg_pupil_dilation_mm=('avg_pupil_dilation_mm', 'mean'),
            trial_count=('direction', 'size')
        ).reset_index()
        
        df_summary.to_excel(writer, sheet_name=f"Riepilogo_{segment_name}", index=False)
        df_metrics.to_excel(writer, sheet_name=f"Dettagli_{segment_name}", index=False)
        print(f"Dati per '{segment_name}' salvati nel report Excel.")

    writer.close()
    print(f"\nReport Excel finale salvato in: {args.output_excel}")
    print(f"Tutti i grafici e le heatmap sono stati salvati nella cartella: {plot_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Genera un report Excel e visualizzazioni (heatmap, grafici) dai dati analizzati.")
    parser.add_argument('--data_dir', default='.', help="Cartella contenente tutti i file CSV e video di input.")
    parser.add_argument('--intermediate_video_name', default='output_final_analysis.mp4', help="Nome del video intermedio per analisi e dimensioni.")
    parser.add_argument('--output_excel', default='final_report.xlsx', help="Percorso del file Excel di output.")
    args = parser.parse_args()
    
    try:
        main(args)
    except Exception as e:
        print(f"Si è verificato un errore critico: {e}")