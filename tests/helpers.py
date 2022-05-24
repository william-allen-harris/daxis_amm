"Helpers for unittests"
"Unit test helper functions."
import pickle


def read_pickle(file_name: str):
    with open(f"/workspaces/daxis_amm/tests/data/{file_name}", "rb") as dill_file:
        data = pickle.load(dill_file)
    return data
