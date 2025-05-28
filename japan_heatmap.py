import datetime
import io
from pathlib import Path

import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import requests

from config.prefectures import prefecture_numbers


resolution_codes = {
    'low': 'l',
    'medium': 'i',
    'high': 'h',
    'full': 'f',
}


def prefecture_heatmap(
        prefecture: str,
        data: pd.DataFrame,
        heatmap_column: str = 'Value',
        district_column: str = 'City',
        year: int = 2023,
        resolution: str = 'h',
        auto_cache: bool = True,
        save: bool = False,
        save_path: Path | str = 'plot',
        save_name: str | None = None,
        cache_dir: str = 'cache',
        crs: str = 'EPSG:6668',
        **kwargs,
) -> None:
    '''
    Prefecture names accepted are of the following format:
    - Roman lettering (e.g. akita or Akita)
    - Roman lettering with -ken added (e.g. akita-ken or Akita-ken)
    - Japanese kanji name (e.g. 秋田 or 秋田県)
    - Japanese hiragana name (e.g. あきた or あきたけん)
    '''
    resolution = get_resolution(resolution)
    if prefecture not in prefecture_numbers:
        raise ValueError(f'Provided prefecture {prefecture} is not recognised')
    else:
        prefecture_num = prefecture_numbers[prefecture]
    file_cache_path = Path(
        cache_dir,
        f'{year}',
        f'{resolution}',
        f'{prefecture_num}_{resolution}.geojson',
    )
    if file_cache_path.is_file():
        print('loading map from cache')
        map_geometry: pd.DataFrame = gpd.read_file(file_cache_path)
    else:
        print('downloading map')
        map_geometry = download_map(prefecture_num, year, resolution)
        map_geometry.crs = crs
        map_geometry = clean_map_data(map_geometry)
        if auto_cache:
            cache_map(map_geometry, file_cache_path, crs)

    cleaned_data = clean_data(data)
    cleaned_data = validate_data(cleaned_data)
    merged_data = merge_data(map_geometry, cleaned_data, district_column)
    plot = create_plot(merged_data, heatmap_column)
    if save:
        if save_name is None:
            save_name = create_save_name(prefecture, year)
        save_plot(plot, Path(save_path) / save_name)


def get_resolution(
        res: str,
        resolution_map: dict[str, str] = resolution_codes,
) -> str:
    '''
    Get resolution from the given mapping. Prioritises values of the dict first.
    '''
    if res in resolution_map.values():
        return res
    elif res in resolution_map:
        return resolution_map[res]
    else:
        raise ValueError(f'Invalid resolution: {res}')


def download_map(
        pref_num: int,
        year: int,
        resolution: str,
) -> gpd.GeoDataFrame:
    url = download_url(year, pref_num, resolution)
    response = requests.get(url)
    map_bytes = io.BytesIO(response.content)
    map_data = gpd.read_file(map_bytes)
    return map_data


def cache_map(
        map_data: gpd.GeoDataFrame,
        save_path: Path,
        crs: str,
) -> None:
    save_path.parent.mkdir(exist_ok=True, parents=True)
    map_data.to_file(save_path, driver='GeoJSON', engine='fiona', crs=crs)


def clean_map_data(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    map_data = map_data.rename(
        columns={
            'N03_001': 'Prefecture',
            'N03_002': 'Bureau',
            'N03_003': 'County',
            'N03_004': 'City',
            'N03_005': 'Founding_date',
            'N03_006': 'Extinction_date',
            'N03_007': 'Code',
        },
        errors='ignore',
    )
    map_data = map_data.dropna(axis=1, how='all')
    map_data = map_data.drop(columns=['id'], errors='ignore')
    return map_data


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    return data


def validate_data(data: pd.DataFrame) -> pd.DataFrame:
    return data


def merge_data(
        map_data: gpd.GeoDataFrame,
        numerical_data: pd.DataFrame,
        district_column: str,
) -> gpd.GeoDataFrame:
    return pd.merge(map_data, numerical_data, how='left', left_on='City', right_on=district_column)


def create_plot(
        plot_data: gpd.GeoDataFrame,
        plot_col: str,
) -> plt.Figure:
    min_value = plot_data[plot_col].min()
    max_value = plot_data[plot_col].max()
    cmap = plt.cm.get_cmap('coolwarm')
    norm = mcolors.Normalize(vmin=min_value, vmax=max_value)
    cmap.set_under('lightgray')

    fig, ax = plt.subplots()
    plot_data[plot_col] = plot_data[plot_col].fillna(min_value - 1)
    plot_data.plot(ax=ax, edgecolor='k', lw=1, column=plot_col, cmap=cmap, norm=norm)
    ax.set_axis_off()
    plt.show()
    return fig


def create_save_name(
        prefecture: str,
        year: int,
) -> str:
    create_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M%S')
    return f'{create_time}_{prefecture}_{year}.png'


def save_plot(
        fig: plt.Figure,
        save_location: Path,
) -> None:
    save_location.parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(save_location)


def download_url(
        year: int,
        pref: int,
        res: str,
) -> str:
    ''''''
    return (
        f'https://geoshape.ex.nii.ac.jp/city/topojson/{year}0101/{pref:>02}/{pref:>02}_city.'
        f'{res}.topojson'
    )
