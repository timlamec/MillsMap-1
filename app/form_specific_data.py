
base_url = 'https://omdtz-data.org'

mill_columns = ['__id', 'start', 'end',
                'interviewee_mill_owner',
                'mills_number_milling_machines',
                'machines_machine_count',
                'Packaging_flour_fortified',
                'Packaging_flour_fortified_standard',
                'Location_addr_region',
                'Location_addr_district',
                'Location_mill_gps_coordinates']
machine_columns = ['__id', '__Submissions-id',
                   'commodity_milled',
                   'mill_type', 'operational_mill',
                   'energy_source', 'img_machines',
                   'non_operational']
columns = {'Submissions': mill_columns, 'Submissions.machines.machine':machine_columns}

array_columns = ['non_operational', 'commodity_milled', 'energy_source']
single_columns = ['Packaging_flour_fortified', 'operational_mill', 'interviewee_mill_owner', 'Packaging_flour_fortified_standard', 'mill_type']

# TODO: define all of the inputs to create a set of
# charts
def charts(datalist):
    for item in figures:
        makechart(item[chart_type], # pie, bar, other?
                  item[datatochart], # list or dict of possible chart elements
                  item[labels], # dict of labels
                  item[colorkeys], # dict of colors
                  item[sizes], # actual quantities
                  item[explode], # floats, need research
                  item[axisticks], # for bar charts
                  item[grids], # for bar charts
                  item[linestyle],
                  item[linewidth],
                  item[alpha],
                  item[fontsize],
                  item[fontweight])
        


                
                  
