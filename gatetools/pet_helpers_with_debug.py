from box import Box
import numpy as np

def get_pet_data(root_file):
    data = Box()
    try:
        data_pet = root_file['pet_data']
        data.total_nb_primaries = data_pet['total_nb_primaries'].array(library='numpy')[0]
        data.latest_event_ID = data_pet['latest_event_ID'].array(library='numpy')[0]
        data.stop_time_sec = data_pet['stop_time_sec'].array(library='numpy')[0]
        data.start_time_sec = data_pet['start_time_sec'].array(library='numpy')[0]
        return data
    except:
        return False


def get_pet_counts(root_file):
    data = Box()

    coincidences = root_file['Coincidences']
    data.prompts_count = coincidences.num_entries
    print('len coincidences', len(coincidences))
    print('len coincidences.num_entries', coincidences.num_entries)

    delays = root_file['Delay']
    data.delays_count = delays.num_entries

    E1 = coincidences['energy1'].array(library='numpy')
    E2 = coincidences['energy2'].array(library='numpy')

    # Root tree analysis principle:
    # 1) consider a "Tree" (such as root_file['Coincidences'])
    # 2) convert the branches to numpy array
    # 3) use mask to select only some part of the tree

    # Compute the number of Random Coincidences
    # (when the two singles in coincidence came from two different events or are noise)
    event_id1 = coincidences['eventID1'].array(library='numpy')
    print('len event_id1', len(event_id1))
    event_id2 = coincidences['eventID2'].array(library='numpy')
    # Warning noise events have eventID == -2
    # https://opengate.readthedocs.io/en/latest/digitizer_and_detector_modeling.html?#noise
    mask_trues = (event_id1 == event_id2) & (event_id1 >= 0)
    data.randoms_count = data.prompts_count - len(event_id1[mask_trues])

    # Scattered coincidences (among the true)
    scatter_compton1 = coincidences['comptonPhantom1'].array(library='numpy')
    print('len compton', len(scatter_compton1))
    scatter_compton2 = coincidences['comptonPhantom2'].array(library='numpy')
    scatter_rayleigh1 = coincidences['RayleighPhantom1'].array(library='numpy')
    scatter_rayleigh2 = coincidences['RayleighPhantom2'].array(library='numpy')
    # if any of the value is greater than zero, it means a compton or a rayleigh occurs,
    # so this is a scattered event
    mask_scatter = (scatter_compton1 > 0) | (scatter_compton2 > 0) | (scatter_rayleigh1 > 0) | (scatter_rayleigh2 > 0)
    data.scatter_count = len(scatter_compton1[mask_trues & mask_scatter])

    # debug FIXME
    print('scatter count V1', data.scatter_count)
    Es1 = E1[mask_scatter]
    Es2 = E2[mask_scatter]
    print('E scatter = ', np.mean(E1[~mask_scatter]), np.mean(E2[~mask_scatter]))
    print('E scatter = ', np.mean(Es1), np.mean(Es2))

    ## alternative ?
    mask_scatter = (E1 < 0.485) | (E2 < 0.485)
    data.scatter_count = len(event_id1)
    print('scatter count V2 all', data.scatter_count)
    data.scatter_count = len(event_id1[mask_trues])
    print('scatter count V2 trues', data.scatter_count)
    data.scatter_count = len(event_id1[mask_scatter])
    print('scatter count V2 scatt', data.scatter_count)
    data.scatter_count = len(event_id1[mask_trues & mask_scatter])
    print('scatter count V2 both', data.scatter_count)

    # Remaining true events
    data.trues_count = data.prompts_count - data.randoms_count - data.scatter_count

    return data
