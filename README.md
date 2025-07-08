 Strumento di Analisi Neuro-Visuale - LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)

- **Sito Web Lab**: [labscoc.wordpress.com](https://labscoc.wordpress.com/)
- **Repository GitHub**: [github.com/danielelozzi/neurological-assessment](https://github.com/danielelozzi/neurological-assessment)

[cite_start]Questo repository contiene una pipeline software completa per l'analisi del movimento oculare in relazione al movimento di una palla. [cite: 3]

[cite_start]L'intero processo è gestito da un'unica **interfaccia grafica (GUI)** che orchestra l'elaborazione dei dati, dal taglio dei video grezzi fino alla generazione di un report statistico finale. [cite: 3]

---

## 🎯 Obiettivo del Software

[cite_start]L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. [cite: 3] Partendo dai dati grezzi elaborati da Pupil Cloud, il software:
1.  [cite_start]**Identifica e isola** i segmenti di interesse del test ("fast" e "slow"). [cite: 3]
2.  [cite_start]**Rileva la palla** e ne traccia il movimento nel video. [cite: 3]
3.  [cite_start]**Sincronizza i dati dello sguardo** con la posizione della palla. [cite: 3]
4.  [cite_start]**Calcola metriche chiave** come la velocità dello sguardo, la velocità della palla e la percentuale di tempo in cui lo sguardo è correttamente sulla palla. [cite: 3, 6]
5.  [cite_start]**Produce un report Excel dettagliato** e visualizzazioni grafiche (heatmap, grafici pupillometrici) per un'analisi approfondita. [cite: 3, 6]

---

## 📋 Prerequisiti: Acquisizione e Preparazione dei Dati

Prima di utilizzare questo software, è necessario acquisire e preparare i dati seguendo una procedura specifica con gli strumenti di Pupil Labs.

1.  **Registrazione Video**: Utilizzare gli occhiali **Pupil Labs Neon** per registrare la sessione di test. Per l'analisi è fondamentale inquadrare una superficie piana (es. un monitor o un tavolo).
2.  **Definizione della Superficie (AprilTag)**: Posizionare degli **AprilTag** ai quattro angoli della superficie di interesse. Questi marcatori permettono al software di Pupil Labs di tracciare la superficie e mappare le coordinate dello sguardo su di essa.
    * Per maggiori dettagli, consultare la documentazione ufficiale: [**Pupil Labs Surface Tracker**](https://docs.pupil-labs.com/neon/neon-player/surface-tracker/).
3.  **Caricamento su Pupil Cloud**: Una volta completata la registrazione, caricare i dati sulla piattaforma **Pupil Cloud**.
4.  **Enrichment con Marker Mapper**: All'interno di Pupil Cloud, avviare l'enrichment **Marker Mapper**. Questo processo analizza il video, rileva gli AprilTag e genera il file `surface_positions.csv`, che contiene le coordinate della superficie per ogni frame.
    * Guida all'utilizzo del Marker Mapper: [**Pupil Cloud Marker Mapper**](https://docs.pupil-labs.com/neon/pupil-cloud/enrichments/marker-mapper/#setup).
5.  **Download dei Dati**: Al termine dell'enrichment, **scaricare l'intera cartella dei dati** dal progetto su Pupil Cloud. Questa cartella conterrà tutti i file necessari per l'analisi (`video.mp4`, `gaze.csv`, `surface_positions.csv`, `world_timestamps.csv`, etc.).

---

## 🛠️ Installazione

Per utilizzare il software, sono necessarie alcune librerie Python. [cite_start]È fortemente consigliato creare un ambiente virtuale per gestire le dipendenze. [cite: 3]

1.  [cite_start]**Crea un ambiente virtuale**: [cite: 3]
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

2.  [cite_start]**Installa le librerie richieste**: [cite: 3]
    ```bash
    pip install customtkinter opencv-python pandas numpy matplotlib seaborn scipy easyocr ultralytics xlsxwriter
    ```

---

## 🚀 Utilizzo

[cite_start]L'intera pipeline viene eseguita tramite l'interfaccia grafica. [cite: 3]

1.  [cite_start]**Avvia la GUI**: [cite: 3]
    [cite_start]Esegui il seguente comando dalla directory principale del progetto: [cite: 3]
    ```bash
    python main_gui.py
    ```

2.  **Configura l'Analisi**:
    [cite_start]Dalla finestra dell'applicazione, segui questi passaggi: [cite: 3]

    * **1. [cite_start]Seleziona la Cartella Input**: Clicca su "Seleziona..." e scegli la **cartella scaricata da Pupil Cloud** dopo aver eseguito l'enrichment con Marker Mapper. [cite: 3]

    * **2. [cite_start]Seleziona la Cartella Output**: Clicca su "Seleziona..." e scegli una cartella (anche vuota) dove verranno salvati **tutti i risultati** dell'analisi (video tagliati, report, grafici). [cite: 3]

    * **3. [cite_start]Scegli il Metodo di Rilevamento**: [cite: 3]
        * [cite_start]**YOLO**: Più moderno e accurato, ma richiede un file modello (`.pt`). [cite: 3]
        * [cite_start]**Hough Circle**: Meno accurato, ma non richiede file esterni. [cite: 3]

    * **4. [cite_start]Seleziona il Modello YOLO (se necessario)**: Se hai scelto YOLO, un'opzione aggiuntiva apparirà. [cite: 3] [cite_start]Clicca su "Seleziona..." per trovare e caricare il tuo file modello `.pt`. [cite: 3]

3.  **Avvia l'Analisi**:
    [cite_start]Una volta configurati tutti i percorsi, il pulsante **"Avvia Analisi Completa"** diventerà cliccabile. [cite: 3] [cite_start]Premilo per iniziare il processo. [cite: 3]

4.  **Monitora il Progresso**:
    [cite_start]Puoi seguire ogni fase dell'elaborazione nel riquadro **"Log di Analisi"** in tempo reale. [cite: 3]

---

## 📊 Output del Progetto

Al termine dell'analisi, troverai i seguenti file nella cartella di Output che hai scelto:

* [cite_start]**`final_report.xlsx`**: Il report quantitativo finale con tutte le metriche chiave, suddiviso per protocollo ("fast", "slow") e direzione del movimento. [cite: 3]
* [cite_start]**`output_final_analysis.mp4`**: Un video di riferimento con le annotazioni del rilevamento della palla e dello sguardo, utile per una revisione qualitativa. [cite: 3]
* [cite_start]**`output_final_analysis_analysis.csv`**: I dati grezzi, frame per frame, calcolati dalla pipeline. [cite: 3]
* [cite_start]**`cut_points.csv`**: I frame di inizio/fine dei segmenti "fast" e "slow". [cite: 3]
* [cite_start]**`trimmed_video_fast.mp4` / `trimmed_video_slow.mp4`**: I clip video dei singoli protocolli. [cite: 3]
* [cite_start]**Cartella `plots_and_heatmaps/`**: Contiene le visualizzazioni grafiche, incluse le heatmap dello sguardo e i grafici sulla pupillometria. [cite: 3]