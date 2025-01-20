from pathlib import Path
from typing import Literal

import pandas as pd
import requests

from config.prefectures import prefecture_numbers


ValidInputResolution = Literal['l', 'low', 'i', 'medium', 'h', 'high', 'f', 'full']
ResolutionCode = Literal['l', 'i', 'h', 'f']
resolution_code_mapping = {
    'low': 'l',
    'medium': 'i',
    'high': 'h',
    'full': 'f',
}


def prefecture_heatmap(
        prefecture: str,
        data: pd.DataFrame,
        year: int = 2023,
        resolution: ValidInputResolution = 'h',
        auto_cache: bool = True,
        save: bool = False,
        save_path: Path | str = 'plot',
        cache_dir: str = 'cache',
        **kwargs,
) -> None:
    ''''''
    resolution = get_resolution(resolution)
    cache_path = Path(cache_dir, f'{year}', f'{prefecture}_{resolution}.png')
    if cache_path.is_file():
        load_cache(cache_path)
    else:
        download_map(prefecture, year, resolution)
        if auto_cache:
            cache_map()

    cleaned_data = clean_data(data)
    validate_data(cleaned_data)
    create_plot(cleaned_data)
    if save:
        save_plot(Path(save_path))


def get_resolution(
        res: str,
        resolution_map: dict[str, str] = resolution_code_mapping,
) -> str:
    '''
    Get resolution from the given mapping. Priotises values of the dict first.
    '''
    if res in resolution_map.values():
        return res
    elif res in resolution_map:
        return resolution_map[res]
    else:
        raise ValueError(f'Invalid resolution: {res}')


def load_cache(cache_path: Path) -> None:
    ...


def download_map(
        prefecture: str,
        year: int,
        resolution: str,
) -> None:
    if resolution == 'high':
        res = 'h'
    else:
        resolution = 'i'
    pref = prefecture_numbers[prefecture]
    url = download_url(year, pref, res)
    with open('test.topojson', 'wb') as f:
        response = requests.get(url)
        f.write(response.content)


def cache_map() -> None:
    ...


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    return data


def validate_data(data: pd.DataFrame) -> pd.DataFrame:
    return data


def create_plot(data: pd.DataFrame) -> None:
    ...


def save_plot(save_path: Path) -> None:
    ...


def download_url(
        year: int,
        pref: str,
        res: ResolutionCode,
) -> str:
    ''''''
    return (
        f'https://geoshape.ex.nii.ac.jp/city/topojson/{year}0101/{pref:>02}/{pref:>02}_city.'
        f'{res}.topojson'
    )
