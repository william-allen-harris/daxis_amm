"Abstract Classes for Graphs."
import logging
import asyncio
from typing import Any, Coroutine, List, Dict, Tuple

from gql import Client, gql
from gql.transport.async_transport import AsyncTransport


class BaseGraph:
    "Base Graph."
    transporter: AsyncTransport

    @staticmethod
    async def __query_gpl(session: Client, query: str) -> dict:
        "Query the gql graph."
        counter = 1
        while True:
            try:
                logging.info(f"Retreiving {query} for Subgraph")
                query_result = await session.execute(gql(query))
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
    async def query_gql(cls, querys: list[str]) -> Tuple[Dict]:
        "Perform multiple queries similtaniously."
        async with Client(transport=cls.transporter, fetch_schema_from_transport=True) as session:
            tasks = [cls.__query_gpl(session, query) for query in querys]
            responses = await asyncio.gather(*tasks)
        return responses

    @staticmethod
    async def __wrapped_funcs(funcs: List[Coroutine]):
        "Perform multiple asyncio Graph functions similtaniously."
        responses = await asyncio.gather(*funcs, return_exceptions=True)
        return responses

    @classmethod
    def run(cls, funcs: Dict[str, Coroutine]) -> Dict[str, Any]:
        "Perform multiple queries similtaniously."
        wrapped_funcs = cls.__wrapped_funcs(list(funcs.values()))
        return dict(zip(funcs.keys(), asyncio.get_event_loop().run_until_complete(wrapped_funcs)))
