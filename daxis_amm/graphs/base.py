"Abstract Classes for Graphs."
import logging
import multiprocessing
from typing import Callable, Dict, Any, Tuple

from gql import Client, gql


class BaseGraph:
    "Base Graph."
    client: Client

    @classmethod
    def query_gpl(cls, query: str) -> dict:
        "Query a Client."
        counter = 1
        while True:
            try:
                logging.info(f"Retreiving {query} for Subgraph")
                query_result = cls.client.execute(gql(query))
            except Exception as err:
                logging.warning(f"Retrying(total={counter}. trying again... Error: {err}")
                counter += 1
                if counter > 5:
                    logging.error(f"Query {query} failed 5 times... Stopping", exc_info=True)
                    raise Exception("Query GQL error") from err
                continue
            break
        return query_result

    @classmethod
    def wrapper_query_gpl(cls, query: str, return_dict: dict) -> None:
        "Wrapper for querying a client. Used for multiprocessing."
        return_dict[query] = cls.query_gpl(query)

    @classmethod
    def query_multiple_gql(cls, querys: list[str]) -> dict:
        "Perform multiple queries similtaniously."
        manager = multiprocessing.Manager()
        return_dict = manager.dict()

        jobs = []
        for query in querys:
            process = multiprocessing.Process(target=cls.wrapper_query_gpl, args=(query, return_dict))
            jobs.append(process)
            process.start()

        for process in jobs:
            process.join()

        return return_dict

    @classmethod
    def wrapper_get_data(cls, func: Callable, name: str, return_dict: dict, args: tuple) -> None:
        "Wrapper to run get data functions similtaniously."
        return_dict[name] = func(*args)

    @classmethod
    def multiprocess(cls, funcs_dict: Dict[str, Tuple[Callable, tuple]]) -> dict:
        "Perform multiple queries similtaniously."
        manager = multiprocessing.Manager()
        return_dict = manager.dict()

        jobs = []
        for name in funcs_dict:
            func, args = funcs_dict[name]
            process = multiprocessing.Process(target=cls.wrapper_get_data, args=(func, name, return_dict, args))
            jobs.append(process)
            process.start()

        for process in jobs:
            process.join()

        return return_dict
