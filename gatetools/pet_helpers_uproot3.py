import uproot3
import numpy as np


def tree_get_branch_types(tree):
    """
    For a given ROOT Tree, return the list of branch types, only if the type is numerics
    All string/char branches are ignored (for the moment)
    """
    info = {}
    for branch in tree.keys():
        a = tree.array(branch)
        # check that the array is not empty
        if len(a) == 0:
            continue
        branch_type = type(a[0])
        if branch_type is not type(b'c'):
            info[branch] = branch_type
    return info


def branch_job_update(run_id, previous_root_file, branch, array, verbose=True):
    """
    Update the array values of the current branch, according to the data found in the
    previous root file.
    For the events ID: values are shifted by the latest_event_ID
    For the run ID: values take the run_id value
    For the time: values are shifted by stop_time_sec
    """
    if not previous_root_file:
        return array
    # Event ID
    if branch == b'eventID1' or branch == b'eventID2':
        latest_event_id = previous_root_file['pet_data'].array('latest_event_ID')[0]
        # FIXME negative event !
        mask = array < 0
        if verbose:
            print(f'\t\tShifting event ID by {latest_event_id} for branch {branch} '
                  f'(noise: nb of negative event id = {len(array[mask])})')
        array += np.int64(latest_event_id)
        array[mask] -= np.int64(latest_event_id)
    # Run ID
    if branch == b'runID':
        # we assume this is the same run id for all elements
        s = run_id - array[0]
        array += np.int64(s)
        if verbose:
            print(f'\t\tShifting run ID by {s} for branch {branch}')
    # time1 time2
    if branch == b'time1' or branch == b'time2':
        stop_time_sec = previous_root_file['pet_data'].array('stop_time_sec')[0]
        array += np.int64(stop_time_sec)
        if verbose:
            print(f'\t\tShifting time by {stop_time_sec} seconds for branch {branch}')

    # return the array of values
    return array


def pet_merge_root_output(root_filenames, output_filename, verbose=True):
    """
    Merge several root file that contains PET output.
    This take into account the event ID and the time.
    """
    root_files = []
    for fn in root_filenames:
        try:
            root_file = uproot3.open(fn)
        except Exception:
            print(f'Cannot open the file {fn}. Is this a root file ?')
            exit(-1)
        root_files.append(root_file)

    # print
    if verbose:
        print(f'Reading {len(root_files)} root files')

    # create the output file
    out = uproot3.recreate(output_filename)

    # Merge all the branches
    for tree in root_files[0].keys():
        if not hasattr(root_files[0][tree], 'keys'):
            continue
        if verbose:
            print(f'Merging the tree {tree}')
        pet_merge_tree(root_filenames, root_files, tree, out, verbose)


def pet_merge_tree(root_filenames, root_files, tree_name, out, verbose):
    first = root_files[0][tree_name]
    branch_types = tree_get_branch_types(first)
    # check that the branch is not empty
    if branch_types == {}:
        return
    out[tree_name] = uproot3.newtree(branch_types)
    previous = None
    run_id = 0
    for f in root_files:
        if verbose:
            print(f'\tMerging {root_filenames[run_id]}')
        tree = f[tree_name]
        branch_values = {}
        for branch in branch_types.keys():
            a = branch_job_update(run_id, previous, branch, tree.array(branch), verbose)
            branch_values[branch] = a
        previous = f
        run_id += 1
        out[tree_name].extend(branch_values)
