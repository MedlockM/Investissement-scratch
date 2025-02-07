import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

# =====================================
# Fonctions métier
# =====================================
def compound_growth(principal, monthly_rate, months=1):
    """
    Croissance composée d'un capital 'principal' sur 'months' mois
    au taux mensuel 'monthly_rate'.
    """
    return principal * (1 + monthly_rate) ** months

def annual_rate2mensual_rate(annual_rate):
    """
    Convertit un taux annuel en taux mensuel moyen.
    """
    return (1 + annual_rate) ** (1/12) - 1

def monthly_repayment(principal, annual_interest_rate, years):
    """
    Calcule la mensualité standard (annuité) pour un emprunt.
    """
    monthly_interest_rate = annual_rate2mensual_rate(annual_interest_rate)
    n_months = int(years * 12)

    if n_months == 0:
        return 0.0
    if monthly_interest_rate == 0:
        return principal / n_months

    numerator = monthly_interest_rate * (1 + monthly_interest_rate) ** n_months
    denominator = (1 + monthly_interest_rate) ** n_months - 1

    return principal * (numerator / denominator)


def simulate_multi_cycle_strategy_detailed(strategy_cycles, annual_investment_rate,
                                           start_age):
    """
    Variante détaillée qui enregistre chaque année :
      - Age (en fin d'année)
      - out_of_pocket_year : argent sorti de la poche (remboursement + contributions)
      - roi_year : gains effectifs de l'investissement sur l'année
      - net_gains : le net_gains cumulé (comme avant)

    Retourne :
      ages, net_gains_annual, final_portfolio, final_net_gains, annual_details

    Où :
      annual_details est une liste de dict, chaque dict contenant :
        {
          "year_index": i (0, 1, 2, ...)
          "age_end": int
          "portfolio_before": float
          "out_of_pocket_year": float
          "portfolio_after": float
          "roi_year": float
          "delta_year": float  (roi_year - out_of_pocket_year)
          "net_gains_end_of_year": float  (portefeuille - argent total injecté)
        }
    """
    monthly_investment_rate = annual_rate2mensual_rate(annual_investment_rate)

    total_portfolio = 0.0
    total_external_investment = 0.0
    current_age = start_age

    ages = []
    net_gains_annual = []

    annual_details = []  # on va remplir cette liste année par année

    # On va parcourir chaque cycle
    for cycle in strategy_cycles:
        loan_amount = cycle['loan_amount']
        loan_interest_rate = cycle['loan_interest_rate']
        loan_repayment_years = cycle['loan_repayment_years']
        monthly_contribution = cycle['monthly_contribution']
        contribution_years = cycle['contribution_years']
        m_repayment = cycle['m_repayment']

        # On investit immédiatement le montant emprunté (le cas échéant)
        total_portfolio += loan_amount

        # Durée du cycle = la plus longue des deux périodes
        cycle_length_years = max(loan_repayment_years, contribution_years)

        for year_index in range(cycle_length_years):
            # En début d'année, on enregistre la valeur du portefeuille
            portfolio_before = total_portfolio
            out_of_pocket_year = 0.0

            # 12 mois dans l'année
            for _ in range(12):
                # Remboursement mensuel
                if year_index < loan_repayment_years:
                    out_of_pocket_year += m_repayment

                # Contribution mensuelle
                if year_index < contribution_years:
                    out_of_pocket_year += monthly_contribution
                    total_portfolio += monthly_contribution

                # Croissance mensuelle
                total_portfolio = compound_growth(total_portfolio,
                                                  monthly_investment_rate, 1)

            # Fin d'année => on met à jour "total_external_investment"
            # (car c'est de l'argent qui sort de la poche au total)
            total_external_investment += out_of_pocket_year

            portfolio_after = total_portfolio

            # Gains réels de l'investissement pour l'année
            roi_year = (portfolio_after - portfolio_before) - out_of_pocket_year

            # Gains nets cumulés en fin d'année
            net_gains_end_of_year = total_portfolio - total_external_investment

            # On incrémente l'âge
            current_age += 1
            ages.append(current_age)
            net_gains_annual.append(net_gains_end_of_year)

            # On stocke un petit résumé pour l'année
            annual_details.append({
                "year_index": len(ages),  # ou year_index+1
                "age_end": current_age,
                "portfolio_before": portfolio_before,
                "out_of_pocket_year": out_of_pocket_year,
                "portfolio_after": portfolio_after,
                "roi_year": roi_year,
                "delta_year": roi_year - out_of_pocket_year,
                "net_gains_end_of_year": net_gains_end_of_year
            })

    final_portfolio = total_portfolio
    final_net_gains = final_portfolio - total_external_investment

    return ages, net_gains_annual, final_portfolio, final_net_gains, annual_details


# =====================================
# Application Streamlit
# =====================================

st.title("Comparaison de deux scénarios d'investissement & emprunt")

# -- Stockage de l'état dans st.session_state
if "scenario1_cycles" not in st.session_state:
    st.session_state.scenario1_cycles = []
if "scenario2_cycles" not in st.session_state:
    st.session_state.scenario2_cycles = []

# Info sur le cycle en cours d'édition : {'scenario': 1 ou 2, 'index': i}
if "edit_cycle_info" not in st.session_state:
    st.session_state.edit_cycle_info = None

# ==========================================
# CASE À COCHER : LUMP SUM vs DCA
# ==========================================
lumpsum_vs_dca = st.sidebar.checkbox("Lump Sum vs. DCA?")

# =====================================================
# Saisie des paramètres globaux : taux d'investissement
# et âge de départ pour les deux scénarios
# =====================================================
st.sidebar.header("Paramètres globaux")

col1, col2 = st.sidebar.columns(2)
with col1:
    annual_investment_rate_s1 = st.number_input(
        "Taux annuel d'investissement (Scénario 1)",
        min_value=0.0, max_value=1.0, value=0.08, step=0.01
    )
    start_age_s1 = st.number_input(
        "Âge de départ (Scénario 1)",
        min_value=0, max_value=100, value=30, step=1
    )

with col2:
    annual_investment_rate_s2 = st.number_input(
        "Taux annuel d'investissement (Scénario 2)",
        min_value=0.0, max_value=1.0, value=0.08, step=0.01
    )
    start_age_s2 = st.number_input(
        "Âge de départ (Scénario 2)",
        min_value=0, max_value=100, value=30, step=1
    )

# ==========================================
# FONCTIONS UTILITAIRES GESTION DES CYCLES
# ==========================================
def add_cycle(
    scenario_cycles,
    loan_amount,
    loan_interest_rate,
    loan_repayment_years,
    monthly_contribution,
    contribution_years
):
    m_repay = monthly_repayment(loan_amount, loan_interest_rate, loan_repayment_years)
    cycle_dict = {
        "loan_amount": loan_amount,
        "loan_interest_rate": loan_interest_rate,
        "loan_repayment_years": loan_repayment_years,
        "monthly_contribution": monthly_contribution,
        "contribution_years": contribution_years,
        "m_repayment": m_repay,
    }
    scenario_cycles.append(cycle_dict)

def update_cycle(
    scenario_cycles,
    index,
    loan_amount,
    loan_interest_rate,
    loan_repayment_years,
    monthly_contribution,
    contribution_years
):
    m_repay = monthly_repayment(loan_amount, loan_interest_rate, loan_repayment_years)
    scenario_cycles[index] = {
        "loan_amount": loan_amount,
        "loan_interest_rate": loan_interest_rate,
        "loan_repayment_years": loan_repayment_years,
        "monthly_contribution": monthly_contribution,
        "contribution_years": contribution_years,
        "m_repayment": m_repay,
    }

def display_cycles(scenario_number):
    """
    Affiche la liste des cycles pour le scénario demandé,
    avec possibilités de Modifier / Supprimer (si autorisé).
    """
    if scenario_number == 1:
        scenario_cycles = st.session_state.scenario1_cycles
        label = "Scénario 1"
    else:
        scenario_cycles = st.session_state.scenario2_cycles
        label = "Scénario 2"

    if scenario_cycles:
        st.write(f"**Cycles du {label} :**")
        for i, c in enumerate(scenario_cycles):
            with st.expander(f"Cycle #{i+1}", expanded=False):
                st.write(c)

                # Si lumpsum_vs_dca est coché et qu'on est sur le Scénario 2,
                # on n'autorise pas la modif/suppression (car c'est auto-généré).
                if lumpsum_vs_dca and scenario_number == 2:
                    st.info("Cycle généré automatiquement (DCA).")
                else:
                    # Sinon, on permet la modif/suppression
                    col1, col2 = st.columns(2)
                    # Bouton "Modifier"
                    if col1.button(f"Modifier cycle #{i+1} ({label})", key=f"edit_{label}_{i}"):
                        st.session_state.edit_cycle_info = {
                            "scenario": scenario_number,
                            "index": i
                        }
                        st.rerun()

                    # Bouton "Supprimer"
                    if col2.button(f"Supprimer cycle #{i+1} ({label})", key=f"delete_{label}_{i}"):
                        scenario_cycles.pop(i)
                        st.rerun()
    else:
        st.write(f"Aucun cycle pour le {label} pour le moment.")

def cycle_form(scenario_number):
    """
    Affiche un formulaire pour Ajouter/Modifier un cycle
    dans le scénario 'scenario_number'.
    """
    if scenario_number == 1:
        scenario_cycles = st.session_state.scenario1_cycles
        label = "Scénario 1"
    else:
        scenario_cycles = st.session_state.scenario2_cycles
        label = "Scénario 2"

    # Vérifie si on est en mode édition pour ce scénario
    is_edit_mode = (
        st.session_state.edit_cycle_info is not None
        and st.session_state.edit_cycle_info["scenario"] == scenario_number
    )

    # Clé "générale" pour différencier "nouveau cycle" vs. "édition de cycle"
    if is_edit_mode:
        index_to_edit = st.session_state.edit_cycle_info["index"]
        cycle_data = scenario_cycles[index_to_edit]

        title = f"Modifier le cycle #{index_to_edit+1} du {label}"

        default_loan_amount = cycle_data["loan_amount"]
        default_loan_interest_rate = cycle_data["loan_interest_rate"]
        default_loan_repayment_years = cycle_data["loan_repayment_years"]
        default_monthly_contribution = cycle_data["monthly_contribution"]
        default_contribution_years = cycle_data["contribution_years"]

        # Pour éviter que Streamlit réutilise les mêmes clés d'input
        form_key_prefix = f"edit_{label}_{index_to_edit}"
    else:
        title = f"Nouveau cycle {label}"
        default_loan_amount = 100_000.0
        default_loan_interest_rate = 0.06
        default_loan_repayment_years = 20
        default_monthly_contribution = 500.0
        default_contribution_years = 20

        form_key_prefix = f"new_{label}"

    # Si c'est le scénario 2 et lumpsum_vs_dca est coché,
    # on désactive ce formulaire d'ajout (puisque c'est automatique).
    if lumpsum_vs_dca and scenario_number == 2:
        return  # on n'affiche pas le formulaire

    with st.expander(title, expanded=False):
        loan_amount = st.number_input(
            "Montant du prêt",
            min_value=0.0,
            value=default_loan_amount,
            step=5_000.0,
            key=f"loan_amount_{form_key_prefix}"
        )
        loan_interest_rate = st.number_input(
            "Taux annuel du prêt (0.06 = 6%)",
            min_value=0.0,
            max_value=1.0,
            value=default_loan_interest_rate,
            step=0.01,
            key=f"loan_interest_rate_{form_key_prefix}"
        )
        loan_repayment_years = st.number_input(
            "Durée de remboursement (années)",
            min_value=0,
            max_value=40,
            value=default_loan_repayment_years,
            key=f"loan_repayment_years_{form_key_prefix}"
        )
        monthly_contribution = st.number_input(
            "Contribution mensuelle",
            min_value=0.0,
            value=default_monthly_contribution,
            step=100.0,
            key=f"monthly_contribution_{form_key_prefix}"
        )
        contribution_years = st.number_input(
            "Durée de contribution (années)",
            min_value=0,
            max_value=40,
            value=default_contribution_years,
            key=f"contribution_years_{form_key_prefix}"
        )

        # Bouton de validation
        if is_edit_mode:
            if st.button(f"Valider la modification du cycle #{index_to_edit+1}"):
                update_cycle(
                    scenario_cycles,
                    index_to_edit,
                    loan_amount,
                    loan_interest_rate,
                    loan_repayment_years,
                    monthly_contribution,
                    contribution_years
                )
                st.success(f"Cycle #{index_to_edit+1} modifié avec succès !")
                # Quitter le mode édition
                st.session_state.edit_cycle_info = None
                st.rerun()
        else:
            # Mode "ajout"
            if st.button(f"Ajouter ce cycle au {label}"):
                add_cycle(
                    scenario_cycles,
                    loan_amount,
                    loan_interest_rate,
                    loan_repayment_years,
                    monthly_contribution,
                    contribution_years
                )
                st.success(f"Cycle ajouté au {label} !")
                st.rerun()

# ==========================================
# GÉNÉRER AUTOMATIQUEMENT LE SCÉNARIO 2 (DCA)
# À PARTIR DU SCÉNARIO 1 (LUMP SUM)
# ==========================================
def build_dca_cycles_from_lumpsum():
    """
    Pour chaque cycle du Scénario 1, on crée un "cycle miroir" DCA dans le Scénario 2 :
      - Même durée totale = max(loan_repayment_years, contribution_years) (Scénario 1)
      - loan_amount = 0, loan_interest_rate = 0, loan_repayment_years = 0
      - monthly_contribution = m_repayment (du cycle 1)
      - contribution_years = même durée
      - m_repayment = 0 (car pas de prêt)
    """
    st.session_state.scenario2_cycles = []  # on réinitialise

    for c in st.session_state.scenario1_cycles:
        cycle_length_years = max(c["loan_repayment_years"], c["contribution_years"])
        dca_cycle = {
            "loan_amount": 0,
            "loan_interest_rate": 0,
            "loan_repayment_years": 0,
            "monthly_contribution": c["m_repayment"],  # on investit la mensualité du prêt
            "contribution_years": cycle_length_years,
            "m_repayment": 0,  # pas de remboursement car pas de prêt
        }
        st.session_state.scenario2_cycles.append(dca_cycle)

# ==========================================
# SECTION : SCÉNARIO 1 (toujours éditable)
# ==========================================
st.header("Scénario 1 : Configuration des cycles")
cycle_form(scenario_number=1)
display_cycles(scenario_number=1)

# ==========================================
# SECTION : SCÉNARIO 2
# ==========================================
st.header("Scénario 2 : Configuration des cycles")

if lumpsum_vs_dca:
    st.info("Ce scénario (DCA) est automatiquement généré à partir du Scénario 1.")
    build_dca_cycles_from_lumpsum()
    display_cycles(scenario_number=2)
else:
    cycle_form(scenario_number=2)
    display_cycles(scenario_number=2)

# =====================================================
# Lancement de la simulation et affichage des résultats
# =====================================================
st.subheader("Lancer la comparaison")

if st.button("Simuler les deux scénarios"):
    # --- SIMULATION SCÉNARIO 1 ---
    if st.session_state.scenario1_cycles:
        (
            ages_s1,
            net_gains_s1,
            final_portfolio_s1,
            final_net_gains_s1,
            annual_details_s1
        ) = simulate_multi_cycle_strategy_detailed(
            st.session_state.scenario1_cycles,
            annual_investment_rate_s1,
            start_age_s1
        )

    else:
        ages_s1, net_gains_s1 = [], []
        final_portfolio_s1, final_net_gains_s1 = 0.0, 0.0

    # --- SIMULATION SCÉNARIO 2 ---
    if st.session_state.scenario2_cycles:
        (
            ages_s2,
            net_gains_s2,
            final_portfolio_s2,
            final_net_gains_s2,
            annual_details_s2
        ) = simulate_multi_cycle_strategy_detailed(
            st.session_state.scenario2_cycles,
            annual_investment_rate_s2,
            start_age_s2
        )
    else:
        ages_s2, net_gains_s2 = [], []
        final_portfolio_s2, final_net_gains_s2 = 0.0, 0.0

    # =====================================================
    # AFFICHAGE GRAPHIQUE DES GAINS NETS
    # =====================================================
    fig, ax = plt.subplots(figsize=(8, 4))

    if ages_s1:
        ax.plot(ages_s1, net_gains_s1, label="Scénario 1 (Lump Sum)", marker='o')
    if ages_s2:
        ax.plot(ages_s2, net_gains_s2, label="Scénario 2 (DCA)", marker='o')

    ax.set_xlabel("Âge")
    ax.set_ylabel("Gains nets (en €)")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # =====================================================
    # TABLEAU RÉCAPITULATIF
    # =====================================================
    s1_injected = round(final_portfolio_s1 - final_net_gains_s1, 2)
    s2_injected = round(final_portfolio_s2 - final_net_gains_s2, 2)

    results = {
        "Scénario": ["Scénario 1", "Scénario 2"],
        "Valeur finale Portefeuille (€)": [
            round(final_portfolio_s1, 2),
            round(final_portfolio_s2, 2)
        ],
        "Total injecté (€)": [s1_injected, s2_injected],
        "Gains nets (€)": [
            round(final_net_gains_s1, 2),
            round(final_net_gains_s2, 2)
        ]
    }

    st.write("### Résultats Finaux")
    st.table(results)

    # Tables for annual details
    df_s1 = pd.DataFrame(annual_details_s1)
    st.write("**Détails annuels – Scénario 1**")
    st.dataframe(df_s1)

    df_s2 = pd.DataFrame(annual_details_s2)
    st.write("**Détails annuels – Scénario 2**")
    st.dataframe(df_s2)

