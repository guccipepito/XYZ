import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Fonction pour créer un fichier Excel modèle
def generate_empty_template():
    # Noms des colonnes attendues dans l'application
    columns = [
        "Date", "Calories Entraînement", "Temps Entraînement",
        "Calories journalières", "Calories Consommées",
        "Proteines consommées", "Glucides consommées",
        "Lipides consommées", "Déficit Calorique"
    ]
    
    # Crée un DataFrame vide avec les colonnes nécessaires
    empty_df = pd.DataFrame(columns=columns)
    
    # Sauvegarde dans un buffer mémoire pour téléchargement
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        empty_df.to_excel(writer, index=False, sheet_name="Modèle")
    
    buffer.seek(0)
    return buffer

# Configuration de la page
st.set_page_config(
    page_title="FitTrack App",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ajout dans le menu pour le téléchargement
with st.sidebar:
    st.subheader("📥 Télécharger un Modèle Excel")
    st.markdown(
        "Téléchargez un fichier Excel modèle contenant les colonnes nécessaires pour soumettre vos données."
    )
    
    # Génération et téléchargement du fichier
    template_file = generate_empty_template()
    st.download_button(
        label="Télécharger le modèle",
        data=template_file,
        file_name="modele_donnees.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Barre latérale
st.sidebar.title("📊 Tableau de Bord")
st.sidebar.info("Téléversez vos données pour commencer.")
uploaded_file = st.sidebar.file_uploader("Téléversez le fichier Excel", type=["xlsx", "xls"])
# Ajout d'un champ pour définir le poids cible
st.sidebar.subheader("🔧 Ajustez vos paramètres")
poids_cible = st.sidebar.number_input("Entrez votre poids cible (kg)", min_value=0.0, value=70.0, step=0.5)


# Tableau de bord
st.title("FitTrack App")

if uploaded_file:
    try:
        # Lecture du fichier Excel
        data = pd.read_excel(uploaded_file)

        # Pré-traitement des données
        data = data[["Date", "Calories Entraînement", "Temps Entraînement", "Calories journalières", 
                     "Calories Consommées", "Proteines consommées", "Glucides consommées", "Lipides consommées"]]

        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        for col in ["Calories Entraînement", "Temps Entraînement", "Calories journalières", 
                    "Calories Consommées", "Proteines consommées", "Glucides consommées", "Lipides consommées"]:
            data[col] = data[col].replace({",": ".", "\xa0": ""}, regex=True).astype(float)

        data = data.dropna()

        # Calculs supplémentaires
        data["Moyenne Mobile 7 Jours"] = data["Calories journalières"].rolling(window=7).mean()
        data["Déficit Calorique"] = data["Calories journalières"] - data["Calories Consommées"]

        # Calcul du déficit calorique total
        total_deficit = data["Déficit Calorique"].sum()

        # Calcul du poids perdu en fonction du déficit calorique
        poids_perdu_lbs = total_deficit / 3500  # 3500 kcal = 1 lb
        poids_perdu_kg = poids_perdu_lbs * 0.453592  # Conversion lbs en kg

        # Ajout dans le tableau de bord principal
        st.markdown("### 💡 Poids Potentiellement Perdu")
        col1, col2 = st.columns(2)

        col1.metric("Poids Perdu (lbs)", f"{poids_perdu_lbs:.2f} lbs")
        col2.metric("Poids Perdu (kg)", f"{poids_perdu_kg:.2f} kg")

        # Mise à jour des données affichées dans le tableau
        data["Poids Perdu (lbs)"] = total_deficit / 3500
        data["Poids Perdu (kg)"] = data["Poids Perdu (lbs)"] * 0.453592

        # Structure des onglets
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Données", "📈 Visualisations", "💪 Analyse Avancée", "🔧 Ajustements"])

        # Onglet 1 : Données enrichies
        with tab1:

            # Affichage des métriques résumées
            st.markdown("### 🏆 Aperçu Résumé")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Total Calories Brûlées", f"{data['Calories Entraînement'].sum():,.0f} kcal")
            col2.metric("Temps Total d’Entraînement", f"{data['Temps Entraînement'].sum():,.0f} minutes")
            col3.metric("Déficit Moyen", f"{data['Déficit Calorique'].mean():,.1f} kcal")
            col4.metric("Max Calories Journalières", f"{data['Calories journalières'].max():,.0f} kcal")
            
            st.subheader("📋 Aperçu et Statistiques des Données")
            
            # Affichage des données sous forme de tableau
            st.dataframe(data, use_container_width=True)
            
            # Calculs statistiques descriptifs
            st.markdown("### 🧮 Statistiques Clés")
            
            stats = {
                "Colonnes": [
                    "Calories Entraînement", "Temps Entraînement", "Calories journalières",
                    "Calories Consommées", "Proteines consommées", "Glucides consommées", 
                    "Lipides consommées", "Déficit Calorique"
                ]
            }
            
            stats["Moyenne"] = [data[col].mean() for col in stats["Colonnes"]]
            stats["Médiane"] = [data[col].median() for col in stats["Colonnes"]]
            stats["Écart-Type"] = [data[col].std() for col in stats["Colonnes"]]
            stats["Valeur Max"] = [data[col].max() for col in stats["Colonnes"]]
            stats["Valeur Min"] = [data[col].min() for col in stats["Colonnes"]]
            
            # Conversion des statistiques en DataFrame
            stats_df = pd.DataFrame(stats)
            st.dataframe(stats_df, use_container_width=True)

            
            # Analyses complémentaires
            st.markdown("### 🔍 Points Intéressants")
            
            col5, col6 = st.columns(2)
            
            with col5:
                st.write("**Top 5 Jours avec le Plus Grand Déficit Calorique :**")
                top_deficit_days = data.nlargest(5, "Déficit Calorique")[["Date", "Déficit Calorique"]]
                st.dataframe(top_deficit_days)
                
            with col6:
                st.write("**Top 5 Jours avec le Plus Petit Déficit Calorique :**")
                low_deficit_days = data.nsmallest(5, "Déficit Calorique")[["Date", "Déficit Calorique"]]
                st.dataframe(low_deficit_days)
            
            # Distribution des variables principales
            st.markdown("### 📊 Distribution des Données")
            col7, col8 = st.columns(2)
            
            with col7:
                fig10 = px.histogram(data, x="Calories journalières", nbins=30, 
                                    title="Distribution des Calories Journalières",
                                    labels={"Calories journalières": "Calories (kcal)"})
                st.plotly_chart(fig10, use_container_width=True)
            
            with col8:
                fig11 = px.box(data, y="Déficit Calorique", 
                            title="Distribution du Déficit Calorique",
                            labels={"Déficit Calorique": "Déficit (kcal)"})
                st.plotly_chart(fig11, use_container_width=True)
            
            # Ajout d'une analyse de tendance
            st.markdown("### 📈 Analyse des Tendances")
            
            fig_trend = px.line(data, x="Date", y=["Calories journalières", "Calories Consommées"],
                                title="Tendance des Calories : Consommées vs Journalières",
                                labels={"Date": "Date", "value": "Calories (kcal)"})
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # Onglet 2 : Visualisations
        with tab2:
        
            st.subheader("📈 Visualisations")
            col1, col2 = st.columns(2)

            # Graphiques existants
            with col1:
                fig1 = px.scatter(data, x="Temps Entraînement", y="Calories Entraînement",
                                title="Calories brûlées vs Temps d'entraînement",
                                labels={"Temps Entraînement": "Temps (minutes)", "Calories Entraînement": "Calories brûlées"})
                st.plotly_chart(fig1, use_container_width=True)

                fig2 = px.line(data, x="Date", y="Déficit Calorique",
                            title="Évolution du Déficit Calorique",
                            labels={"Date": "Date", "Déficit Calorique": "Déficit (kcal)"})
                st.plotly_chart(fig2, use_container_width=True)

            with col2:
                fig3 = px.line(data, x="Date", y=["Calories journalières", "Moyenne Mobile 7 Jours"],
                            title="Calories Journalières vs Moyenne Mobile",
                            labels={"Date": "Date", "value": "Calories (kcal)"})
                st.plotly_chart(fig3, use_container_width=True)

                fig4 = px.pie(names=["Protéines", "Glucides", "Lipides"],
                            values=[data["Proteines consommées"].mean(),
                                    data["Glucides consommées"].mean(),
                                    data["Lipides consommées"].mean()],
                            title="Répartition Moyenne des Macronutriments")
                st.plotly_chart(fig4, use_container_width=True)

            # Nouveaux graphiques
            st.markdown("### 📊 Graphiques supplémentaires")

            col3, col4 = st.columns(2)

            with col3:
                # Graphique 5 : Histogramme des calories consommées
                fig5 = px.histogram(data, x="Calories Consommées", nbins=20,
                                    title="Répartition des Calories Consommées",
                                    labels={"Calories Consommées": "Calories (kcal)"})
                st.plotly_chart(fig5, use_container_width=True)

                # Graphique 6 : Boxplot des macronutriments
                fig6 = px.box(data, y=["Proteines consommées", "Glucides consommées", "Lipides consommées"],
                            title="Distribution des Macronutriments",
                            labels={"value": "Valeur (g)", "variable": "Macronutriment"})
                st.plotly_chart(fig6, use_container_width=True)

            with col4:
                # Graphique 7 : Évolution des protéines consommées
                fig7 = px.line(data, x="Date", y="Proteines consommées",
                            title="Évolution des Protéines Consommées",
                            labels={"Date": "Date", "Proteines consommées": "Protéines (g)"})
                st.plotly_chart(fig7, use_container_width=True)

                # Graphique 8 : Proportions des macronutriments par jour
                fig8 = px.area(data, x="Date", y=["Proteines consommées", "Glucides consommées", "Lipides consommées"],
                            title="Évolution des Macronutriments Consommés",
                            labels={"Date": "Date", "value": "Valeur (g)"})
                st.plotly_chart(fig8, use_container_width=True)

            # Graphique 9 : Calories entraînement vs déficit calorique
            fig9 = px.scatter(data, x="Calories Entraînement", y="Déficit Calorique",
                            title="Relation entre Calories brûlées et Déficit Calorique",
                            labels={"Calories Entraînement": "Calories brûlées", "Déficit Calorique": "Déficit (kcal)"},
                            trendline="ols")
            st.plotly_chart(fig9, use_container_width=True)

            fig1 = px.line(data, x="Date", y="Déficit Calorique",
                       title="Évolution du Déficit Calorique",
                       labels={"Date": "Date", "Déficit Calorique": "Déficit (kcal)"})
            # Ajout de la ligne représentant le poids cible
            fig1.add_hline(y=poids_cible, line_dash="dot", line_color="red", annotation_text="Poids cible (kg)")
            st.plotly_chart(fig1, use_container_width=True)

            # Graphique 2 : Calories journalières vs consommées avec poids cible
            fig2 = px.line(data, x="Date", y=["Calories journalières", "Calories Consommées"],
                        title="Tendance des Calories : Journalières vs Consommées",
                        labels={"value": "Calories (kcal)", "variable": "Type"})
            # Ajout de la ligne représentant le poids cible
            fig2.add_hline(y=poids_cible, line_dash="dot", line_color="red", annotation_text="Poids cible (kg)")
            st.plotly_chart(fig2, use_container_width=True)

            # Graphique 3 : Répartition des macronutriments
            fig3 = px.area(data, x="Date", y=["Proteines consommées", "Glucides consommées", "Lipides consommées"],
                        title="Évolution des Macronutriments Consommés",
                        labels={"value": "Quantité (g)", "variable": "Macronutriment"})
            st.plotly_chart(fig3, use_container_width=True)

            # Résumé
            st.subheader("💡 Résumé")
            st.metric("Poids potentiellement perdu (kg)", f"{poids_perdu_kg:.2f} kg")
            st.metric("Poids cible", f"{poids_cible:.2f} kg")
        ####
        # Onglet 3 : Analyse Avancée
        with tab3:
            
            st.markdown("### Corrélations et Analyse")
            corr_matrix = data[["Calories Entraînement", "Temps Entraînement", "Calories journalières", "Déficit Calorique"]].corr()
            #st.dataframe(corr_matrix)

            fig_corr = px.imshow(corr_matrix, text_auto=True, title="Matrice de Corrélation")
            st.plotly_chart(fig_corr, use_container_width=True)

            st.markdown("### Répartition des Déficits")
            fig_hist = px.histogram(data, x="Déficit Calorique", nbins=20, title="Histogramme des Déficits Caloriques")
            st.plotly_chart(fig_hist, use_container_width=True)

        # Onglet 4 : Ajustements
        with tab4:
            st.subheader("🔧 Ajustement Nutritionnel")
            program_type = st.radio("Choisissez un objectif nutritionnel :", ["Bulk", "Cut"])

            if program_type == "Bulk":
                st.markdown("""
                **Programme Bulk :**
                - Augmentez l'apport calorique global pour favoriser la prise de masse.
                - Priorisez les repas riches en protéines et glucides.
                """)
            else:
                st.markdown("""
                **Programme Cut :**
                - Réduisez l'apport calorique global pour perdre de la masse graisseuse.
                - Maintenez un apport élevé en protéines pour préserver la masse musculaire.
                """)

            st.subheader("🏋️ Programme d’Entraînement")
            training_goal = st.selectbox("Objectif d'entraînement :", ["Force", "Endurance", "Hypertrophie"])

            # Génération du programme
            def generate_training_program(goal):
                program = {
                    "Lundi": ["Pectoraux", "Triceps"],
                    "Mardi": ["Dos", "Biceps"],
                    "Mercredi": ["Jambes", "Mollets"],
                    "Jeudi": ["Épaules", "Trapèzes"],
                    "Vendredi": ["Cardio"],
                }
                st.write(f"### Programme {goal} :")
                for day, activities in program.items():
                    st.write(f"**{day} :** {', '.join(activities)}")

            generate_training_program(training_goal)

    except Exception as e:
        st.error(f"Erreur lors de l'importation des données : {e}")

else:
    st.info("📤 Téléversez vos données pour visualiser votre tableau de bord.")