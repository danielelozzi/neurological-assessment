# Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)

**LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)**  
**Sito Web Lab:** [labscoc.wordpress.com](https://labscoc.wordpress.com)  
**PIs:** Prof. Giuseppe Curcio, Prof. Simone Migliore
**Concettualizzazione:** Dr. Massimo Marano  
**Codice:** Dr. Daniele Lozzi  

Questo repository contiene una pipeline software completa per l'analisi del movimento oculare e della pupillometria in relazione al movimento di un cerchio su uno schermo. L'intero processo è gestito da un'unica interfaccia grafica (GUI) che orchestra l'elaborazione dei dati.

## 🎯 Obiettivo del Software
L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. Il software offre diverse modalità di lavoro per massima flessibilità, da quella completamente automatica a quella interamente manuale e interattiva.

## 🚀 Modalità di Lavoro

### 1. Modalità Automatica (Default)
Questa è la modalità standard. Il software esegue l'intera pipeline con il minimo intervento manuale:

- **Identifica i Segmenti di Test**: Utilizzando OCR, individua automaticamente l'inizio dei segmenti "fast" e "slow".
- **Corregge la Prospettiva**: Isola l'area dello schermo tramite AprilTag.
- **Rileva e Sincronizza**: Rileva il cerchio (con YOLO o Hough), tracciandone il movimento e sincronizzando i dati di sguardo e pupilla.
- **Identifica gli Eventi**: Riconosce automaticamente l'inizio e la fine di ogni movimento della palla (destra, sinistra, ecc.).
- **Genera l'Output**: Produce video con overlay, un report Excel dettagliato e grafici.

> **NOTA SUL FALLBACK**: Se la ricerca automatica dei segmenti (fase 1) non riesce, il programma aprirà automaticamente una **finestra video interattiva** per permetterti di definire manualmente l'inizio dei segmenti "fast" e "slow".

### 2. Modalità Ibrida e Manuale
Per un controllo granulare, è possibile definire manualmente sia i segmenti che gli eventi di movimento direttamente dalla GUI, anche in modo combinato.

La GUI è organizzata in sezioni per gestire i dati in modo intuitivo. Di seguito sono descritte le principali modalità di lavoro manuali e ibride.

---

### A. Template a Tempi Fissi (Consigliato per Paradigmi Standard)
Questa modalità è la più potente e precisa per analizzare esperimenti che seguono una temporizzazione predefinita e ripetibile. Permette di saltare completamente la ricerca automatica e l'etichettatura manuale, garantendo massima coerenza tra le analisi.

**Come funziona:**
1.  **Crea il Template una Sola Volta**: Per un dato paradigma sperimentale, si crea un unico file CSV (es. `template_standard.csv`) che descrive la temporizzazione di tutti gli eventi. I tempi in questo file sono **relativi** a un punto "zero", che per convenzione è l'inizio del segmento `fast`.
2.  **Carica il Template**: Dalla GUI, clicca su **"Carica Template a Tempi Fissi..."** e seleziona il tuo file template.
3.  **Definisci l'Onset**: Questo è l'unico passaggio manuale richiesto. Il software ti chiederà di specificare a quale frame del video corrisponde il punto "zero" del template (l'**onset**). Puoi farlo in due modi:
    - **Inserisci Manualmente**: Digitando il numero esatto del frame.
    - **Seleziona da Video**: Usando un player interattivo per trovare e cliccare sul frame esatto.
4.  **Configurazione Automatica**: Una volta definito l'onset, il software esegue tutto in automatico:
    - **Calcola i Tempi Assoluti**: Somma il frame di onset a tutti i tempi relativi presenti nel template.
    - **Imposta i Segmenti**: Compila automaticamente i campi di inizio/fine per i segmenti "fast" e "slow" e attiva la modalità "Definisci Segmenti Manualmente".
    - **Crea il File Eventi**: Genera un nuovo file CSV (es. `manual_events_fixed.csv`) nella cartella di output con i tempi assoluti di ogni trial (movimento).
    - **Imposta gli Eventi**: Compila automaticamente il percorso di questo nuovo file. Il programma userà questo file per l'analisi.

A questo punto, l'intera analisi è pre-configurata con la massima precisione. Basta cliccare su "Avvia Analisi Completa".

---

### B. Definizione Interattiva
Questa modalità ti dà il pieno controllo visivo sull'analisi.

#### 1. Definire i Segmenti (Fast/Slow)
- Clicca il pulsante **"Definisci Segmenti FAST/SLOW (Interattivo)"**.
- Si aprirà un video player che ti permetterà di scorrere il video, definire l'inizio e la fine per i segmenti "fast" e "slow" e confermare.
- Una volta chiusa la finestra, i campi interni del programma verranno compilati e l'analisi userà questi valori, saltando la ricerca automatica.

#### 2. Definire gli Eventi di Movimento (Trial)
- Clicca il pulsante **"Definisci Eventi UP/DOWN/LEFT/RIGHT (Interattivo)"**.
- Si aprirà il video player. Potrai definire l'inizio e la fine di ogni trial, etichettandolo (es. "right", "left").
- Al termine, il programma ti chiederà di **salvare le annotazioni in un file .csv** (es. `manual_events.csv`).
- Il percorso di questo file verrà inserito automaticamente nella GUI, pronto per essere usato nell'analisi.

---

### C. Caricare e Salvare File di Eventi
Questa modalità è utile per riutilizzare definizioni già create o per preparare l'analisi in anticipo.

#### 1. Caricare/Salvare Segmenti (Fast/Slow)
- **Carica**: Usa **"Carica Segmenti FAST/SLOW (da CSV)"** per caricare un file `.csv` con i frame di inizio e fine dei segmenti.
- **Salva**: Usa **"Salva Segmenti FAST/SLOW (CSV Assoluto)"** per salvare i segmenti attualmente definiti (automaticamente o manualmente) in un file `.csv`.

#### 2. Caricare Eventi di Movimento (Trial)
- Prepara un file `.csv` con le specifiche di ogni trial (vedi formato sotto).
- Clicca su **"Carica Eventi U/D/L/R (da CSV)"** e seleziona il tuo file.
- Il programma salterà l'identificazione automatica dei movimenti e userà i dati del tuo file.

#### 3. Salvare un Template Relativo
- Dopo aver completato un'analisi (definendo segmenti e trial), puoi salvarla come un nuovo template riutilizzabile tramite **"Salva Template Relativo Corrente (in CSV)"**. Il software ti chiederà di definire un punto "zero" (onset) e convertirà tutti i tempi assoluti in relativi.

---

### E. Parametri di Analisi
La GUI presenta una sezione dedicata ai "Parametri di Analisi" che permette di affinare il comportamento degli algoritmi:

- **Padding Box Inseguimento (%)**: Controlla la dimensione dell'area di tolleranza usata per determinare se lo sguardo è "sulla palla" (`gaze_in_box`). Un valore più alto rende l'analisi più permissiva (box più grande), mentre un valore più basso la rende più conservativa (box più piccolo). Il default è 20%.

- **Soglia Successo Escursione (%)**: Definisce la percentuale minima di tempo che lo sguardo deve passare all'interno del box di inseguimento affinché un trial sia considerato "di successo" per la metrica `escursione_successo_perc`. Il default è 80%.

Questi parametri vengono passati agli script di analisi quando si clicca su "Avvia Analisi Completa".

> **Nota**: Se si desidera calcolare le metriche di escursione, è necessario spuntare la casella "Calcola metriche 'Escursione' e 'Escursione Direzionale'".


---

### D. Formati dei File CSV

#### 1. Formato per Template a Tempi Fissi
Il file deve contenere le colonne: `event_type`, `direction`, `relative_start`, `relative_end`.

- **event_type**: `segment` (per i blocchi fast/slow) o `trial` (per i movimenti)
- **direction**: `fast`, `slow`, `up`, `down`, `left`, `right`
- **relative_start / relative_end**: I numeri di frame relativi all'inizio dell'esperimento (l'onset)

**Esempio (`template_tempi.csv`)**
```csv
event_type,direction,relative_start,relative_end
segment,fast,0,5000
segment,slow,6000,15000
trial,right,200,450
trial,left,700,950
```

#### 2. Formato per Eventi Manuali
Il file deve contenere le colonne: `segment_name`, `direction_simple`, `start_frame`, `end_frame`.

- **segment_name**: `fast` o `slow`
- **direction_simple**: `right`, `left`, `up`, o `down`
- **start_frame / end_frame**: I numeri di frame assoluti nel video

**Esempio (`manual_events.csv`)**
```csv
segment_name,direction_simple,start_frame,end_frame
fast,right,5010,5090
fast,left,5150,5230
```

---

## 📋 Prerequisiti

È necessario acquisire i dati con **Pupil Labs Neon**, usare gli **AprilTag** e processare la registrazione su **Pupil Cloud** con l'enrichment **Marker Mapper**.  
La cartella scaricata da Pupil Cloud deve contenere i file:

- `video.mp4`
- `gaze.csv`
- `world_timestamps.csv`
- `surface_positions.csv`

---

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

---

## 📊 Output del Progetto

Il software genera una serie di file nella cartella di output specificata, fornendo un'analisi completa.

- **`final_report.xlsx`**: Il file più importante, un report Excel con metriche dettagliate e di riepilogo. (Vedi dettagli sotto)
- **`final_video_fast.mp4` / `final_video_slow.mp4`**: Video dei segmenti "fast" e "slow" con overlay dei dati di sguardo (posizione, tracciamento della palla).
- **`output_final_analysis_analysis.csv`**: Un file CSV contenente i dati grezzi calcolati, frame per frame, che costituisce la base per il report finale.
- **`cut_points.csv`**: Un file CSV che memorizza i frame di inizio e fine dei segmenti "fast" e "slow", sia che siano stati trovati automaticamente o definiti manualmente.
- **Cartella `plots_and_heatmaps/`**: Contiene tutte le visualizzazioni grafiche generate, come:
  - Heatmap dello sguardo per ogni direzione.
  - Grafici dell'andamento pupillare medio.
  - Grafici di frammentazione dello sguardo (se l'opzione è attiva).

### Dettaglio del `final_report.xlsx`

Questo file Excel è il prodotto finale dell'analisi e riassume le performance visuo-motorie del partecipante. È strutturato in diversi fogli di lavoro per fornire sia una visione d'insieme che un'analisi dettagliata per ogni segmento dell'esperimento (`fast` e `slow`).

Il report è composto da 5 fogli di lavoro:

1.  **`Riepilogo_Generale`**: Fornisce una sintesi ad alto livello, confrontando le performance complessive tra i segmenti "fast" e "slow".
2.  **`Riepilogo_fast`**: Contiene le metriche aggregate per ogni direzione di movimento (`up`, `down`, `left`, `right`) all'interno del solo segmento "fast".
3.  **`Dettagli_fast`**: Mostra i dati grezzi, frame per frame, per tutti i trial (movimenti) identificati nel segmento "fast".
4.  **`Riepilogo_slow`**: Simile a `Riepilogo_fast`, ma per il segmento "slow".
5.  **`Dettagli_slow`**: Simile a `Dettagli_fast`, ma per il segmento "slow".

---

#### 1. Foglio: `Riepilogo_Generale`

Questo foglio è il punto di partenza ideale. Offre un confronto diretto delle metriche chiave tra i due segmenti principali dell'esperimento. Ogni riga corrisponde a un segmento (`fast` o `slow`).

| Colonna | Descrizione e Metodo di Calcolo |
| :--- | :--- |
| **`segmento`** | Indica il segmento di riferimento per quella riga (`fast` o `slow`). |
| **`gaze_in_box_perc_totale`** | **Cosa misura:** La percentuale di tempo in cui lo sguardo del partecipante si trovava correttamente sulla palla (all'interno di un'area di tolleranza) durante tutti i trial di quel segmento. <br> **Come si calcola:** È la media della colonna `gaze_in_box` (che vale 1 se lo sguardo è nel box, 0 altrimenti) per tutti i frame che appartengono a un trial valido, moltiplicata per 100. Un valore alto indica un buon inseguimento. |
| **`velocita_sguardo_media`** | **Cosa misura:** La velocità media dello sguardo durante i trial. <br> **Come si calcola:** È la media della colonna `gaze_speed`. La velocità istantanea (`gaze_speed`) è calcolata come la distanza euclidea tra le coordinate normalizzate dello sguardo in due frame consecutivi. |
| **`numero_trial_validi`** | **Cosa misura:** Il numero totale di movimenti (trial) validi che il software ha identificato in quel segmento. <br> **Come si calcola:** È il conteggio dei valori unici di `trial_id` maggiori di zero. |
| **`diametro_pupillare_medio`** | **Cosa misura:** Il diametro medio della pupilla (in mm) durante tutti i trial del segmento. <br> **Come si calcola:** È la media della colonna `pupil_diameter_mean`. Questa metrica è presente solo se i dati pupillari sono disponibili. |
| **`escursione_successo_perc`** | **Cosa misura:** La percentuale di trial considerati "di successo" in termini di completamento della traiettoria. <br> **Come si calcola:** Un trial è un "successo" se la metrica `gaze_in_box` è stata `True` per almeno l'80% della sua durata. Questa colonna mostra la percentuale di trial che hanno superato tale soglia. È presente solo se l'analisi "Escursione" è attiva. |
| **`escursione_perc_frames_media`** | **Cosa misura:** La percentuale media di completamento della traiettoria (inseguimento della palla) per ogni trial. <br> **Come si calcola:** Per ogni trial, si calcola la percentuale di frame in cui lo sguardo era nel box. Questa colonna è la media di tali percentuali su tutti i trial del segmento. È presente solo se l'analisi "Escursione" è attiva. |
| **`escursione_direzionale_successo_perc`** | **Cosa misura:** La percentuale di trial in cui lo sguardo ha raggiunto con successo il bordo corretto dello schermo (es. bordo superiore per un trial 'up'). <br> **Come si calcola:** Un trial è un "successo direzionale" se, in almeno un frame, la coordinata dello sguardo supera una soglia predefinita vicino al bordo (es. 15% dal margine). Questa colonna è la percentuale di trial che soddisfano questa condizione. |
| **`escursione_direzionale_raggiunta_perc_media`** | **Cosa misura:** La media del successo direzionale, espressa come valore tra 0 e 1. <br> **Come si calcola:** È la media della colonna `directional_excursion_reached` (che vale 1 per successo, 0 per fallimento). Il valore è numericamente equivalente a `escursione_direzionale_successo_perc / 100`. |

---

#### 2. Fogli: `Riepilogo_fast` e `Riepilogo_slow`

Questi fogli "spaccano" i dati del riepilogo generale, mostrando le performance per ogni singola direzione di movimento. Questo permette di identificare eventuali asimmetrie o difficoltà specifiche (es. il partecipante segue bene a destra ma male in alto). Le colonne sono le stesse del riepilogo generale, ma calcolate raggruppando per direzione.

| Colonna | Descrizione e Metodo di Calcolo |
| :--- | :--- |
| **`direction_simple`** | La direzione del movimento (`right`, `left`, `up`, `down`). |
| **`avg_gaze_in_box_perc`** | **Cosa misura:** La percentuale di tempo in cui lo sguardo era sulla palla, ma mediata solo per i trial di una specifica direzione. <br> **Come si calcola:** È la media di `gaze_in_box` per tutti i frame dei trial che vanno in quella direzione, moltiplicata per 100. |
| **`avg_gaze_speed`** | **Cosa misura:** La velocità media dello sguardo solo per i trial di una specifica direzione. <br> **Come si calcola:** È la media di `gaze_speed` per tutti i frame dei trial che vanno in quella direzione. |
| **`trial_count`** | **Cosa misura:** Il numero di trial eseguiti in quella specifica direzione. <br> **Come si calcola:** Conteggio dei trial unici per quella direzione. |
| **`avg_pupil_diameter`** | **Cosa misura:** Il diametro pupillare medio solo per i trial di una specifica direzione. <br> **Come si calcola:** Media di `pupil_diameter_mean` per i trial di quella direzione. |
| **`excursion_success_perc`** | **Cosa misura:** La percentuale di trial di successo per una specifica direzione. <br> **Come si calcola:** Percentuale di trial in quella direzione che superano la soglia dell'80% di `gaze_in_box`. |
| **`avg_excursion_perc_frames`** | **Cosa misura:** La percentuale media di completamento dell'inseguimento per i trial di una specifica direzione. <br> **Come si calcola:** Media delle percentuali di completamento per ogni trial di quella direzione. |
| **`directional_excursion_success_perc`** | **Cosa misura:** La percentuale di trial di successo direzionale per una specifica direzione. <br> **Come si calcola:** Percentuale di trial in quella direzione in cui lo sguardo ha raggiunto il bordo corretto. |
| **`avg_directional_excursion_reached`** | **Cosa misura:** La media del successo direzionale per i trial di una specifica direzione. <br> **Come si calcola:** Media di `directional_excursion_reached` per i trial di quella direzione. |

---

#### 3. Fogli: `Dettagli_fast` e `Dettagli_slow`

Questi sono i fogli più granulari e contengono i dati calcolati per ogni singolo frame che fa parte di un trial. Sono utili per analisi approfondite o per debug.

| Colonna | Descrizione |
| :--- | :--- |
| **`frame`** | Il numero del frame nel video originale. |
| **`ball_center_x_norm`, `ball_center_y_norm`** | Coordinate normalizzate (0-1) del centro della palla. |
| **`gaze_x_norm`, `gaze_y_norm`** | Coordinate normalizzate (0-1) del punto di sguardo sulla superficie. |
| **`gaze_in_box`** | Valore booleano (`True`/`False`) che indica se il punto di sguardo (`gaze`) si trova all'interno del rettangolo di tracciamento della palla. |
| **`direction`** | Descrizione completa del movimento (es. `center_to_right`). |
| **`trial_id`** | Un numero intero che identifica univocamente ogni movimento. Tutti i frame con lo stesso `trial_id` appartengono allo stesso evento. |
| **`direction_simple`** | La direzione cardinale del movimento (`right`, `left`, `up`, `down`). |
| **`ball_speed`, `gaze_speed`** | Velocità istantanea della palla e dello sguardo, calcolata tra frame consecutivi. |
| **`pupil_diameter_mean`** | Diametro pupillare (mm) sincronizzato a quel frame. |
| **`excursion_perc_frames`** | Percentuale di completamento del trial a cui questo frame appartiene (è lo stesso valore per tutti i frame dello stesso `trial_id`). |
| **`excursion_success`** | Valore booleano (`True`/`False`) che indica se il trial a cui questo frame appartiene è stato un successo di inseguimento (è lo stesso valore per tutti i frame dello stesso `trial_id`). |
| **`directional_excursion_reached`** | Valore numerico (1.0/0.0) che indica se il trial a cui questo frame appartiene ha raggiunto il bordo corretto. |
| **`directional_excursion_success`** | Valore booleano (`True`/`False`) che indica se il trial a cui questo frame appartiene è stato un successo direzionale. |
