# visualizer.py

# Importations pour la visualisation
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from groq import Groq
import re 
import subprocess
import sys
from matplotlib.ticker import FuncFormatter

def setup_groq_client():
    """Configure et retourne le client Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    return Groq(api_key=api_key)

def generate_visualization(user_question, query_results, groq_client):
    """
    Génère un graphique à partir des résultats d'une requête.
    
    Args:
        user_question (str): La question posée par l'utilisateur.
        query_results (list): Les résultats de la requête SQL sous forme de liste de dictionnaires.
        groq_client: L'instance du client Groq pour interagir avec le LLM.
    
    Returns:
        str: Le chemin vers le fichier image du graphique généré, ou None en cas d'échec.
    """
    if not query_results:
        print("Les résultats de la requête sont vides, aucun graphique à générer.")
        return None

    df = pd.DataFrame(query_results)

    # L'invite pour demander au LLM de choisir les paramètres de visualisation.
    visualization_prompt = f"""
    Based on the following user question and the data provided, generate a single JSON object to configure a chart.
    Do not include any other text, explanation, or markdown formatting outside of the JSON object itself.
    
    User Question: {user_question}
    
    Data Columns: {list(df.columns)}
    
    JSON Object must contain the following keys:
    'chart_type': The best chart type (e.g., 'bar', 'line', 'pie'). Choose 'bar' for rankings or categorical data. Choose 'line' for time-series data. Use 'pie' for part-to-whole analysis (e.g., percentage of total).
    'x_column': The column name for the x-axis.
    'y_column': The column name for the y-axis.
    'title': A descriptive title for the chart.
    'x_label': A label for the x-axis.
    'y_label': A label for the y-axis.
    
    Example for a query about top products by sales:
    {{
      "chart_type": "bar",
      "x_column": "productName",
      "y_column": "totalSales",
      "title": "Top 10 Products by Sales",
      "x_label": "Product Name",
      "y_label": "Total Sales"
    }}
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "user", "content": visualization_prompt}
            ],
            model="llama3-8b-8192",
            temperature=0,
            max_tokens=200
        )
        json_output = chat_completion.choices[0].message.content.strip()

        json_match = re.search(r'\{.*\}', json_output, re.DOTALL)
        if not json_match:
            print("Erreur : aucun objet JSON valide trouvé dans la réponse de l'IA.")
            print(f"Réponse brute de l'IA : {json_output}")
            return None
            
        chart_config = json.loads(json_match.group(0))
        
    except Exception as e:
        print(f"Erreur lors de la génération JSON de la visualisation : {e}")
        print(f"Réponse brute de l'IA : {json_output}")
        return None

    # Création du graphique basée sur la configuration du LLM
    try:
        # Utiliser Seaborn pour un style plus professionnel
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(12, 8))

        # Vérifier si les colonnes 'year' et 'quarter' existent pour les regrouper.
        if 'year' in df.columns and 'quarter' in df.columns:
            # Créer une nouvelle colonne pour un affichage "année-trimestre"
            df['year_quarter'] = df['year'].astype(str) + '-T' + df['quarter'].astype(str)
            # Mettre à jour la colonne x dans la configuration du graphique
            chart_config['x_column'] = 'year_quarter'
            chart_config['x_label'] = 'Année et Trimestre'

        # Trier les données pour le graphique
        # if chart_config['y_column'] in df.columns:
            #df = df.sort_values(by=chart_config['y_column'], ascending=False)
        
        if chart_config['chart_type'] == 'bar':
            # Utiliser la colonne x_column pour les étiquettes de l'axe x
            x_values = df[chart_config['x_column']]
            
            # Créer le graphique à barres
            sns.barplot(x=x_values, y=df[chart_config['y_column']], palette="viridis", hue=x_values, legend=False)

            # Correction de l'avertissement 'set_ticklabels' en utilisant plt.xticks
            plt.xticks(rotation=45, ha='right')
            
        elif chart_config['chart_type'] == 'line':
            # Amélioration : Augmenter l'épaisseur de la ligne et la taille des marqueurs
            sns.lineplot(x=df[chart_config['x_column']], y=df[chart_config['y_column']], marker='o', linestyle='--', linewidth=2.5, markersize=8)
            # Ajouter une rotation pour les étiquettes de l'axe X pour les dates
            plt.xticks(rotation=45, ha='right')
        
        elif chart_config['chart_type'] == 'pie':
            # Créer un graphique en secteurs
            plt.figure(figsize=(10, 10))
            plt.pie(df[chart_config['y_column']], labels=df[chart_config['x_column']], autopct='%1.1f%%', startangle=90)
            plt.title(chart_config['title'], fontsize=16, fontweight='bold')
            plt.axis('equal') # S'assure que le graphique en secteurs est un cercle
        
        else:
            print("Type de graphique non pris en charge.")
            return None

        # Amélioration : Formater l'axe Y pour une meilleure lisibilité pour les graphiques à barres et linéaires
        if chart_config['chart_type'] in ['bar', 'line']:
            def y_formatter(y, pos):
                # Formate les valeurs en millions avec " M" ou en milliers avec " K"
                if y >= 1e6:
                    return f'{y*1e-6:.1f} M\u20AC'
                elif y >= 1e3:
                    return f'{y*1e-3:.1f} K\u20AC'
                return f'{y:.0f}'

            plt.gca().yaxis.set_major_formatter(FuncFormatter(y_formatter))

        plt.title(chart_config['title'], fontsize=16, fontweight='bold')
        if chart_config['chart_type'] in ['bar', 'line']:
            plt.xlabel(chart_config['x_label'], fontsize=12)
            plt.ylabel(chart_config['y_label'], fontsize=12)
        plt.tight_layout()

        # Enregistrer le graphique
        file_path = "chart.png"
        plt.savefig(file_path)
        plt.close()

        # Ajouter le code pour ouvrir automatiquement le fichier image
        print(f"Graphique généré : {file_path}")
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # linux
                subprocess.call(('xdg-open', file_path))
        except FileNotFoundError:
            print(f"Impossible d'ouvrir le fichier {file_path}. Veuillez le faire manuellement.")
        
        return file_path
    
    except Exception as e:
        print(f"Erreur lors de la création du graphique : {e}")
        return None
