# Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)
### LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)

- **Sito Web Lab**: [labscoc.wordpress.com](https://labscoc.wordpress.com/)
- **Repository GitHub**: [github.com/danielelozzi/neurological-assessment](https://github.com/danielelozzi/neurological-assessment)

Questo repository contiene una pipeline software completa per l'analisi del movimento oculare e della pupillometria in relazione al movimento di un cerchio su uno schermo.

L'intero processo è gestito da un'unica **interfaccia grafica (GUI)** che orchestra l'elaborazione dei dati, dal taglio dei video grezzi fino alla generazione di un report statistico e visuale completo.

---

## 🎯 Obiettivo del Software

L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. Partendo dai dati grezzi elaborati da Pupil Cloud, il software esegue i seguenti passaggi:
1.  **Identifica i Segmenti di Test**: Utilizzando il riconoscimento ottico dei caratteri (OCR), lo script individua automaticamente i frame di inizio e fine dei segmenti di interesse del test ("fast" e "slow").
2.  **Correzione Prospettica e Creazione Video**: Per ogni segmento, applica una correzione della prospettiva basata sugli AprilTag, isolando l'area dello schermo e generando video finali raddrizzati.
3.  **Rilevamento e Sincronizzazione**: Rileva il cerchio e ne traccia il movimento all'interno dei video corretti, sincronizzando la posizione dello sguardo (gaze) e i dati pupillometrici per ogni frame.
4.  **Analisi Dati e Overlay**:
    * Calcola metriche chiave come velocità dello sguardo e del cerchio, percentuale di tempo in cui lo sguardo è sul target e diametro pupillare medio.
    * **Scrive in sovrimpressione la direzione del movimento** (UP, DOWN, LEFT, RIGHT) direttamente sui video finali per un'analisi qualitativa immediata.
    * Esegue una validazione della sequenza dei movimenti e, specificamente per il protocollo "slow", esclude l'ultimo movimento "up" dall'analisi statistica per allinearsi al disegno sperimentale.
5.  **Generazione dell'Output**: Produce video finali con overlay, un report Excel dettagliato e visualizzazioni grafiche (heatmap, grafici pupillometrici).

---

## 📋 Prerequisiti: Acquisizione e Preparazione dei Dati

Prima di utilizzare questo software, è necessario acquisire e preparare i dati seguendo una procedura specifica con gli strumenti di Pupil Labs.

1.  **Registrazione Video**: Utilizzare gli occhiali **Pupil Labs Neon** per registrare la sessione di test.
2.  **Definizione della Superficie (AprilTag)**: Posizionare degli **AprilTag** ai quattro angoli dello schermo. Questi marcatori permettono al software di tracciare la superficie e mappare le coordinate dello sguardo.
    * Dettagli: [**Pupil Labs Surface Tracker**](https://docs.pupil-labs.com/neon/neon-player/surface-tracker/).
3.  **Caricamento su Pupil Cloud**: Caricare la registrazione sulla piattaforma **Pupil Cloud**.
4.  **Enrichment con Marker Mapper**: All'interno di Pupil Cloud, avviare l'enrichment **Marker Mapper** per generare il file `surface_positions.csv`.
    * Guida: [**Pupil Cloud Marker Mapper**](https://docs.pupil-labs.com/neon/pupil-cloud/enrichments/marker-mapper/#setup).
5.  **Download dei Dati**: Al termine, **scaricare l'intera cartella dei dati** dal progetto. Questa cartella deve contenere tutti i file necessari per l'analisi:
    * `video.mp4`: Il video della scena.
    * `gaze.csv`: Dati dettagliati dello sguardo.
    * `world_timestamps.csv`: Dati di sincronizzazione dei frame.
    * `surface_positions.csv`: Coordinate della superficie tracciata.
    * **Per analisi pupillometrica**: `3d_eye_states.csv`. L'inclusione di questo file è **essenziale** per calcolare le metriche relative al diametro pupillare.

---

## 🛠️ Installazione

Per utilizzare il software, sono necessarie alcune librerie Python. È fortemente consigliato creare un ambiente virtuale.

1.  **Crea un ambiente virtuale**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

2.  **Installa le librerie richieste**:
    ```bash
    pip install customtkinter opencv-python pandas numpy matplotlib seaborn scipy easyocr ultralytics xlsxwriter
    ```

---

## 🚀 Utilizzo

L'intera pipeline viene eseguita tramite l'interfaccia grafica.

1.  **Avvia la GUI**:
    Esegui il seguente comando dalla directory principale del progetto:
    ```bash
    python main_gui.py
    ```
    ![Interfaccia Grafica CNA](gui_cna.png)

2.  **Configura l'Analisi**:
    * **1. Seleziona la Cartella Input**: Scegli la **cartella scaricata da Pupil Cloud**.
    * **2. Seleziona la Cartella Output**: Scegli una cartella dove verranno salvati **tutti i risultati**.
    * **3. Scegli il Metodo di Rilevamento**: **YOLO** (raccomandato, richiede un modello `.pt`) o **Hough Circle**.
    * **4. Seleziona il Modello YOLO (se necessario)**: Carica il file del modello `.pt`.

3.  **Avvia l'Analisi**:
    Una volta configurati tutti i percorsi, il pulsante **"Avvia Analisi Completa"** diventerà cliccabile. Premilo per iniziare.

4.  **Monitora il Progresso**:
    Puoi seguire ogni fase dell'elaborazione nel riquadro **"Log di Analisi"** in tempo reale.

---

## 📊 Output del Progetto

Al termine dell'analisi, troverai i seguenti file nella cartella di Output che hai scelto:

* **`final_report.xlsx`**: Il report quantitativo finale. Include:
    * Un foglio di **`Riepilogo_Generale`** con le medie complessive per i segmenti "fast" e "slow".
    * Fogli di **riepilogo per direzione** (`Riepilogo_fast`, `Riepilogo_slow`) con metriche di sguardo e pupillometria.
    * Fogli di **dati dettagliati** (`Dettagli_fast`, `Dettagli_slow`) con i valori calcolati per ogni frame.

* **`final_video_fast.mp4` / `final_video_slow.mp4`**: I video finali dei segmenti di test. Questi video sono già ritagliati sulla superficie dello schermo, corretti nella prospettiva e includono **l'overlay dello sguardo e l'indicazione testuale della direzione del movimento** (es. "UP", "RIGHT") per una revisione qualitativa immediata.

* **`output_final_analysis_analysis.csv`**: I dati grezzi, frame per frame, calcolati dalla pipeline (posizione del cerchio, posizione dello sguardo, diametro pupillare, ecc.).

* **`cut_points.csv`**: I frame di inizio/fine dei segmenti "fast" e "slow", calcolati tramite OCR. Questo è l'unico output della prima fase di analisi.

* **Cartella `plots_and_heatmaps/`**: Contiene le visualizzazioni grafiche, incluse le **heatmap** dello sguardo e i **grafici sull'andamento della pupillometria** per ogni direzione di movimento (se i dati erano disponibili).

---

## Citazione

*Se utilizzi questo script nella tua ricerca o nel tuo lavoro, ti preghiamo di citare le seguenti pubblicazioni:*

Lozzi, D.; Di Pompeo, I.; Marcaccio, M.; Ademaj, M.; Migliore, S.; Curcio, G. SPEED: A Graphical User Interface Software for Processing Eye Tracking Data. NeuroSci 2025, 6, 35. [https://doi.org/10.3390/neurosci6020035](https://doi.org/10.3390/neurosci6020035)

Lozzi, D.; Di Pompeo, I.; Marcaccio, M.; Alemanno, M.; Krüger, M.; Curcio, G.; Migliore, S. AI-Powered Analysis of Eye Tracker Data in Basketball Game. Sensors 2025, 25, 3572. [https://doi.org/10.3390/s25113572](https://doi.org/10.3390/s25113572)

---

*This tool is developed for the Cognitive and Behavioral Science Lab. For more information, visit [our website](https://labscoc.wordpress.com/).*