import dimcli
import pandas as pd

from datetime import date
import os

# Housekeeping
HOME_DIR: str = os.getcwd()
DATA_DIR: str = os.path.join(HOME_DIR, 'data')

GRIDID: str = 'grid.6268.a'
MIN_YEAR: int =2014
MAX_YEAR: int = 2024
TODAY: str = date.today().strftime('%Y_%m_%d')

# Log into Dimensions using dsl.ini file
dimcli.login()
dsl = dimcli.Dsl()

# Dimensions query
results = dsl.query(f"""search patents where (year in [{MIN_YEAR}:{MAX_YEAR}] and assignees = "{GRIDID}") 
                    return patents[id+title+original_assignees+filing_date+priority_date+publication_date+
                    granted_date+expiration_date+filing_status+legal_status+jurisdiction+times_cited+inventor_names+
                    category_for_2020] limit 1000""")

df_results = results.as_dataframe().rename(columns = {'id':'patent_id'})

# Original assignees
df_original_assignees = (
    df_results
    .filter(['patent_id', 'original_assignees'])
    .explode('original_assignees')
    .reset_index()
)

df_original_assignees = pd.concat([df_original_assignees['patent_id'], pd.json_normalize(df_original_assignees['original_assignees'])], axis = 1)

df_original_assignees = (
    df_original_assignees
    .explode('types')
    .drop(columns=['acronym', 'linkout', 'state_name'])
)

df_original_assignees.to_csv(os.path.join(DATA_DIR, ''.join([TODAY, '_original_assignees.csv'])), index=False)

# details
df_details = df_results.filter(['patent_id', 'title', 'inventor_names'])

df_details['inventor_names'] = (
    df_details['inventor_names']
    .astype(str)
    .str.title().
    apply(lambda x: x.replace('[','').replace(']','').replace("'",'').replace("'",''))    
)

df_details.to_csv(os.path.join(DATA_DIR, ''.join([TODAY, '_details.csv'])), index=False)

# Status
df_status = df_results.filter(['patent_id', 'jurisdiction', 'legal_status', 'filing_status', 'filing_date', 
                               'priority_date', 'publication_date', 'expiration_date', 'granted_date'])
df_status.to_csv(os.path.join(DATA_DIR, "".join([TODAY, '_status.csv'])), index=False)

# FoR 2020
df_for_2020 = (
    df_results
    .filter(['id', 'category_for_2020'])
    .explode('category_for_2020')
    .reset_index()
)

df_for_2020 = pd.concat([df_for_2020['patent_id'], pd.json_normalize(df_for_2020['category_for_2020'])], axis = 1)

df_for_2020 = (
    df_for_2020
    .assign(
        for_2020_code = lambda df: df['name'].str.split(pat=' ', n=1, expand=True)[0],
        for_2020_name = lambda df: df['name'].str.split(pat=' ', n=1, expand=True)[1]
    )
    .drop(['name', 'id'], axis=1)
)

df_for_2020.to_csv(os.path.join(DATA_DIR, ''.join([TODAY, '_for_2020.csv'])), index=False)

# Citations
df_citations = df_results.filter(['patent_id', 'times_cited'])
df_citations.to_csv(os.path.join(DATA_DIR, ''.join([TODAY, '_times_cited.csv'])), index=False)

# Finished!
print('Data collection completed.')
