import ast
import os

import numpy as np
import pandas as pd

short_coem_numbers = pd.read_excel('embeddings_total.xlsx')
short_coem_metadata =  pd.read_excel('coem_authors_enriched.xlsx')
shorc_metadata = pd.read_excel('coem_cuentos_authors.xlsx')
Totals_df1 = pd.merge(short_coem_numbers, shorc_metadata, left_on="vector_id" ,right_on='uuid_story', how='left')
Totals_df1=Totals_df1[["vector_id","values","author_uuid","story_name","reading_time_min"]].copy()
Totals_df = pd.merge(Totals_df1, short_coem_metadata, left_on="author_uuid" ,right_on='UUID', how='left')
Totals_df=Totals_df[['vector_id', 'values', 'story_name', 'reading_time_min',
       'Author', 'LastName', 'Name', 'country', 'genera',
        'Wiki_URL', 'cats', 'linked_authors','Birth Year', 'Death Year']].copy()#'Summary'
Totals_df_labels = Totals_df.drop(Totals_df.columns[:2], axis=1)
Totals_df_labels = Totals_df_labels.replace('\t', '', regex=True)
Totals_df_labels = Totals_df_labels.replace('\n', '', regex=True)
Totals_df_labels = Totals_df_labels.replace('ñ', 'n', regex=True)
Totals_df_labels = Totals_df_labels.replace('ñ', 'n', regex=True)


non_numeric_mapping_death = {
    '1863 y 1786': 1863,  # Assuming you want to take the first year
    'c.1400': 1400,
    '1976 (desaparecido)': 1976,
    'nan':np.nan
}

# Replace known non-numeric values using the mapping
Totals_df_labels['Death Year'].replace(non_numeric_mapping_death,inplace=True)

Totals_df_labels['Death Year'] = pd.to_numeric(Totals_df_labels['Death Year'], errors='coerce')
# Convert all values to numeric, setting errors='coerce' will convert non-numeric values to NaN
country_mapping = {
    'Estadounidense': "Estados Unidos",  # Assuming you want to take the first year
    'Inglesa': "Inglaterra",
    'Argentino': "Argentina",
    'nan':np.nan,
    "Cubano":"Cuba",
    "Puertorriqueno": "Puerto Rico",
    "Nueva Zelandia": "Nueva Zelanda"
}

# Replace known non-numeric values using the mapping
Totals_df_labels['country'].replace(country_mapping,inplace=True)

non_numeric_mapping_birth = {
    'Siglo VI AC': -600,   # 6th century BC
    'Siglo XII': 1200      # 12th century
}

# Replace known non-numeric values using the mapping
Totals_df_labels['Birth Year'].replace(non_numeric_mapping_birth,inplace=True)

Totals_df_labels['Birth Year'] = pd.to_numeric(Totals_df_labels['Birth Year'], errors='coerce')
#FillNAs
Totals_df_labels['Name'] = Totals_df_labels['Name'].fillna("Unknown")
Totals_df_labels['country'] = Totals_df_labels['country'].fillna("Unknown")
Totals_df_labels['genera'] = Totals_df_labels['genera'].fillna("Unknown")
Totals_df_labels['cats'] = Totals_df_labels['cats'].fillna("Unknown")
Totals_df_labels['Wiki_URL'] = Totals_df_labels['Wiki_URL'].fillna("Unknown")
Totals_df_labels['linked_authors'] = Totals_df_labels['linked_authors'].fillna("Unknown")
Totals_df_labels['Birth Year'] = Totals_df_labels['Birth Year'].fillna(0)
Totals_df_labels['Death Year'] = Totals_df_labels['Death Year'].fillna(0)


#rename columns
new_column_names = {
    'story_name': 'Story Name',
    'reading_time_min': 'Reading Time (min)',
    'Author': 'Author First Name',
    'LastName': 'Author Last Name',
    'Name': 'Full Name',
    'country': 'Country',
    'genera': 'Genre',
    'Wiki_URL': 'Wikipedia URL',
    'cats': 'Categories',
    'linked_authors': 'Linked Authors',
    'Birth Year': 'Year of Birth',
    'Death Year': 'Year of Death'
}

# Rename the columns
Totals_df_labels.rename(columns=new_column_names, inplace=True)

##### Saving
directory=os.path.join(os.path.dirname(__file__))
filname= os.path.join(directory, "stories_metadata.tsv")
Totals_df_labels.to_csv(filname, sep='\t', index=False, header=True)
Totals_df_vals=Totals_df.iloc[:, 1:2].copy()
Totals_df_vals['values'] = Totals_df_vals['values'].apply(ast.literal_eval)
array_2d = np.array(Totals_df_vals['values'].tolist())
print(array_2d.shape)
filname= os.path.join(directory, "stories_tensors.bytes")
array_2d.tofile(filname)
Stories_tensors=pd.DataFrame(Totals_df_vals['values'].tolist())
filname=os.path.join(directory, "stories_tensors.tsv")
Stories_tensors.to_csv(filname, sep='\t', index=False, header=False)

#50 is the max Categorical
# Missing fixing the search by Name of the Author or by Country or Death year or Birth year
