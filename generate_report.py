import pandas as pd
import numpy as np
import os
import cv2
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import interp1d

PUPIL_COL_NAME = 'pupil_diameter_mean'

def get_video_dimensions(video_path):
    if not os.path.exists(video_path): return 1920, 1080
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return 1920, 1080
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def calculate_movement_data(df):
    print("INFO: Inizio calcolo di 'direction', 'trial_id' e velocità...")
    def get_zone(x, y):
        if 0.40 < x < 0.60 and 0.40 < y < 0.60: return 'center'
        if y <= 0.40: return 'up'
        if y >= 0.60: return 'down'
        if x <= 0.40: return 'left'
        if x >= 0.60: return 'right'
        return 'other'
    df['zone'] = df.apply(lambda row: get_zone(row['ball_center_x_norm'], row['ball_center_y_norm']), axis=1)
    df['direction'], df['trial_id'] = '', 0
    trial_counter, in_trial, current_trial_id, current_direction = 0, False, 0, ''
    
    for i in range(1, len(df)):
        if not in_trial and df.loc[i-1, 'zone'] == 'center' and df.loc[i, 'zone'] not in ['center', 'other']:
            in_trial = True
            trial_counter += 1
            current_trial_id = trial_counter
            current_direction = f"center_to_{df.loc[i, 'zone']}"
        
        if in_trial:
            df.loc[i, 'trial_id'] = current_trial_id
            df.loc[i, 'direction'] = current_direction
        
        if in_trial and df.loc[i, 'zone'] == 'center':
            in_trial = False
            current_trial_id = 0
            current_direction = ''

    df['ball_speed'] = np.sqrt((df['ball_center_x_norm'].diff())**2 + (df['ball_center_y_norm'].diff())**2)
    df['gaze_speed'] = np.sqrt((df['gaze_x_norm'].diff())**2 + (df['gaze_y_norm'].diff())**2)
    df.loc[df['trial_id'] != df['trial_id'].shift(1), 'ball_speed'] = 0
    df.drop(columns=['zone'], inplace=True)
    print(f"INFO: Calcolo completato. Trovati {trial_counter} trial.")
    return df

def add_pupil_data(df_main, base_dir):
    print("\n--- Analisi Dati Pupillometrici ---")
    timestamps_path = os.path.join(base_dir, 'world_timestamps.csv') 
    pupil_path_main = os.path.join(base_dir, 'pupil_positions.csv')
    pupil_path_fallback = os.path.join(base_dir, '3d_eye_states.csv')
    
    pupil_path_to_use = None
    if os.path.exists(pupil_path_main):
        pupil_path_to_use = pupil_path_main
    elif os.path.exists(pupil_path_fallback):
        pupil_path_to_use = pupil_path_fallback
    
    if not os.path.exists(timestamps_path) or not pupil_path_to_use:
        df_main[PUPIL_COL_NAME] = np.nan
        print("ATTENZIONE: File di pupillometria o 'world_timestamps.csv' non trovati. Salto l'analisi pupillometrica.")
        return df_main
    
    print(f"INFO: Trovato file di pupillometria: '{os.path.basename(pupil_path_to_use)}'")
    df_timestamps = pd.read_csv(timestamps_path)
    
    if '# frame_idx' in df_timestamps.columns:
        df_timestamps.rename(columns={'# frame_idx': 'frame'}, inplace=True)
    elif 'frame_idx' in df_timestamps.columns:
        df_timestamps.rename(columns={'frame_idx': 'frame'}, inplace=True)
    elif 'world_index' in df_timestamps.columns:
        df_timestamps.rename(columns={'world_index': 'frame'}, inplace=True)
    else:
        print("ATTENZIONE: Nessuna colonna indice frame standard trovata. Uso l'indice del file come fallback.")
        df_timestamps.reset_index(inplace=True)
        df_timestamps.rename(columns={'index': 'frame'}, inplace=True)

    if 'timestamp [s]' in df_timestamps.columns:
        df_timestamps.rename(columns={'timestamp [s]': 'timestamp'}, inplace=True)
    elif 'timestamp [ns]' in df_timestamps.columns:
        df_timestamps['timestamp'] = df_timestamps['timestamp [ns]'] / 1e9
    else:
        print("ERRORE CRITICO: Colonna timestamp non trovata in 'world_timestamps.csv'. Impossibile procedere.")
        df_main[PUPIL_COL_NAME] = np.nan
        return df_main

    df_main = pd.merge(df_main, df_timestamps[['frame', 'timestamp']], on='frame', how='left')
    df_pupil = pd.read_csv(pupil_path_to_use)
    
    pupil_col_found = False
    if 'pupil diameter left [mm]' in df_pupil.columns and 'pupil diameter right [mm]' in df_pupil.columns:
         print("INFO: Trovati dati per pupilla destra e sinistra. Calcolo la media.")
         df_pupil[PUPIL_COL_NAME] = df_pupil[['pupil diameter left [mm]', 'pupil diameter right [mm]']].mean(axis=1)
         pupil_col_found = True
    elif 'diameter_3d' in df_pupil.columns:
        print("INFO: Trovata colonna 'diameter_3d'. La uso per l'analisi.")
        df_pupil[PUPIL_COL_NAME] = df_pupil['diameter_3d']
        pupil_col_found = True
    elif 'diameter' in df_pupil.columns:
        print("INFO: Trovata colonna 'diameter'. La uso per l'analisi.")
        df_pupil[PUPIL_COL_NAME] = df_pupil['diameter']
        pupil_col_found = True

    if not pupil_col_found:
        print(f"ATTENZIONE: Nessuna colonna valida per il diametro pupillare trovata. Salto analisi.")
        df_main[PUPIL_COL_NAME] = np.nan
        return df_main

    if 'timestamp [s]' in df_pupil.columns:
        df_pupil.rename(columns={'timestamp [s]': 'timestamp'}, inplace=True)
    elif 'timestamp [ns]' in df_pupil.columns:
        df_pupil['timestamp'] = df_pupil['timestamp [ns]'] / 1e9

    df_main = pd.merge_asof(df_main.sort_values('timestamp'), 
                            df_pupil[['timestamp', PUPIL_COL_NAME]].dropna().sort_values('timestamp'), 
                            on='timestamp', 
                            direction='nearest')
    print("INFO: Dati di pupillometria aggiunti e sincronizzati con successo.")
    return df_main

def generate_gaze_heatmap(df_gaze, width, height, output_path):
    if df_gaze.empty or 'gaze_x_norm' not in df_gaze.columns or df_gaze['gaze_x_norm'].isnull().all(): return
    plt.figure(figsize=(width/100, height/100)); plt.style.use('dark_background')
    sns.kdeplot(x=df_gaze['gaze_x_norm']*width, y=df_gaze['gaze_y_norm']*height, fill=True, cmap="inferno", thresh=0.05, alpha=0.7)
    plt.xlim(0, width); plt.ylim(height, 0); plt.axis('off'); plt.title(os.path.basename(output_path).replace('.png', ''), color='white')
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, transparent=True); plt.close()

def generate_pupillometry_plot(df_trials, pupil_col, output_path):
    if pupil_col not in df_trials.columns or df_trials[pupil_col].isnull().all(): return
    aligned_trials, normalized_time = [], np.linspace(0, 100, 100)
    for _, group in df_trials[df_trials['trial_id'] > 0].groupby('trial_id'):
        group = group.dropna(subset=[pupil_col])
        if len(group) < 2: continue
        interp_func = interp1d(np.linspace(0, 100, len(group)), group[pupil_col], kind='linear', fill_value="extrapolate")
        aligned_trials.append(interp_func(normalized_time))
    if not aligned_trials: return
    mean_pupil, std_pupil = np.mean(aligned_trials, axis=0), np.std(aligned_trials, axis=0)
    plt.style.use('seaborn-v0_8-whitegrid'); plt.figure(figsize=(10, 6))
    plt.plot(normalized_time, mean_pupil, label='Diametro Pupillare Medio', color='royalblue')
    plt.fill_between(normalized_time, mean_pupil-std_pupil, mean_pupil+std_pupil, color='cornflowerblue', alpha=0.3, label='Deviazione Standard')
    plt.title(f"Andamento Pupillometrico Medio - {os.path.basename(output_path).replace('.png', '')}"); plt.xlabel("Percentuale Completamento Movimento (%)"); plt.ylabel("Diametro Pupillare Medio [mm]")
    plt.legend(); plt.grid(True); plt.savefig(output_path); plt.close()

def validate_movement_sequence(df_segment, expected_sequence, segment_name):
    print(f"\n--- Validazione Sequenza Movimenti per '{segment_name}' ---")
    df_trials = df_segment[df_segment['trial_id'] > 0].copy()
    if df_trials.empty:
        print("ATTENZIONE: Nessun trial valido trovato per la validazione.")
        return
    actual_sequence = df_trials.drop_duplicates(subset=['trial_id']).sort_values('trial_id')['direction_simple'].tolist()
    print(f"Sequenza Attesa  ({len(expected_sequence)}): {expected_sequence}")
    print(f"Sequenza Rilevata ({len(actual_sequence)}): {actual_sequence}")
    if actual_sequence == expected_sequence: print("RISULTATO: ✔️ Corrispondenza Perfetta!")
    else: print("RISULTATO: ❌ ATTENZIONE: La sequenza non corrisponde a quella attesa.")

def main(args):
    analysis_path = os.path.join(args.analysis_dir, 'output_final_analysis_analysis.csv')
    cuts_path = os.path.join(args.analysis_dir, 'cut_points.csv')
    
    for f in [analysis_path, cuts_path]:
        if not os.path.exists(f): raise FileNotFoundError(f"File di analisi richiesto non trovato: {f}")

    df_main = pd.read_csv(analysis_path)
    df_main = calculate_movement_data(df_main)
    df_main = add_pupil_data(df_main, args.input_dir_for_pupil) 
    
    df_cuts = pd.read_csv(cuts_path)
    plot_dir = os.path.join(args.output_dir, "plots_and_heatmaps")
    os.makedirs(plot_dir, exist_ok=True)
    
    output_excel_path = os.path.join(args.output_dir, 'final_report.xlsx')
    writer = pd.ExcelWriter(output_excel_path, engine='xlsxwriter')
    
    expected_sequence_fast = ['right', 'left', 'right', 'up', 'down', 'up', 'right', 'left', 'right', 'up', 'down', 'up', 'right', 'left', 'right', 'up', 'down', 'up']
    expected_sequence_slow = ['right', 'left', 'right', 'up', 'down', 'up', 'down', 'up', 'right', 'left', 'right', 'up', 'down', 'up', 'down', 'right', 'left', 'right', 'up', 'down']
    expected_sequences = {'fast': expected_sequence_fast, 'slow': expected_sequence_slow}
    
    general_summary_list = []

    for _, cut_row in df_cuts.iterrows():
        segment_name, start_frame, end_frame = cut_row['segment_name'], cut_row['start_frame'], cut_row['end_frame']
        print(f"\nElaborazione del report per il segmento: '{segment_name}'...")
        df_segment = df_main[(df_main['frame'] >= start_frame) & (df_main['frame'] <= end_frame)].copy()
        if df_segment.empty: continue

        video_path = os.path.join(args.output_dir, f'final_video_{segment_name}.mp4')
        vid_width, vid_height = get_video_dimensions(video_path)

        df_center_out = df_segment[df_segment['direction'].str.startswith('center_to_', na=False)].copy()
        if df_center_out.empty: continue
        
        df_center_out['direction_simple'] = df_center_out['direction'].str.split('_').str[-1]
        
        if segment_name == 'slow':
            last_trial_id = df_center_out['trial_id'].max()
            if not pd.isna(last_trial_id):
                last_trial_direction = df_center_out[df_center_out['trial_id'] == last_trial_id]['direction_simple'].iloc[0]
                if last_trial_direction == 'up':
                    print(f"INFO: L'ultimo trial 'up' (ID: {last_trial_id}) del segmento 'slow' sarà ESCLUSO dall'analisi statistica.")
                    df_center_out = df_center_out[df_center_out['trial_id'] != last_trial_id].copy()

        validate_movement_sequence(df_center_out, expected_sequences.get(segment_name, []), segment_name)
        
        agg_dict = {'avg_gaze_in_box_perc': ('gaze_in_box', 'mean'), 'avg_gaze_speed': ('gaze_speed', 'mean'), 'trial_count': ('trial_id', 'nunique')}
        if PUPIL_COL_NAME in df_center_out.columns:
            agg_dict['avg_pupil_diameter'] = (PUPIL_COL_NAME, 'mean')
            
        summary_by_direction = df_center_out.groupby('direction_simple').agg(**agg_dict).reset_index()
        summary_by_direction['avg_gaze_in_box_perc'] *= 100
        
        if not summary_by_direction.empty:
            summary_by_direction.to_excel(writer, sheet_name=f"Riepilogo_{segment_name}", index=False)
            df_center_out.to_excel(writer, sheet_name=f"Dettagli_{segment_name}", index=False)
            print(f"Statistiche per '{segment_name}' salvate nei fogli 'Riepilogo_{segment_name}' e 'Dettagli_{segment_name}'.")

            segment_summary = {'segmento': segment_name, 'gaze_in_box_perc_totale': df_center_out['gaze_in_box'].mean() * 100, 'velocita_sguardo_media': df_center_out['gaze_speed'].mean(), 'numero_trial_validi': df_center_out['trial_id'].nunique()}
            if PUPIL_COL_NAME in df_center_out.columns:
                segment_summary['diametro_pupillare_medio'] = df_center_out[PUPIL_COL_NAME].mean()
            general_summary_list.append(segment_summary)

        for direction in summary_by_direction['direction_simple'].unique():
            df_direction = df_center_out[df_center_out['direction_simple'] == direction]
            generate_gaze_heatmap(df_direction, vid_width, vid_height, os.path.join(plot_dir, f"heatmap_{segment_name}_{direction}.png"))
            generate_pupillometry_plot(df_direction, PUPIL_COL_NAME, os.path.join(plot_dir, f"pupillometry_{segment_name}_{direction}.png"))
    
    if general_summary_list:
        df_general_summary = pd.DataFrame(general_summary_list)
        df_general_summary.to_excel(writer, sheet_name="Riepilogo_Generale", index=False)
        print("\nStatistiche aggregate per segmento salvate nel foglio 'Riepilogo_Generale'.")
    
    writer.close()
    print(f"\n--- Report Excel Finale Salvato in: {output_excel_path} ---")