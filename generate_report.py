import pandas as pd
import numpy as np
import os
import argparse
import cv2
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import interp1d

# --- Costanti ---
PUPIL_COL_NAME = 'pupil_diameter_mean'

def get_video_dimensions(video_path):
    """Legge le dimensioni (larghezza, altezza) da un file video."""
    if not os.path.exists(video_path):
        print(f"ATTENZIONE: File video non trovato in {video_path}. Impossibile ottenere le dimensioni.")
        return 1920, 1080
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ATTENZIONE: Impossibile aprire il video {video_path}. Usando dimensioni di default.")
        return 1920, 1080
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def calculate_movement_data(df):
    """
    Funzione chiave per calcolare 'direction', 'trial_id' e 'ball_speed'
    partendo dalle coordinate della palla.
    """
    print("INFO: Inizio calcolo di 'direction', 'trial_id' e 'ball_speed'...")

    # 1. Definizione delle zone (basato su coordinate normalizzate)
    def get_zone(x, y):
        if 0.40 < x < 0.60 and 0.40 < y < 0.60:
            return 'center'
        if y <= 0.40: return 'up'
        if y >= 0.60: return 'down'
        if x <= 0.40: return 'left'
        if x >= 0.60: return 'right'
        return 'other'

    df['zone'] = df.apply(lambda row: get_zone(row['ball_center_x_norm'], row['ball_center_y_norm']), axis=1)
    df['prev_zone'] = df['zone'].shift(1)

    # 2. Identificazione dei trial e delle direzioni
    df['direction'] = ''
    df['trial_id'] = 0
    trial_counter = 0
    current_trial_id = 0
    current_direction = ''

    for i in range(1, len(df)):
        # Un trial inizia quando la palla esce dal centro
        if df.loc[i, 'prev_zone'] == 'center' and df.loc[i, 'zone'] != 'center' and df.loc[i, 'zone'] != 'other':
            trial_counter += 1
            current_trial_id = trial_counter
            current_direction = f"center_to_{df.loc[i, 'zone']}"
        
        # Un trial finisce quando la palla ritorna al centro o va in 'other'
        elif df.loc[i, 'zone'] == 'center' or df.loc[i, 'zone'] == 'other':
            current_trial_id = 0
            current_direction = ''
        
        df.loc[i, 'trial_id'] = current_trial_id
        df.loc[i, 'direction'] = current_direction

    # 3. Calcolo della velocità della palla
    df['prev_x'] = df['ball_center_x_norm'].shift(1)
    df['prev_y'] = df['ball_center_y_norm'].shift(1)
    
    # Calcola la distanza Euclidea tra il frame corrente e il precedente
    df['ball_speed'] = np.sqrt((df['ball_center_x_norm'] - df['prev_x'])**2 + (df['ball_center_y_norm'] - df['prev_y'])**2)
    # Imposta la velocità a 0 per il primo frame di ogni trial per evitare salti
    df.loc[df['trial_id'] != df['trial_id'].shift(1), 'ball_speed'] = 0

    # Rimuove le colonne ausiliarie
    df.drop(columns=['zone', 'prev_zone', 'prev_x', 'prev_y'], inplace=True)
    
    print(f"INFO: Calcolo completato. Trovati {trial_counter} trial.")
    return df


def load_and_prepare_data(args):
    """Carica i dati e li prepara, calcolando le colonne mancanti."""
    base_dir = args.data_dir
    analysis_path = os.path.join(base_dir, 'output_final_analysis_analysis.csv')
    if not os.path.exists(analysis_path):
        print(f"ERRORE: Il file di analisi '{analysis_path}' non è stato trovato.")
        return None, None, None
    df_analysis = pd.read_csv(analysis_path)

    # Rinomina la colonna dei frame
    if 'frame_input' in df_analysis.columns:
        df_analysis.rename(columns={'frame_input': 'frame'}, inplace=True)
    else:
        print(f"\nERRORE CRITICO: La colonna 'frame_input' non è stata trovata.")
        return None, None, None

    # --- CALCOLO DEI DATI DI MOVIMENTO ---
    df_analysis = calculate_movement_data(df_analysis)

    cuts_path = os.path.join(base_dir, 'cut_points.csv')
    if not os.path.exists(cuts_path):
        print(f"ERRORE: Il file dei punti di taglio '{cuts_path}' non è stato trovato.")
        return None, None, None
    df_cuts = pd.read_csv(cuts_path)

    video_path = os.path.join(args.data_dir, args.intermediate_video_name)
    width, height = get_video_dimensions(video_path)
    return df_analysis, df_cuts, (width, height)


def add_pupil_data(df_main, base_dir):
    """Tenta di aggiungere i dati di pupillometria."""
    print("\n--- Tentativo di aggiungere dati di pupillometria (Opzionale) ---")
    timestamps_path = os.path.join(base_dir, 'world_timestamps.csv')
    if not os.path.exists(timestamps_path):
        df_main[PUPIL_COL_NAME] = np.nan
        return df_main
    df_timestamps = pd.read_csv(timestamps_path)
    df_timestamps.rename(columns={'# frame_idx': 'frame', 'timestamp [s]': 'timestamp'}, inplace=True)
    
    if 'frame' not in df_timestamps.columns:
        df_main[PUPIL_COL_NAME] = np.nan
        return df_main
        
    df_main = pd.merge(df_main, df_timestamps[['frame', 'timestamp']], on='frame', how='left')

    pupil_path = os.path.join(base_dir, '3d_eye_states.csv')
    if not os.path.exists(pupil_path) or 'timestamp' not in df_main.columns:
        df_main[PUPIL_COL_NAME] = np.nan
        return df_main
    df_pupil = pd.read_csv(pupil_path)
    if 'timestamp [s]' in df_pupil.columns:
        df_pupil.rename(columns={'timestamp [s]': 'timestamp'}, inplace=True)

    left_col, right_col = 'pupil diameter left [mm]', 'pupil diameter right [mm]'
    if left_col in df_pupil.columns and right_col in df_pupil.columns:
        df_pupil[PUPIL_COL_NAME] = df_pupil[[left_col, right_col]].mean(axis=1)
    else:
        df_main[PUPIL_COL_NAME] = np.nan
        return df_main

    df_main = pd.merge_asof(df_main.sort_values('timestamp'),
                              df_pupil[['timestamp', PUPIL_COL_NAME]].dropna().sort_values('timestamp'),
                              on='timestamp',
                              direction='nearest')
    print("INFO: Dati di pupillometria aggiunti con successo.")
    return df_main


def generate_gaze_heatmap(df_gaze, width, height, output_path):
    """Genera e salva una heatmap dello sguardo."""
    # --- CORREZIONE: Usa i nomi corretti delle colonne 'gaze_x_norm' e 'gaze_y_norm' ---
    if df_gaze.empty or 'gaze_x_norm' not in df_gaze.columns or df_gaze['gaze_x_norm'].isnull().all():
        return
        
    plt.figure(figsize=(width / 100, height / 100))
    plt.style.use('dark_background')
    sns.kdeplot(x=df_gaze['gaze_x_norm'] * width, y=df_gaze['gaze_y_norm'] * height,
                fill=True, cmap="inferno", thresh=0.05, alpha=0.7)
    plt.xlim(0, width); plt.ylim(height, 0); plt.axis('off')
    plt.title(os.path.basename(output_path).replace('.png', ''), color='white')
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, transparent=True); plt.close()
    print(f"Heatmap salvata: {output_path}")


def generate_pupillometry_plot(df_trials, pupil_col, output_path):
    """Genera il grafico della pupillometria se i dati sono disponibili."""
    if pupil_col not in df_trials.columns or df_trials[pupil_col].isnull().all(): return

    aligned_trials = []
    normalized_time = np.linspace(0, 100, 100)
    # Filtra solo per trial validi
    for trial_id, group in df_trials[df_trials['trial_id'] > 0].groupby('trial_id'):
        group = group.dropna(subset=[pupil_col])
        if len(group) < 2: continue
        relative_time = np.linspace(0, 100, len(group))
        interp_func = interp1d(relative_time, group[pupil_col], kind='linear', fill_value="extrapolate")
        aligned_trials.append(interp_func(normalized_time))

    if not aligned_trials: return
    mean_pupil, std_pupil = np.mean(aligned_trials, axis=0), np.std(aligned_trials, axis=0)
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(10, 6))
    plt.plot(normalized_time, mean_pupil, label='Diametro Pupillare Medio', color='royalblue')
    plt.fill_between(normalized_time, mean_pupil - std_pupil, mean_pupil + std_pupil, color='cornflowerblue', alpha=0.3, label='Deviazione Standard')
    plt.title(f"Andamento Pupillometrico Medio - {os.path.basename(output_path).replace('.png', '')}")
    plt.xlabel("Percentuale di Completamento del Movimento (%)"); plt.ylabel("Diametro Pupillare Medio [mm]")
    plt.legend(); plt.grid(True); plt.savefig(output_path); plt.close()
    print(f"Grafico pupillometria salvato: {output_path}")


def main(args):
    """Funzione principale per orchestrare l'analisi e la generazione del report."""
    plot_dir = os.path.join(args.data_dir, "plots_and_heatmaps")
    os.makedirs(plot_dir, exist_ok=True)

    df_main, df_cuts, (vid_width, vid_height) = load_and_prepare_data(args)
    if df_main is None: return

    df_main = add_pupil_data(df_main, args.data_dir)

    writer = pd.ExcelWriter(args.output_excel, engine='xlsxwriter')
    print("\n--- Inizio Analisi Statistica per Segmento (basata su frame) ---")

    for _, cut_row in df_cuts.iterrows():
        segment_name, start_frame, end_frame = cut_row['segment_name'], cut_row['start_frame'], cut_row['end_frame']
        print(f"\n elaborazione del segmento: '{segment_name}' (Frame {start_frame}-{end_frame})...")
        df_segment = df_main[(df_main['frame'] >= start_frame) & (df_main['frame'] <= end_frame)].copy()
        if df_segment.empty: continue

        total_gaze_in_box_perc = df_segment['gaze_in_box'].mean() * 100
        df_center_out = df_segment[df_segment['direction'].str.startswith('center_to_', na=False)].copy()
        if df_center_out.empty: 
            print("ATTENZIONE: Nessun movimento in uscita dal centro trovato in questo segmento.")
            continue
            
        df_center_out['direction_simple'] = df_center_out['direction'].str.split('_').str[-1]
        summary_by_direction = df_center_out.groupby('direction_simple').agg(
            avg_gaze_in_box_perc=('gaze_in_box', 'mean'),
            avg_ball_speed_mps=('ball_speed', 'mean'),
            trial_count=('trial_id', 'nunique')
        ).reset_index()
        summary_by_direction['avg_gaze_in_box_perc'] *= 100
        summary_by_direction['total_segment_gaze_in_box_perc'] = total_gaze_in_box_perc
        
        summary_by_direction.to_excel(writer, sheet_name=f"Riepilogo_{segment_name}", index=False)
        df_center_out.to_excel(writer, sheet_name=f"Dettagli_{segment_name}", index=False)
        print(f"Statistiche per '{segment_name}' salvate nel report Excel.")

        for direction in summary_by_direction['direction_simple']:
            df_direction = df_center_out[df_center_out['direction_simple'] == direction]
            heatmap_path = os.path.join(plot_dir, f"heatmap_{segment_name}_{direction}.png")
            
            # --- CORREZIONE: Passa l'intero dataframe, la funzione ora sa quali colonne usare ---
            generate_gaze_heatmap(df_direction, vid_width, vid_height, heatmap_path)
            
            pupil_plot_path = os.path.join(plot_dir, f"pupillometry_{segment_name}_{direction}.png")
            generate_pupillometry_plot(df_direction, PUPIL_COL_NAME, pupil_plot_path)

    writer.close()
    print(f"\n--- Report Excel Finale Salvato in: {args.output_excel} ---")
    print(f"--- Grafici e Heatmap salvati nella cartella: {plot_dir} ---")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Genera un report Excel e visualizzazioni, calcolando direzione e velocità dai dati grezzi.")
    parser.add_argument('--data_dir', default='.', help="Cartella contenente tutti i file CSV e video di input.")
    parser.add_argument('--intermediate_video_name', default='output_final_analysis.mp4', help="Nome del video per ottenere le dimensioni per le heatmap.")
    parser.add_argument('--output_excel', default='final_report.xlsx', help="Percorso del report Excel finale da generare.")
    
    args = parser.parse_args()
    main(args)