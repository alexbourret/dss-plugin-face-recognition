# -*- coding: utf-8 -*-
import dataiku
import pandas
import face_recognition
import json
import numpy
import uuid
import math

from dataiku.customrecipe import get_input_names_for_role
from dataiku.customrecipe import get_output_names_for_role
from dataiku.customrecipe import get_recipe_config
from plugin_details import get_initialization_string


print("{}".format(get_initialization_string()))

def get_index_of_first_true(booleans):
    # return the index of the first True in a list of booleans
    # or None if none is found
    rank = 0
    for boolean in booleans:
        if boolean==True:
            return rank
        rank +=1
    return None


input_A_names = get_input_names_for_role('input_A_role')
input_A_datasets = [dataiku.Dataset(name) for name in input_A_names]

input_B_names = get_input_names_for_role('input_B_role')
input_B_datasets = [dataiku.Dataset(name) for name in input_B_names]

output_A_names = get_output_names_for_role('main_output')
output_A_datasets = [dataiku.Dataset(name) for name in output_A_names]

config = get_recipe_config()

print("config={}".format(config))
unknowns_to_process = input_A_datasets[0]
unknowns_to_process_dataframe = unknowns_to_process.get_dataframe()
unknown_encodings_column = config.get("unknown_encodings_column")

known_encodings_column = config.get("known_encodings_column")
known_references_column = config.get("known_reference_column", "guid")
if input_B_datasets:
    knowns_dataset = input_B_datasets[0]
    knowns_dataframe = knowns_dataset.get_dataframe()
else:
    knowns_dataframe = pandas.DataFrame()
new_reference_dataset = output_A_datasets[0]
new_reference_dataframe = knowns_dataframe
new_reference_dataframe["error"] = None
if known_references_column not in new_reference_dataframe:
    new_reference_dataframe[known_references_column] = None
print("ALX:starting by writing this:{}".format(new_reference_dataframe))
new_reference_dataset.write_with_schema(new_reference_dataframe)

known_encodings_raw_values = knowns_dataframe.get(known_encodings_column, [])
knowns_encodings = []
for known_encodings_raw_value in known_encodings_raw_values:
    print("ALX:known_encodings_raw_value={}".format(type(known_encodings_raw_value)))
    if isinstance(known_encodings_raw_value, float) and math.isnan(known_encodings_raw_value):
        print("ALX:nan")
        knowns_encodings.append(None)
    else:
        knowns_encodings.append(numpy.array(json.loads(known_encodings_raw_value)))
known_references = list(knowns_dataframe.get(known_references_column))

if not unknown_encodings_column:
    raise Exception("The column containing the unknown encodings must be selected")

output_rows = []

for index, input_row in unknowns_to_process_dataframe.iterrows():
    output_row = input_row
    output_row['error'] = None
    unknown_encoding = json.loads(input_row[unknown_encodings_column])
    results = face_recognition.compare_faces(knowns_encodings, numpy.array(unknown_encoding))
    first_true_rank = get_index_of_first_true(results)
    if first_true_rank is None or (len(known_references) < first_true_rank):
        guid = str(uuid.uuid4())
    else:
        guid = known_references[first_true_rank]
    output_row[known_references_column] = guid
    known_references.append(guid)
    knowns_encodings.append(numpy.array(unknown_encoding))
    output_rows.append(output_row)

output_dataframe = pandas.DataFrame(output_rows)
final_dataframe = pandas.concat([output_dataframe, knowns_dataframe])
# output_A_datasets[0].write_with_schema(output_dataframe)
# output_A_datasets[0].write_from_dataframe(final_dataframe)
output_A_datasets[0].write_with_schema(final_dataframe)
