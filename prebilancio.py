import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Controlli PreBilancio", layout="centered")

st.title("Maschera Controlli PreBilancio")

tipo_controllo = st.selectbox(
    "Seleziona il tipo di controllo:",
    ["Controllo CG-PIV", "Controllo DUQ"]
)
st.divider()

if tipo_controllo == "Controllo CG-PIV":
    st.subheader("Carica i file per Controllo CG-PIV")
    
    file1 = st.file_uploader("Carica Sit-Dir", type=["xlsx", "csv"])
    file2 = st.file_uploader("Carica Misure-Jarvis", type=["xlsx", "csv"])

    if st.button("Esegui Controllo CG-PIV"):
        if file1 and file2:
            df1 = pd.read_excel(file1, sheet_name="lista", dtype={"mercato": str, "rete": str}) if file1.name.endswith("xlsx") else pd.read_csv(file1)
            df2 = pd.read_excel(file2) if file2.name.endswith("xlsx") else pd.read_csv(file2, sep=";", decimal=",",dtype={"Misuratore": str, "Aggregato": str})

            base_path = os.path.expanduser("~")
            save = os.path.join(base_path,"Snam SpA", "CONES_Bilanci - Documenti", "Check", "PreBilancio")

            #modifica la colonna Sm3aaaamm in Sm3
            df1.rename(
                columns={c: "Sm3" for c in df1.columns if c.startswith("Sm3/")},
                inplace=True
            )
            df1= df1[['mercato', 'bil','Sm3','Energia kwh']]
            df4 = pd.pivot_table(
                    df2,
                    index=["Misuratore"],
                    values=[
                        "Energia",
                        "Volume"
                    ],
                    aggfunc={
                        "Energia": "sum",
                        "Volume": "sum",
                    }
                ).reset_index()
            df4 = pd.merge(df4, df1, left_on="Misuratore", right_on="mercato", how="left")
            df4['Energia Mwh'] = df4['Energia kwh'] / 1000
            df4['Sm3_standard'] = df4['Energia Mwh'] / 0.01057275
            df4['Delta_Energia'] = (df4['Energia Mwh'] - df4['Energia']).round(3)
            df4['Delta_Sm3'] = (df4['Volume'] - df4['Sm3']).round(0)
            
            #potrebbe non servire
            pa = df4[df4['bil'].isin([ "PA"])]
            ma_xg = df4[df4['bil'].isin(["MA", "XG"])]
            #da aggiungere in caso di creazione di nuovi PIv sottesi ai CG
            Piv_Cg = {
                '34695301': ('50161701',),
                '34620301': ('50162001',),
                '34209801': ('50163301',),
                '34614001': ('50176301',),
                '34661501': ('50177201',),
                '34625201': ('50177301',),
                '34628302': ('50177401',),
                '34615801': ('50177501','50177601'),
                '34647101': ('50178701',),
                '34648301': ('50178801','50178901'),
                '34635301': ('50181701',),
                '34854801': ('50193801',),
                '34484701': ('50198001','50239301'),
                '34618801': ('50200701','50239001'),
                '34410901': ('50202701',),
                '34687301': ('50209601',),
                '34497101': ('50245001',),
                '34683401': ('50206601',),
                '34725101': ('50228001',),
                '50122701': ('50227901',),
                '34577001': ('50208901',),
                '34591901': ('50209001',),
                '34203001': ('50202801',),
                '34491901': ('50219301','50219501'),
                '34403711': ('50205401',),
                '34466801': ('50207101',),
                '34496701': ('50267701',),
                '34463701': ('50267301',),
                '34466802': ('50239501',),
                '34485401': ('50271701',),
                '34488301': ('50271401',),
                '34528901': ('50270301',),
                '34588001': ('50252901',),
                '34625303': ('50266701',),
                '34681301': ('50266401',),
                '50029501': ('50271001',),
                '50029502': ('50271002',),
                '50029503': ('50271003',),
                '34252001': ('50225901',),
                '34809201': ('50200601',),
            }
            group_map = {}

            for principale, collegati in Piv_Cg.items():
                group_map[principale] = principale
                for c in collegati:
                    group_map[c] = principale
            
            df4['Gruppo'] = df4['Misuratore'].map(group_map)
            df5 = df4[df4['Gruppo'].notna()]
            df5= df5[['Gruppo','Misuratore', 'Energia','Volume','Sm3', 'Energia Mwh', 'Sm3_standard']]
            cols = df5.select_dtypes(include='number').columns
            df5['Tipo'] = np.where(df5['Gruppo'] == df5['Misuratore'], 'CG', 'Piv')
            totali = (
                df5[df5['Tipo'] == 'Piv']
                .groupby('Gruppo')[cols]
                .sum()
                .reset_index()
            )
            totali['Sm3_Jarvis'] = totali['Energia'] / 0.01057275
            df6 = pd.merge(df5,totali, left_on='Gruppo', right_on='Gruppo', how='left')
            df6 = df6.sort_values(['Gruppo'])
            intestazioni = ['Gruppo', 'CG', 'Energia_Mwh_Jarvis', 'Volume_Jarvis', 'Volume_sitdir', 'Energia_Sitdir', 'Smc38100', 'Tipo','Energia_Mwh_Jarvis_PIV', 'Volume_Jarvis_PIV', 'Volume_sitdir_PIV', 'Energia_Sitdir_PIV', 'Smc38100_PIV', 'Smc38100_Jarvis']
            df6.columns= intestazioni
            totali['Misuratore'] = 'TOTALE PIV'
            totali['Misuratore'] = 'TOTALE PIV'
            df_finale = pd.concat([df5, totali], ignore_index=True)
            df_finale = df_finale.sort_values(['Gruppo','Misuratore'])
            
            df_finale['Smc_Jarvis'] = df_finale['Energia'] / 0.01057275

            df_finale['Sm3_standard'] = df_finale['Sm3_standard'].round(0)
            df_finale['Smc_Jarvis'] = df_finale['Smc_Jarvis'].round(0)
            df_finale['delta'] = df_finale['Sm3_standard'] - df_finale['Smc_Jarvis']

            df_finale.to_csv(os.path.join(save, "Controllo_CG_PIV.csv"), index=False, sep=";", decimal=",")
            df5.to_csv(os.path.join(save, "Controllo_CG_PIV_Dettaglio.csv"), index=False, sep=";", decimal=",")

            st.success(f"Controllo completato. Controlla in cartella {save}")
        else:
            st.warning("Caricare entrambi i file.")

elif tipo_controllo == "Controllo DUQ":
    st.subheader("Carica file per Controllo DUQ")

    file3 = st.file_uploader("Carica file Allocazioni.csv", type=["xlsx", "csv"])

    if st.button("Esegui Controllo DUQ"):
        if file3:
            df = pd.read_excel(file3) if file3.name.endswith("xlsx") else pd.read_csv(file3, sep=";", decimal=",",dtype={"Misuratore": str, "Utente": str, "Macrosettore": str})

            base_path = os.path.expanduser("~")
            save = os.path.join(base_path,"Snam SpA", "CONES_Bilanci - Documenti", "Check", "PreBilancio")

            giorno = (
                        df
                        .groupby(
                            ["Misuratore", "Macrosettore", "Giorno"],
                            as_index=False
                        )
                        .agg({
                            "Allocato Definitivo in Energia": "sum",
                            "Allocato Definitivo in Volume": "sum",
                            "Misura in Energia (MWH)": "mean"
                        })
                    )

            giorno['Duq'] = giorno['Misura in Energia (MWH)'] - giorno['Allocato Definitivo in Energia']
            im_e = giorno[giorno['Macrosettore'].isin(["IM", "E"])]
            #Calcolo il valore soltanto delle importazioni che hanno OBA
            im_valide = ["50169101", "35718301", "35718200", "50020901"]
            im1 = im_e[im_e['Misuratore'].isin(im_valide)]
            im1['Smc1057275'] = im1['Allocato Definitivo in Energia'] / 0.01057275
            pivotimp = pd.pivot_table(im1, index="Giorno", columns="Misuratore", values="Smc1057275", aggfunc="sum", margins=True,margins_name="Totale").reset_index()
            #Calcolo il valore soltanto delle esportazioni che hanno OBA
            exp_valide = ["35718901", "50039801", "50039901", "50181801"]
            exp = im_e[im_e['Misuratore'].isin(exp_valide)]
            exp['Smc1057275'] = exp['Allocato Definitivo in Energia'] / 0.01057275
            pivotexp = pd.pivot_table(exp, index="Giorno", columns="Misuratore", values="Smc1057275", aggfunc="sum", margins=True,margins_name="Totale").reset_index()
            pivotim_e = pd.pivot_table(im_e, index="Giorno", columns="Misuratore", values="Duq", aggfunc="sum").reset_index()
            coppie = {
                '35718200': ('35718200','50039801'),
                '35718301': ('35718301','50039901'),
                '35718901': ('35718901','50020901'),
                '50169101': ('50169101','50181801')  }

            duq = pivotim_e.copy() 

            for origine, (col_pos, col_neg) in coppie.items():  
                duq[origine] = pivotim_e.get(col_pos, 0) - pivotim_e.get(col_neg, 0)
            duqfin= duq[['Giorno', '35718200', '35718301', '35718901', '50169101']]
            # Seleziona le colonne numeriche
            num_cols = ['35718200', '35718301', '35718901', '50169101']  

            duqfin['IMM'] = duqfin[num_cols].where(duqfin[num_cols] > 0).sum(axis=1)
            duqfin['ESP'] = duqfin[num_cols].where(duqfin[num_cols] < 0).sum(axis=1)

            duqfin['IMM'] = duqfin['IMM'].abs()
            duqfin['ESP'] = duqfin['ESP'].abs()

            duqfin.to_csv(os.path.join(save, "Controllo_DUQ.csv"), index=False, sep=";", decimal=",")
            pivotim_e.to_csv(os.path.join(save, "Controllo_DUQ_Dettaglio.csv"), index=False, sep=";", decimal=",")

            st.success(f"Totale numerico: Controllo completato. Controlla in cartella {save}")
        else:
            st.warning("Caricare il file.")