# non-pytest fixtures
def empty_pickle():
    match_dict = {}
    inputs = {'pickle_tasks': match_dict}
    return inputs
