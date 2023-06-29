"""
Abstract Classes for Graphs.
"""
import logging as _log
import asyncio as _as
import typing as _tp

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


class BaseGraph:
    """
    Base Graph.
    """

    url: str

    @staticmethod
    async def __query_gpl(session: Client, query: str) -> dict:
        """
        Query the gql graph.

        :param session: The gql client session.
        :type session: gql.Client
        :param query: The gql query string.
        :type query: str
        :return: The query result.
        :rtype: dict
        """
        counter = 1
        while True:
            try:
                _log.info(f"Retrieving {query} for Subgraph")
                query_result = await session.execute(gql(query))
            except Exception as err:
                _log.warning(f"Retrying (total={counter}). Trying again... Error: {err}")
                counter += 1
                if counter > 5:
                    _log.error(f"Query {query} failed 5 times... Stopping", exc_info=True)
                    raise Exception("Query GQL error") from err
                continue
            break
        return query_result

    @classmethod
    async def query_gql(cls, queries: _tp.List[str]) -> _tp.Tuple[_tp.Dict]:
        """
        Perform multiple queries simultaneously.

        :param queries: The list of gql query strings.
        :type queries: List[str]
        :return: The list of query results.
        :rtype: Tuple[Dict]
        """
        async with Client(transport=AIOHTTPTransport(url=cls.url), fetch_schema_from_transport=True) as session:
            tasks = [cls.__query_gpl(session, query) for query in queries]
            responses = await _as.gather(*tasks)
        return responses

    @staticmethod
    async def __wrapped_funcs(funcs: _tp.List[_tp.Coroutine]):
        """
        Perform multiple asyncio Graph functions simultaneously.

        :param funcs: The list of coroutines representing the graph functions.
        :type funcs: List[Coroutine]
        :return: The list of responses.
        """
        responses = await _as.gather(*funcs, return_exceptions=True)
        return responses

    @classmethod
    def run(cls, funcs: _tp.Dict[str, _tp.Coroutine]) -> _tp.Dict[str, _tp.Any]:
        """
        Perform multiple queries simultaneously.

        :param funcs: The dictionary of function names and coroutines.
        :type funcs: Dict[str, Coroutine]
        :return: The dictionary of function names and their results.
        :rtype: Dict[str, Any]
        """
        wrapped_funcs = cls.__wrapped_funcs(list(funcs.values()))
        return dict(zip(funcs.keys(), _as.get_event_loop().run_until_complete(wrapped_funcs)))
