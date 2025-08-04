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
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h

def load_manual_events(df_main, manual_events_path):
    """Carica e applica gli eventi (trial) da un file CSV fornito dall'utente."""
    print(f"INFO: Caricamento eventi manuali da '{os.path.basename(manual_events_path)}'...")
    try:
        df_events = pd.read_csv(manual_events_path)
        required_cols = ['segment_name', 'direction_simple', 'start_frame', 'end_frame']
        if not all(col in df_events.columns for col in required_cols):
            raise ValueError(f"Il file CSV deve contenere le colonne: {required_cols}")
    except Exception as e:
        raise Exception(f"Errore nella lettura del file CSV degli eventi: {e}")

    df_main['direction'] = ''
    df_main['trial_id'] = 0
    df_main['direction_simple'] = ''
    trial_counter = 0

    for _, event in df_events.iterrows():
        trial_counter += 1
        mask = (df_main['frame'] >= event['start_frame']) & (df_main['frame'] <= event['end_frame'])
        df_main.loc[mask, 'trial_id'] = trial_counter
        df_main.loc[mask, 'direction_simple'] = event['direction_simple']
        df_main.loc[mask, 'direction'] = f"center_to_{event['direction_simple']}"

    df_main['ball_speed'] = np.sqrt(df_main['ball_center_x_norm'].diff()**2 + df_main['ball_center_y_norm'].diff()**2)
    df_main['gaze_speed'] = np.sqrt(df_main['gaze_x_norm'].diff()**2 + df_main['gaze_y_norm'].diff()**2)
    df_main.loc[df_main['trial_id'] != df_main['trial_id'].shift(1), ['ball_speed', 'gaze_speed']] = np.nan
    
    print(f"INFO: Caricati e applicati {len(df_events)} eventi manuali.")
    return df_main

def calculate_movement_data(df):
    """Calcola automaticamente i trial basandosi sul movimento della palla."""
    print("INFO: Calcolo automatico di 'direction' e 'trial_id'...")
    def get_zone(x, y):
        if 0.40 < x < 0.60 and 0.40 < y < 0.60: return 'center'
        if y <= 0.40: return 'up'
        if y >= 0.60: return 'down'
        if x <= 0.40: return 'left'
        if x >= 0.60: return 'right'
        return 'other'
    df['zone'] = df.apply(lambda row: get_zone(row['ball_center_x_norm'], row['ball_center_y_norm']), axis=1)
    df['direction'], df['trial_id'], df['direction_simple'] = '', 0, ''
    trial_counter, in_trial = 0, False
    for i in range(1, len(df)):
        if not in_trial and df.loc[i-1, 'zone'] == 'center' and df.loc[i, 'zone'] not in ['center', 'other']:
            in_trial, trial_counter = True, trial_counter + 1
        if in_trial:
            direction = df.loc[i, 'zone']
            df.loc[i, 'trial_id'] = trial_counter
            df.loc[i, 'direction'] = f"center_to_{direction}"
            df.loc[i, 'direction_simple'] = direction
        if in_trial and df.loc[i, 'zone'] == 'center':
            in_trial = False
    
    df['ball_speed'] = np.sqrt(df['ball_center_x_norm'].diff()**2 + df['ball_center_y_norm'].diff()**2)
    df['gaze_speed'] = np.sqrt(df['gaze_x_norm'].diff()**2 + df['gaze_y_norm'].diff()**2)
    df.loc[df['trial_id'] != df['trial_id'].shift(1), ['ball_speed', 'gaze_speed']] = np.nan
    df.drop(columns=['zone'], inplace=True)
    print(f"INFO: Calcolo completato. Trovati {trial_counter} trial.")
    return df

def add_pupil_data(df_main, base_dir):
    # ... (questa funzione rimane uguale)
    return df_main

def generate_gaze_heatmap(df_gaze, width, height, output_path):
    # ... (questa funzione rimane uguale)
    pass

def generate_pupillometry_plot(df_trials, pupil_col, output_path):
    # ... (questa funzione rimane uguale)
    pass
    
def validate_movement_sequence(df, seq, name):
    # ... (questa funzione rimane uguale)
    pass

def generate_fragmentation_plots(df_analysis, df_cuts, output_dir):
    # ... (questa funzione rimane uguale)
    pass

def calculate_excursion(df_input):
    # ... (questa funzione rimane uguale)
    return df_input

def main(args):
    analysis_path = os.path.join(args.analysis_dir, 'output_final_analysis_analysis.csv')
    cuts_path = os.path.join(args.analysis_dir, 'cut_points.csv')
    df_main = pd.read_csv(analysis_path)
    df_cuts = pd.read_csv(cuts_path)

    # Controlla se usare il calcolo automatico o gli eventi manuali
    if args.manual_events_path and os.path.exists(args.manual_events_path):
        df_main = load_manual_events(df_main, args.manual_events_path)
    else:
        if 'manual_events_path' in args and args.manual_events_path:
             print(f"ATTENZIONE: File eventi manuali non trovato in '{args.manual_events_path}'. Eseguo calcolo automatico.")
        df_main = calculate_movement_data(df_main)
    
    df_main = add_pupil_data(df_main, args.input_dir_for_pupil)

    plot_dir = os.path.join(args.output_dir, "plots_and_heatmaps")
    os.makedirs(plot_dir, exist_ok=True)
    writer = pd.ExcelWriter(os.path.join(args.output_dir, 'final_report.xlsx'), engine='xlsxwriter')

    expected_sequences = {'fast': ['right','left','right','up','down','up']*3, 'slow': ['right','left','right','up','down','up','down','up','right','left','right','up','down','up','down','right','left','right','up','down']}
    general_summary_list = []

    for _, cut_row in df_cuts.iterrows():
        segment_name = cut_row['segment_name']
        df_segment = df_main[(df_main['frame'] >= cut_row['start_frame']) & (df_main['frame'] <= cut_row['end_frame'])].copy()
        
        if df_segment.empty: continue
        w, h = get_video_dimensions(os.path.join(args.output_dir, f'final_video_{segment_name}.mp4'))
        df_center_out = df_segment[df_segment['trial_id'] > 0].copy()
        if df_center_out.empty: continue

        # In modalità eventi manuali, la validazione della sequenza potrebbe non essere pertinente
        if not (args.manual_events_path and os.path.exists(args.manual_events_path)):
            validate_movement_sequence(df_center_out, expected_sequences.get(segment_name, []), segment_name)

        if args.run_excursion_analysis: df_center_out = calculate_excursion(df_center_out)

        agg_dict = {'avg_gaze_in_box_perc': ('gaze_in_box', 'mean'), 'avg_gaze_speed': ('gaze_speed', 'mean'), 'trial_count': ('trial_id', 'nunique')}
        if PUPIL_COL_NAME in df_center_out: agg_dict['avg_pupil_diameter'] = (PUPIL_COL_NAME, 'mean')
        if args.run_excursion_analysis and 'excursion_success' in df_center_out.columns:
            agg_dict['excursion_success_perc'] = ('excursion_success', 'mean')
            agg_dict['avg_excursion_perc_frames'] = ('excursion_perc_frames', 'mean')

        summary = df_center_out.groupby('direction_simple').agg(**agg_dict).reset_index()
        summary['avg_gaze_in_box_perc'] *= 100
        if 'excursion_success_perc' in summary: summary['excursion_success_perc'] *= 100

        summary.to_excel(writer, sheet_name=f"Riepilogo_{segment_name}", index=False)
        df_center_out.to_excel(writer, sheet_name=f"Dettagli_{segment_name}", index=False)

        gen_sum = {'segmento': segment_name, 'gaze_in_box_perc_totale': df_center_out['gaze_in_box'].mean()*100, 'velocita_sguardo_media': df_center_out['gaze_speed'].mean(), 'numero_trial_validi': df_center_out['trial_id'].nunique()}
        if PUPIL_COL_NAME in df_center_out: gen_sum['diametro_pupillare_medio'] = df_center_out[PUPIL_COL_NAME].mean()
        if args.run_excursion_analysis and 'excursion_success' in df_center_out.columns:
            gen_sum['escursione_successo_perc'] = df_center_out['excursion_success'].mean() * 100
            gen_sum['escursione_perc_frames_media'] = df_center_out['excursion_perc_frames'].mean()
        general_summary_list.append(gen_sum)

        for direction in summary['direction_simple'].unique():
            df_dir = df_center_out[df_center_out['direction_simple'] == direction]
            generate_gaze_heatmap(df_dir, w, h, os.path.join(plot_dir, f"heatmap_{segment_name}_{direction}.png"))
            generate_pupillometry_plot(df_dir, PUPIL_COL_NAME, os.path.join(plot_dir, f"pupillometry_{segment_name}_{direction}.png"))

    if general_summary_list: pd.DataFrame(general_summary_list).to_excel(writer, sheet_name="Riepilogo_Generale", index=False)
    writer.close()

    if args.run_fragmentation_analysis: generate_fragmentation_plots(df_main, df_cuts, plot_dir)