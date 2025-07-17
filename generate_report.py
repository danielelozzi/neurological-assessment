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
    cap = cv2.VideoCapture(video_path);
    if not cap.isOpened(): return 1920, 1080
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); cap.release(); return w, h

def calculate_movement_data(df):
    print("INFO: Calcolo 'direction', 'trial_id' e velocità...")
    def get_zone(x, y):
        if 0.40 < x < 0.60 and 0.40 < y < 0.60: return 'center'
        if y <= 0.40: return 'up'
        if y >= 0.60: return 'down'
        if x <= 0.40: return 'left'
        if x >= 0.60: return 'right'
        return 'other'
    df['zone'] = df.apply(lambda row: get_zone(row['ball_center_x_norm'], row['ball_center_y_norm']), axis=1)
    df['direction'], df['trial_id'] = '', 0
    trial_counter, in_trial = 0, False
    for i in range(1, len(df)):
        if not in_trial and df.loc[i-1, 'zone'] == 'center' and df.loc[i, 'zone'] not in ['center', 'other']:
            in_trial, trial_counter = True, trial_counter + 1
        if in_trial: df.loc[i, 'trial_id'], df.loc[i, 'direction'] = trial_counter, f"center_to_{df.loc[i, 'zone']}"
        if in_trial and df.loc[i, 'zone'] == 'center': in_trial = False
    df['ball_speed'] = np.sqrt(df['ball_center_x_norm'].diff()**2 + df['ball_center_y_norm'].diff()**2)
    df['gaze_speed'] = np.sqrt(df['gaze_x_norm'].diff()**2 + df['gaze_y_norm'].diff()**2)
    df.loc[df['trial_id'] != df['trial_id'].shift(1), ['ball_speed', 'gaze_speed']] = 0
    df.drop(columns=['zone'], inplace=True); print(f"INFO: Calcolo completato. Trovati {trial_counter} trial."); return df

def add_pupil_data(df_main, base_dir):
    # (Questa funzione rimane invariata rispetto all'ultima versione)
    print("\n--- Analisi Dati Pupillometrici ---")
    timestamps_path = os.path.join(base_dir, 'world_timestamps.csv') 
    pupil_path_main = os.path.join(base_dir, 'pupil_positions.csv')
    pupil_path_fallback = os.path.join(base_dir, '3d_eye_states.csv')
    pupil_path_to_use = next((p for p in [pupil_path_main, pupil_path_fallback] if os.path.exists(p)), None)
    if not pupil_path_to_use: print("ATTENZIONE: File pupillometria non trovato."); df_main[PUPIL_COL_NAME] = np.nan; return df_main
    print(f"INFO: Trovato file pupillometria: '{os.path.basename(pupil_path_to_use)}'")
    df_timestamps = pd.read_csv(timestamps_path)
    if '# frame_idx' in df_timestamps.columns: df_timestamps.rename(columns={'# frame_idx': 'frame'}, inplace=True)
    elif 'frame_idx' in df_timestamps.columns: df_timestamps.rename(columns={'frame_idx': 'frame'}, inplace=True)
    elif 'world_index' in df_timestamps.columns: df_timestamps.rename(columns={'world_index': 'frame'}, inplace=True)
    else: print("ATTENZIONE: Indice frame non trovato, uso fallback."); df_timestamps.reset_index(inplace=True); df_timestamps.rename(columns={'index': 'frame'}, inplace=True)
    if 'timestamp [s]' in df_timestamps.columns: df_timestamps.rename(columns={'timestamp [s]': 'timestamp'}, inplace=True)
    elif 'timestamp [ns]' in df_timestamps.columns: df_timestamps['timestamp'] = df_timestamps['timestamp [ns]'] / 1e9
    df_main = pd.merge(df_main, df_timestamps[['frame', 'timestamp']], on='frame', how='left')
    df_pupil = pd.read_csv(pupil_path_to_use)
    if 'pupil diameter left [mm]' in df_pupil.columns and 'pupil diameter right [mm]' in df_pupil.columns:
         df_pupil[PUPIL_COL_NAME] = df_pupil[['pupil diameter left [mm]', 'pupil diameter right [mm]']].mean(axis=1)
    elif 'diameter_3d' in df_pupil.columns: df_pupil[PUPIL_COL_NAME] = df_pupil['diameter_3d']
    elif 'diameter' in df_pupil.columns: df_pupil[PUPIL_COL_NAME] = df_pupil['diameter']
    else: print("ATTENZIONE: Colonna diametro pupillare non trovata."); df_main[PUPIL_COL_NAME] = np.nan; return df_main
    if 'timestamp [s]' in df_pupil.columns: df_pupil.rename(columns={'timestamp [s]': 'timestamp'}, inplace=True)
    elif 'timestamp [ns]' in df_pupil.columns: df_pupil['timestamp'] = df_pupil['timestamp [ns]'] / 1e9
    df_main = pd.merge_asof(df_main.sort_values('timestamp'), df_pupil[['timestamp', PUPIL_COL_NAME]].dropna().sort_values('timestamp'), on='timestamp', direction='nearest')
    print("INFO: Dati pupillometria aggiunti."); return df_main

def generate_gaze_heatmap(df_gaze, width, height, output_path):
    if df_gaze.empty or df_gaze['gaze_x_norm'].isnull().all(): return
    plt.figure(figsize=(width/100, height/100)); plt.style.use('dark_background')
    sns.kdeplot(x=df_gaze['gaze_x_norm']*width, y=df_gaze['gaze_y_norm']*height, fill=True, cmap="inferno", thresh=0.05, alpha=0.7)
    plt.xlim(0, width); plt.ylim(height, 0); plt.axis('off')
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, transparent=True); plt.close()

def generate_pupillometry_plot(df_trials, pupil_col, output_path):
    # (Questa funzione rimane invariata)
    if pupil_col not in df_trials.columns or df_trials[pupil_col].isnull().all(): return
    aligned_trials, normalized_time = [], np.linspace(0, 100, 100)
    for _, group in df_trials[df_trials['trial_id'] > 0].groupby('trial_id'):
        group = group.dropna(subset=[pupil_col]);
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

def validate_movement_sequence(df, seq, name):
    print(f"\n--- Validazione Sequenza per '{name}' ---")
    actual_seq = df[df['trial_id'] > 0].drop_duplicates('trial_id')['direction_simple'].tolist()
    print(f"Attesa ({len(seq)}): {seq}")
    print(f"Rilevata ({len(actual_seq)}): {actual_seq}")
    print("RISULTATO: ✔️ Corrispondenza Perfetta!" if actual_seq == seq else "RISULTATO: ❌ ATTENZIONE: Non corrisponde.")

# --- FUNZIONE RINOMINATA E AGGIORNATA ---
def generate_fragmentation_plots(df_analysis, df_cuts, output_dir):
    print("\n--- Generazione Grafici 'Frammentazione' ---")
    for _, cut_row in df_cuts.iterrows():
        segment_name = cut_row['segment_name']
        df_segment = df_analysis[(df_analysis['frame'] >= cut_row['start_frame']) & (df_analysis['frame'] <= cut_row['end_frame'])].copy()
        if df_segment.empty: continue
        start_markers = df_segment.drop_duplicates('trial_id'); start_markers = start_markers[start_markers['trial_id'] > 0]
        plt.style.use('seaborn-v0_8-whitegrid'); fig, ax = plt.subplots(figsize=(20, 8))
        ax.plot(df_segment['frame'], df_segment['gaze_speed'], label=f'Frammentazione Sguardo ({segment_name})', color='dodgerblue', alpha=0.7, lw=1.5)
        for _, marker in start_markers.iterrows():
            direction = marker['direction'].split('_')[-1]
            ax.axvline(x=marker['frame'], color='red', linestyle='--', lw=1.2, alpha=0.9)
            ax.text(marker['frame'] + 5, ax.get_ylim()[1] * 0.95, direction, rotation=90, color='red', va='top', fontdict={'size': 9, 'weight': 'bold'})
        ax.set_xlabel("Frame Video"); ax.set_ylabel("Distanza Euclidea Sguardo (Frammentazione)")
        ax.set_title(f"Analisi Frammentazione per Segmento '{segment_name}'"); ax.legend(loc='upper right')
        ax.grid(True, which='both', linestyle='--', lw=0.5); ax.set_xlim(df_segment['frame'].min(), df_segment['frame'].max())
        output_path = os.path.join(output_dir, f"fragmentation_plot_{segment_name}.png")
        plt.savefig(output_path, dpi=150); plt.close(fig)
        print(f"INFO: Grafico 'Frammentazione' salvato in: {output_path}")

# --- NUOVA FUNZIONE: CALCOLO ESCURSIONE ---
def calculate_excursion(df_input):
    print("INFO: Calcolo metrica 'Escursione'...")
    df = df_input.copy()
    if df.empty or 'trial_id' not in df.columns: return df
    
    results = {}
    # Itera su ogni trial (gruppo di righe con lo stesso trial_id > 0)
    for trial_id, group in df[df['trial_id'] > 0].groupby('trial_id'):
        direction = group['direction_simple'].iloc[0]
        gaze_reached_target = False
        if direction == 'right' and not group['gaze_x_norm'].isnull().all(): gaze_reached_target = group['gaze_x_norm'].max() >= 0.60
        elif direction == 'left' and not group['gaze_x_norm'].isnull().all(): gaze_reached_target = group['gaze_x_norm'].min() <= 0.40
        elif direction == 'down' and not group['gaze_y_norm'].isnull().all(): gaze_reached_target = group['gaze_y_norm'].max() >= 0.60
        elif direction == 'up' and not group['gaze_y_norm'].isnull().all(): gaze_reached_target = group['gaze_y_norm'].min() <= 0.40
        results[trial_id] = gaze_reached_target
    
    # Mappa i risultati booleani al DataFrame originale
    df['excursion_success'] = df['trial_id'].map(results)
    return df

def main(args):
    analysis_path = os.path.join(args.analysis_dir, 'output_final_analysis_analysis.csv')
    cuts_path = os.path.join(args.analysis_dir, 'cut_points.csv')
    df_main = pd.read_csv(analysis_path); df_cuts = pd.read_csv(cuts_path)
    df_main = calculate_movement_data(df_main)
    df_main = add_pupil_data(df_main, args.input_dir_for_pupil) 
    
    plot_dir = os.path.join(args.output_dir, "plots_and_heatmaps"); os.makedirs(plot_dir, exist_ok=True)
    writer = pd.ExcelWriter(os.path.join(args.output_dir, 'final_report.xlsx'), engine='xlsxwriter')
    
    expected_sequences = {'fast': ['right','left','right','up','down','up']*3, 'slow': ['right','left','right','up','down','up','down','up','right','left','right','up','down','up','down','right','left','right','up','down']}
    general_summary_list = []

    for _, cut_row in df_cuts.iterrows():
        segment_name, start_f, end_f = cut_row['segment_name'], cut_row['start_frame'], cut_row['end_frame']
        df_segment = df_main[(df_main['frame'] >= start_f) & (df_main['frame'] <= end_f)].copy()
        if df_segment.empty: continue
        w, h = get_video_dimensions(os.path.join(args.output_dir, f'final_video_{segment_name}.mp4'))
        df_center_out = df_segment[df_segment['direction'].str.startswith('center_to_', na=False)].copy()
        if df_center_out.empty: continue
        df_center_out['direction_simple'] = df_center_out['direction'].str.split('_').str[-1]
        
        if segment_name == 'slow' and df_center_out['trial_id'].max() is not np.nan:
            last_trial_id = df_center_out['trial_id'].max()
            if df_center_out[df_center_out['trial_id'] == last_trial_id]['direction_simple'].iloc[0] == 'up':
                df_center_out = df_center_out[df_center_out['trial_id'] != last_trial_id]

        validate_movement_sequence(df_center_out, expected_sequences.get(segment_name, []), segment_name)
        
        # --- INTEGRAZIONE ESCURSIONE ---
        if args.run_excursion_analysis: df_center_out = calculate_excursion(df_center_out)
        
        agg_dict = {'avg_gaze_in_box_perc': ('gaze_in_box', 'mean'), 'avg_gaze_speed': ('gaze_speed', 'mean'), 'trial_count': ('trial_id', 'nunique')}
        if PUPIL_COL_NAME in df_center_out: agg_dict['avg_pupil_diameter'] = (PUPIL_COL_NAME, 'mean')
        if args.run_excursion_analysis: agg_dict['excursion_success_perc'] = ('excursion_success', 'mean')
            
        summary = df_center_out.groupby('direction_simple').agg(**agg_dict).reset_index()
        summary['avg_gaze_in_box_perc'] *= 100
        if 'excursion_success_perc' in summary: summary['excursion_success_perc'] *= 100

        summary.to_excel(writer, sheet_name=f"Riepilogo_{segment_name}", index=False)
        df_center_out.to_excel(writer, sheet_name=f"Dettagli_{segment_name}", index=False)
        
        # Riepilogo generale
        gen_sum = {'segmento': segment_name, 'gaze_in_box_perc_totale': df_center_out['gaze_in_box'].mean()*100, 'velocita_sguardo_media': df_center_out['gaze_speed'].mean(), 'numero_trial_validi': df_center_out['trial_id'].nunique()}
        if PUPIL_COL_NAME in df_center_out: gen_sum['diametro_pupillare_medio'] = df_center_out[PUPIL_COL_NAME].mean()
        if args.run_excursion_analysis: gen_sum['escursione_successo_perc'] = df_center_out['excursion_success'].mean() * 100
        general_summary_list.append(gen_sum)

        for direction in summary['direction_simple'].unique():
            df_dir = df_center_out[df_center_out['direction_simple'] == direction]
            generate_gaze_heatmap(df_dir, w, h, os.path.join(plot_dir, f"heatmap_{segment_name}_{direction}.png"))
            generate_pupillometry_plot(df_dir, PUPIL_COL_NAME, os.path.join(plot_dir, f"pupillometry_{segment_name}_{direction}.png"))

    if general_summary_list: pd.DataFrame(general_summary_list).to_excel(writer, sheet_name="Riepilogo_Generale", index=False)
    writer.close()
    
    if args.run_fragmentation_analysis: generate_fragmentation_plots(df_main, df_cuts, plot_dir)