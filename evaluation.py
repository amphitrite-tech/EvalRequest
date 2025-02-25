import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

def list_csv_files(directory="data"):
    """Liste tous les fichiers CSV dans le répertoire."""
    return [f for f in os.listdir(directory) if f.endswith('.csv')]

def load_and_process_data(file_path):
    """Charge et traite les données d'un fichier CSV."""
    with open(file_path, 'r') as file:
        content = file.readlines()
    
    dir_start = next(i for i, line in enumerate(content) if 'Error Distribution: Direction' in line)
    neva_start = next(i for i, line in enumerate(content) if 'Error Distribution: NEVA' in line)
    
    dir_data = pd.read_csv(file_path, skiprows=dir_start+1, nrows=4, engine='python')
    neva_data = pd.read_csv(file_path, skiprows=neva_start+1, nrows=4, engine='python')
    
    return dir_data, neva_data

def extract_metadata(file_path):
    """Extrait les métadonnées d'un fichier CSV."""
    metadata = {}
    with open(file_path, 'r') as file:
        content = file.readlines()
        
        # Extraction des métadonnées de base
        metadata['instruments'] = content[1].split(': ')[1].strip()
        metadata['periode'] = content[2].split(': ')[1].strip()
        metadata['model'] = content[3].split(': ')[1].strip()
        metadata['region'] = content[4].split(': ')[1].strip()
        
        # Extraction des types d'erreur avec leurs paramètres
        error_types = []
        for line in content:
            if 'Error Distribution:' in line:
                error_info = line.split('Error Distribution:')[1].strip()
                param = error_info.split('(')[1].split(')')[0] if '(' in error_info else ''
                error_type = error_info.split('(')[0].strip()
                error_types.append(f"{error_type} ({param})")
        metadata['type_erreur'] = ', '.join(error_types)
    return metadata

def create_files_dataframe():
    """Crée un DataFrame avec tous les fichiers CSV et leurs métadonnées."""
    files_data = []
    for file in list_csv_files():
        file_path = os.path.join("data", file)
        metadata = extract_metadata(file_path)
        files_data.append({
            'Fichier': file,
            'Region': metadata['region'],
            'Instruments': metadata['instruments'],
            'Période': metadata['periode'],
            'Modèles': metadata['model'],
            'Types d\'erreur': metadata['type_erreur']
        })
    return pd.DataFrame(files_data)

def display_analysis(dir_data, neva_data):
    """Affiche les graphiques et métriques pour un fichier."""
    tab1, tab2 = st.tabs(["Distribution des Erreurs de Direction", "Distribution NEVA"])

    with tab1:
        st.header("Distribution des Erreurs de Direction")
        
        # Graphique en barres côte à côte avec les colonnes correctes
        fig_dir = go.Figure()
        x_values = dir_data.iloc[:, 0]  # Première colonne pour l'axe x
        fig_dir.add_trace(go.Bar(name='HIRESv1_MED_d0', x=x_values, y=dir_data['HIRESv1_MED_d0']))
        fig_dir.add_trace(go.Bar(name='HIRESv3_MED_d1', x=x_values, y=dir_data['HIRESv3_MED_d1']))
        fig_dir.update_layout(barmode='group', yaxis_title="Pourcentage (%)")
        st.plotly_chart(fig_dir)

        # Métriques pour la direction
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Erreurs < 45° - HIRESv1", 
                     f"{dir_data['HIRESv1_MED_d0'].iloc[0:2].sum():.1f}%")
        with col2:
            st.metric("Erreurs < 45° - HIRESv3", 
                     f"{dir_data['HIRESv3_MED_d1'].iloc[0:2].sum():.1f}%")

    with tab2:
        st.header("Distribution NEVA")
        
        # Graphique en ligne pour NEVA avec les colonnes correctes
        fig_neva = go.Figure()
        x_values_neva = neva_data.iloc[:, 0]  # Première colonne pour l'axe x
        fig_neva.add_trace(go.Scatter(x=x_values_neva, y=neva_data['HIRESv1_MED_d0'],
                                     mode='lines+markers', name='HIRESv1_MED_d0'))
        fig_neva.add_trace(go.Scatter(x=x_values_neva, y=neva_data['HIRESv3_MED_d1'],
                                     mode='lines+markers', name='HIRESv3_MED_d1'))
        fig_neva.update_layout(yaxis_title="Pourcentage (%)")
        st.plotly_chart(fig_neva)

        # Métriques pour NEVA
        col1, col2 = st.columns(2)
        with col1:
            st.metric("NEVA < 66% - HIRESv1", 
                     f"{neva_data['HIRESv1_MED_d0'].iloc[0:2].sum():.1f}%")
        with col2:
            st.metric("NEVA < 66% - HIRESv3", 
                     f"{neva_data['HIRESv3_MED_d1'].iloc[0:2].sum():.1f}%")

# Configuration de la page
st.set_page_config(page_title="Analyse des Erreurs", layout="wide")

# Interface principale
st.title("Analyse des Distributions d'Erreurs")

# Création du DataFrame des fichiers
files_df = create_files_dataframe()
st.markdown("### Liste des fichiers disponibles")

# Affichage du tableau des fichiers
st.dataframe(
    files_df,
    hide_index=True,
    column_config={
        "Fichier": st.column_config.Column(
            "Fichier",
            width="medium",
        ),
        "Types d'erreur": st.column_config.Column(
            "Types d'erreur",
            width="large",
        ),
    },
    use_container_width=True
)

# Ajout d'un sélecteur de fichier
selected_file = st.selectbox(
    "Sélectionner un fichier à analyser:",
    files_df['Fichier'].tolist(),
    key="file_selector"
)

# Si un fichier est sélectionné
if selected_file:
    file_path = os.path.join("data", selected_file)
    
    # Charger les données
    dir_data, neva_data = load_and_process_data(file_path)
    
    # Afficher les métadonnées du fichier sélectionné
    st.markdown(f"### Analyse du fichier : {selected_file}")
    
    # Créer un tableau des types d'erreur
    error_types = pd.DataFrame({
        'Type d\'erreur': ['Direction', 'NEVA'],
        'Description': [
            f"Erreurs de direction (0-15°: {dir_data['HIRESv1_MED_d0'].iloc[0]:.1f}%, ...)",
            f"Distribution NEVA (0-33%: {neva_data['HIRESv1_MED_d0'].iloc[0]:.1f}%, ...)"
        ]
    })
    
    st.markdown("### Détails des erreurs")
    st.dataframe(error_types, hide_index=True, use_container_width=True)
    
    # Afficher les analyses
    display_analysis(dir_data, neva_data)
