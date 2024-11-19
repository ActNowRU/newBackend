from httpx import AsyncClient
from dataclasses import dataclass


@dataclass
class YandexGeocoder:

    client: AsyncClient
    api_key: str
    url: str = "https://geocode-maps.yandex.ru/1.x"

    @classmethod
    def with_client(cls, api_key) -> "YandexGeocoder":
        client = AsyncClient()
        return cls(client=client, api_key=api_key)

    async def address_to_geopoint(self, address: str) -> tuple[float, float] | None:
        response = await self.client.get(
            self.url,
            params={
                "apikey": self.api_key,
                "geocode": address,
                "format": "json",
            },
        )
        response.raise_for_status()

        result = response.json()["response"]["GeoObjectCollection"]["featureMember"]

        if not result:
            return None

        lat, lon = result[0]["GeoObject"]["Point"]["pos"].split(" ")
        return float(lon), float(lat)
