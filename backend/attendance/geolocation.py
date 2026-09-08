"""Regras de geolocalização usadas na validação de presença do AURA.

O navegador fornece a posição do aluno, mas somente esta camada do backend
pode decidir se a posição está dentro do raio da sessão. A validação inclui
limites geográficos e um pré-filtro por caixa delimitadora antes do cálculo de
Haversine.
"""
from math import asin, cos, isfinite, radians, sin, sqrt


EARTH_RADIUS_METERS = 6_371_000
MIN_RADIUS_METERS = 1
MAX_RADIUS_METERS = 10_000


def validate_coordinate(value: float, minimum: float, maximum: float, name: str) -> float:
    """Valida uma coordenada finita dentro dos limites geográficos permitidos."""
    if not isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{name} deve estar entre {minimum} e {maximum}.')
    return value


def validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    """Valida e retorna um par de latitude/longitude em graus decimais."""
    return (
        validate_coordinate(latitude, -90.0, 90.0, 'latitude'),
        validate_coordinate(longitude, -180.0, 180.0, 'longitude'),
    )


def validate_radius(radius_meters: int) -> int:
    """Valida o raio operacional da cerca geográfica em metros."""
    if not MIN_RADIUS_METERS <= radius_meters <= MAX_RADIUS_METERS:
        raise ValueError(
            f'raio deve estar entre {MIN_RADIUS_METERS} e {MAX_RADIUS_METERS} metros.'
        )
    return radius_meters


def haversine_distance(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Calcula a distância entre dois pontos na superfície terrestre, em metros."""
    latitude_a, longitude_a = map(radians, (latitude_a, longitude_a))
    latitude_b, longitude_b = map(radians, (latitude_b, longitude_b))
    delta_latitude = latitude_b - latitude_a
    delta_longitude = longitude_b - longitude_a
    haversine_value = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude_a) * cos(latitude_b) * sin(delta_longitude / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(haversine_value))


def is_within_radius(
    origin_latitude: float,
    origin_longitude: float,
    target_latitude: float,
    target_longitude: float,
    radius_meters: int,
) -> bool:
    """Retorna se o ponto alvo está dentro ou exatamente no limite da sessão."""
    validate_coordinates(origin_latitude, origin_longitude)
    validate_coordinates(target_latitude, target_longitude)
    validate_radius(radius_meters)

    origin_latitude_rad = radians(origin_latitude)
    target_latitude_rad = radians(target_latitude)
    origin_longitude_rad = radians(origin_longitude)
    target_longitude_rad = radians(target_longitude)
    latitude_delta = radius_meters / EARTH_RADIUS_METERS
    longitude_scale = abs(cos(origin_latitude_rad))
    longitude_delta = (
        radius_meters / (EARTH_RADIUS_METERS * longitude_scale)
        if longitude_scale > 1e-10
        else float('inf')
    )

    if (
        target_latitude_rad < origin_latitude_rad - latitude_delta
        or target_latitude_rad > origin_latitude_rad + latitude_delta
        or target_longitude_rad < origin_longitude_rad - longitude_delta
        or target_longitude_rad > origin_longitude_rad + longitude_delta
    ):
        return False

    return haversine_distance(
        origin_latitude,
        origin_longitude,
        target_latitude,
        target_longitude,
    ) <= radius_meters
