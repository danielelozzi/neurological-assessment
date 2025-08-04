# Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)

**LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)**  
**Sito Web Lab:** [labscoc.wordpress.com](https://labscoc.wordpress.com)

**Repository GitHub:** [github.com/danielelozzi/neurological-assessment](https://github.com/danielelozzi/neurological-assessment)  
**Concettualizzazione:** Dr. Massimo Marano

---

Questo repository contiene una pipeline software completa per l'analisi del movimento oculare e della pupillometria in relazione al movimento di un cerchio su uno schermo. L'intero processo è gestito da un'unica interfaccia grafica (GUI) che orchestra l'elaborazione dei dati.

## 🎯 Obiettivo del Software
L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. Il software offre diverse modalità di lavoro per massima flessibilità.

## 🚀 Modalità di Lavoro

### 1. Modalità Automatica (Default)
Questa è la modalità standard. Il software esegue l'intera pipeline senza intervento manuale:

- **Identifica i Segmenti di Test**: Utilizzando OCR, individua automaticamente i segmenti "fast" e "slow".
- **Corregge la Prospettiva**: Isola l'area dello schermo tramite AprilTag.
- **Rileva e Sincronizza**: Rileva il cerchio (con YOLO o Hough), tracciandone il movimento e sincronizzando i dati di sguardo e pupilla.
- **Identifica gli Eventi**: Riconosce automaticamente l'inizio e la fine di ogni movimento della palla (destra, sinistra, ecc.).
- **Genera l'Output**: Produce video con overlay, un report Excel dettagliato e grafici.

### 2. Modalità Manuale e Ibrida
Per un controllo totale, è possibile attivare le opzioni di inserimento manuale direttamente dalla GUI, anche in modo combinato.

#### A. Definizione Manuale dei Segmenti
Attivando la checkbox **"Definisci Segmenti Manualmente"**, appariranno quattro campi per inserire i frame esatti di INIZIO e FINE dei segmenti fast e slow. In questa modalità, la ricerca automatica del punto di inizio (`trim_video.py`) viene saltata.

#### B. Definizione Manuale degli Eventi di Movimento
Attivando la checkbox **"Definisci Eventi Manualmente (CSV)"**, il programma salterà l'identificazione automatica dei movimenti della palla. Sarà necessario fornire un file `.csv` che specifichi l'inizio e la fine di ogni *trial* (movimento).

##### Formato del file CSV per eventi manuali:
Il file deve contenere le seguenti colonne: `segment_name`, `direction_simple`, `start_frame`, `end_frame`.

- **segment_name**: `fast` o `slow`
- **direction_simple**: `right`, `left`, `up`, o `down`
- **start_frame**: Il numero del frame in cui inizia il movimento
- **end_frame**: Il numero del frame in cui termina il movimento

**Esempio (`miei_eventi.csv`)**:
```
segment_name,direction_simple,start_frame,end_frame
fast,right,5010,5090
fast,left,5150,5230
slow,right,10200,10350
```

> **NOTA:** Quando si usa l'opzione "Definisci Eventi Manualmente", l'etichetta di testo con la direzione del movimento non verrà disegnata sui video finali, poiché tale funzione è legata al processo automatico. Il report Excel sarà invece generato correttamente in base ai dati manuali forniti.

---

## 📋 Prerequisiti
È necessario acquisire i dati con **Pupil Labs Neon**, usare gli **AprilTag** e processare la registrazione su **Pupil Cloud** con l'enrichment *Marker Mapper*. La cartella scaricata da Pupil Cloud deve contenere i file:

- `video.mp4`
- `gaze.csv`
- `world_timestamps.csv`
- `surface_positions.csv`

## 🛠️ Installazione

Crea un ambiente conda:
```bash
conda create --name cna-env python=3.10 -y
conda activate cna-env
```

Installa le librerie:
```bash
pip install -r requirements.txt
```

## 📊 Output del Progetto

- `final_report.xlsx`: Report Excel con metriche dettagliate e di riepilogo
- `final_video_fast.mp4` / `final_video_slow.mp4`: Video finali (con overlay solo in modalità automatica)
- `output_final_analysis_analysis.csv`: Dati grezzi calcolati, frame per frame
- `cut_points.csv`: Frame di inizio/fine dei segmenti (calcolati automaticamente o inseriti manualmente)
- Cartella `plots_and_heatmaps/`: Visualizzazioni grafiche (heatmap, grafici pupillometrici, ecc.)