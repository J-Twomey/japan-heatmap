from pathlib import Path

import pandas as pd



def prefecture_heatmap(
        prefecture: str,
        data: pd.DataFrame,
        year: int = 2022,
        resolution: str = 'high',
        auto_cache: bool = True,
        save_path: Path | str | bool = False,
        cache_dir: str = 'cache',
        **kwargs,
) -> None:
    ''''''
    cache_path = Path(cache_dir, f'{year}', f'{prefecture}.png')
    if cache_path.is_file():
        try_loading_cache(cache_path)
    else:
        download_map(prefecture, year, resolution)
        if auto_cache:
            cache_map()

    cleaned_data = clean_data(data)
    validate_data(cleaned_data)
    create_plot(cleaned_data)
    if save_path:
        save_plot(Path(save_path))


def try_loading_cache(cache_path: Path) -> None:
    ...


def download_map(prefecture: str, year: int, resolution: str) -> None:
    ...


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

