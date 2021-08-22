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

def get_filters(filter_column_names, df):
	filter_selection = {} 
	filter_columns = df.loc[:,filter_column_names]
	for col in filter_columns:
		values_list = []
		values_list = filter_columns.loc[:,col]
		unique_values_list =[]
		unique_values_list = list(map(str, list(set(values_list))))
		filter_selection[col] = unique_values_list
		print(unique_values_list)
	return filter_selection


# def get_filters_list(filter_column_names, df):
# 	filter_selection = {} 
# 	filter_columns = df.loc[:,filter_column_names]
# 	for col in filter_columns:
# 		values_list = []
# 		values_list = filter_columns.loc[:,col].str.split()
# 		unique_values_list =[]
# 		for item in (values_list):
# 			if type(item) == list:
# 				for sub_item in item:
# 					if sub_item not in unique_values_list:
# 						unique_values_list.append(sub_item)
# 			else:
# 				if sub_item not in unique_values_list:
# 					unique_values_list.append(sub_item)
# 		filter_selection[col] = unique_values_list
# 	return filter_selection

def nested_dictionary_to_df(nested_table):
	while True:
		data_types = []
		for col in nested_table:
			if (type(nested_table[col][0])) == dict:
				data_types.append(type(nested_table[col][0]))
				nested_table = pd.concat([nested_table.drop(col, axis=1), nested_table[col].apply(pd.Series)], axis=1)					
		if dict not in data_types:
			break
	flat_table = nested_table
	return flat_table




if __name__ == '__main__':
    pass
