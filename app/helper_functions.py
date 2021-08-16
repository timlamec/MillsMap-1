import pandas as pd

def dict_to_df(dictionary):
	dictionary_columns = []
	while True:
		data_types = []
		for col in dictionary:
			data_types.append(type(dictionary[col][0]))
		if dict not in data_types:
			break
		for col in dictionary:
			if (type(dictionary[col][0])) == dict:
				dictionary_columns.append(col)
				df = pd.concat([dictionary.drop(col, axis=1), dictionary[col].apply(pd.Series)], axis=1)
	return df