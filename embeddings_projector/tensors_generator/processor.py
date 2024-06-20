import pandas as pd
import numpy as np
import ast
import os
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
