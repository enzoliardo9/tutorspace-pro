import streamlit as st
from groq import Groq
import PyPDF2
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURAZIONE DELLA PAGINA (Enterprise Layout) ---
st.set_page_config(page_title="TutorSpace Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# --- RECUPERO DELLA CHIAVE SEGRETA ---
try:
    api_key = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("🛑 Errore: Chiave API mancante in .streamlit/secrets.toml")
    st.stop()

client = Groq(api_key=api_key)

# --- INIZIALIZZAZIONE MEMORIA ---
if "testo_pdf" not in st.session_state:
    st.session_state.testo_pdf = ""
if "dati_pdf" not in st.session_state:
    st.session_state.dati_pdf = {"pagine": 0, "caratteri": 0}
if "messaggi_chat" not in st.session_state:
    st.session_state.messaggi_chat = [{"role": "assistant", "content": "Benvenuto in TutorSpace Pro. Inizializzazione completata. Sistemi pronti."}]

def reset_sessione():
    st.session_state.testo_pdf = ""
    st.session_state.dati_pdf = {"pagine": 0, "caratteri": 0}
    st.session_state.messaggi_chat = [{"role": "assistant", "content": "Memoria azzerata. Pronto per un nuovo ciclo di studio."}]
    st.toast("Ambiente ripristinato.", icon="🔄")

# --- MOTORE DI ESPORTAZIONE PDF ---
def genera_pdf(messaggi):
    class ReportPDF(FPDF):
        def header(self):
            # Intestazione Professionale
            self.set_font('helvetica', 'B', 16)
            self.set_text_color(41, 128, 185) # Blu elegante
            self.cell(0, 10, 'TutorSpace Pro - Report Accademico', border=False, ln=True, align='C')
            self.set_font('helvetica', 'I', 10)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Generato il: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", border=False, ln=True, align='C')
            self.line(10, 30, 200, 30)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for msg in messaggi:
        if "Benvenuto in TutorSpace" in msg["content"]: continue
        
        ruolo = "Utente:" if msg["role"] == "user" else "Intelligenza Artificiale:"
        colore_titolo = (44, 62, 80) if msg["role"] == "user" else (39, 174, 96)
        
        # Titolo (Chi parla)
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_text_color(*colore_titolo)
        pdf.cell(0, 8, ruolo, ln=True)
        
        # Testo del messaggio
        pdf.set_font("helvetica", '', 11)
        pdf.set_text_color(0, 0, 0)
        
        # Pulizia del testo per evitare errori di codifica nel PDF (rimuove emoji e caratteri speciali non supportati dal font base)
        testo_pulito = msg['content'].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.multi_cell(0, 6, testo_pulito)
        pdf.ln(5)
        
    # La conversione fondamentale in bytes per Streamlit
    return bytes(pdf.output())

# --- BARRA LATERALE: DASHBOARD ---
with st.sidebar:
    st.markdown("### 📊 TutorSpace Pro")
    st.caption("Piattaforma Enterprise v6.0")
    st.divider()
    
    st.markdown("#### ⚙️ Controlli di Sistema")
    st.button("🔄 Svuota Memoria", on_click=reset_sessione, use_container_width=True)
    
    st.divider()
    st.markdown("#### 📑 Esportazione Avanzata")
    st.caption("Scarica il documento impaginato e pronto per la stampa.")
    
    # Bottone di esportazione PDF!
    pdf_bytes = genera_pdf(st.session_state.messaggi_chat)
    st.download_button(
        label="📥 Esporta Report PDF Pro",
        data=pdf_bytes,
        file_name=f"Report_Studio_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )

# --- AREA DI LAVORO ---
col_strumenti, col_chat = st.columns([2, 3], gap="large")

with col_strumenti:
    tab1, tab2 = st.tabs(["📄 Acquisizione Dati", "🧠 Pianificatore Avanzato"])

    # SCHEDA 1
    with tab1:
        st.markdown("#### Database Documentale")
        file_caricato = st.file_uploader("Carica File Sorgente (PDF)", type=["pdf"])
        
        if st.button("Avvia Estrazione 🔍", type="primary", use_container_width=True):
            if file_caricato:
                with st.spinner("Analisi morfologica del PDF in corso..."):
                    lettore = PyPDF2.PdfReader(file_caricato)
                    testo_estratto = "".join([p.extract_text() + "\n" for p in lettore.pages])
                    
                    st.session_state.testo_pdf = testo_estratto
                    st.session_state.dati_pdf = {"pagine": len(lettore.pages), "caratteri": len(testo_estratto)}
                    
                    st.session_state.messaggi_chat.append({
                        "role": "assistant", 
                        "content": f"✅ Acquisizione completata con successo. Ho elaborato {len(lettore.pages)} pagine."
                    })
                    st.rerun() # Ricarica per aggiornare l'interfaccia
            else:
                st.error("Inserire un file valido.")

        if st.session_state.dati_pdf["pagine"] > 0:
            st.markdown("##### Metriche in Tempo Reale")
            c1, c2 = st.columns(2)
            c1.metric("Pagine Processate", st.session_state.dati_pdf["pagine"])
            c2.metric("Volume Dati (Caratteri)", st.session_state.dati_pdf["caratteri"])

    # SCHEDA 2
    with tab2:
        st.markdown("#### Motore di Generazione Piani")
        argomento = st.text_input("Soggetto accademico", placeholder="Es: Economia Aziendale...")
        giorni = st.number_input("Orizzonte Temporale (Giorni)", 1, 60, 5)
        
        if st.button("Sintetizza Piano ⚙️", type="primary", use_container_width=True):
            if argomento:
                with st.spinner("Elaborazione..."):
                    istruzioni = f"Genera un piano didattico professionale per '{argomento}' di {giorni} giorni. Usa tabelle in Markdown per riassumere le fasi."
                    try:
                        risposta = client.chat.completions.create(
                            messages=[{"role": "user", "content": istruzioni}],
                            model="llama-3.3-70b-versatile",
                            stream=False
                        )
                        st.session_state.messaggi_chat.append({
                            "role": "assistant", "content": risposta.choices[0].message.content
                        })
                        st.rerun() # Ricarica per aggiornare subito il bottone PDF
                    except Exception as e:
                        st.error(f"Errore: {e}")

# --- TERMINALE CHAT ---
with col_chat:
    st.markdown("#### 💻 Terminale di Apprendimento")
    chat_container = st.container(height=650, border=True)
    
    with chat_container:
        for m in st.session_state.messaggi_chat:
            avatar_icon = "👤" if m["role"] == "user" else "🏛️"
            st.chat_message(m["role"], avatar=avatar_icon).markdown(m["content"])

    if domanda := st.chat_input("Inserisci un comando (es. 'Spiegami la cellula usando una tabella')"):
        st.session_state.messaggi_chat.append({"role": "user", "content": domanda})
        
        with chat_container:
            st.chat_message("user", avatar="👤").markdown(domanda)
            
            istruzioni_sistema = """
            Sei TutorSpace Pro, un sistema IA di altissimo livello.
            REGOLE RIGOROSE:
            1. Quando spieghi concetti complessi o paragoni due cose, USA SEMPRE DELLE TABELLE IN MARKDOWN.
            2. Usa un linguaggio accademico e strutturato (Titoli, Sottotitoli, Elenchi Numerati).
            3. Rendilo visivamente bellissimo da leggere. Non fare muri di testo. Non usare emoji.
            """
            
            if st.session_state.testo_pdf:
                istruzioni_sistema += f"\nDATASET: {st.session_state.testo_pdf}"
            
            messaggi_ia = [{"role": "system", "content": istruzioni_sistema}]
            messaggi_ia.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messaggi_chat])
            
            with st.chat_message("assistant", avatar="🏛️"):
                casella = st.empty()
                testo_risposta = ""
                try:
                    stream = client.chat.completions.create(
                        messages=messaggi_ia,
                        model="llama-3.3-70b-versatile",
                        stream=True
                    )
                    for blocco in stream:
                        if blocco.choices[0].delta.content:
                            testo_risposta += blocco.choices[0].delta.content
                            casella.markdown(testo_risposta)
                    st.session_state.messaggi_chat.append({"role": "assistant", "content": testo_risposta})
                    st.rerun() # Ricarica l'app silenziosamente per far aggiornare il bottone del PDF con la nuova risposta!
                except Exception as e:
                    st.error(f"Errore: {e}")