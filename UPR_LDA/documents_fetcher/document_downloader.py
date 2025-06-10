from UPR_LDA import models
import aiohttp

class DocumentDownloader:
    async def download(self, url) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.read()