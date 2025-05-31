import datetime
import io
from pathlib import Path

import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from pyproj.crs import CRS

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
    map_geometry = get_map_geometry(prefecture, year, resolution, auto_cache, cache_dir, crs)
    cleaned_data = clean_data(data)
    cleaned_data = validate_data(cleaned_data)
    merged_data = merge_data(map_geometry, cleaned_data, district_column)
    plot = create_plot(merged_data, heatmap_column, **kwargs)
    if save:
        if save_name is None:
            save_name = create_save_name(prefecture, year)
        save_plot(plot, Path(save_path) / save_name)


def prefecture_random_heatmap(
        prefecture: str,
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
    Generate random heatmap for the given prefecture.
    '''
    map_geometry = get_map_geometry(prefecture, year, resolution, auto_cache, cache_dir, crs)
    random_added_data = add_random_values(map_geometry)
    plot = create_plot(random_added_data, 'Random_Values', **kwargs)
    if save:
        if save_name is None:
            save_name = create_save_name(prefecture, year, random_data=True)
        save_plot(plot, Path(save_path) / save_name)


def get_map_geometry(
        prefecture: str,
        year: int,
        resolution: str,
        auto_cache: bool,
        cache_dir: str,
        crs: str,
) -> gpd.GeoDataFrame:
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
        map_geometry = gpd.read_file(file_cache_path)
    else:
        print('downloading map')
        map_geometry = download_map(prefecture_num, year, resolution)
        map_geometry.crs = CRS.from_user_input(crs)
        map_geometry = clean_map_data(map_geometry)
        if auto_cache:
            cache_map(map_geometry, file_cache_path, crs)
    return map_geometry


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
        use_defaults: bool = True,
        colour_for_na: str = 'darkgray',
        **kwargs,
) -> plt.Figure:
    fig, ax = plt.subplots()
    if use_defaults:
        if 'cmap' in kwargs:
            cmap = kwargs.pop('cmap')
        else:
            cmap = plt.cm.get_cmap('coolwarm')
        if 'norm' in kwargs:
            norm = kwargs.pop('norm')
            try:
                min_val = norm.vmin
            except AttributeError as e:
                print('Expected user provided norm to have a vmin attribute')
                raise e
        else:
            min_val = plot_data[plot_col].min()
            max_val = plot_data[plot_col].max()
            norm = mcolors.Normalize(vmin=min_val, vmax=max_val)
        cmap.set_under(colour_for_na)
        plot_data[plot_col] = plot_data[plot_col].fillna(min_val - 1)
        plot_data.plot(ax=ax, column=plot_col, cmap=cmap, norm=norm, **kwargs)
    else:
        plot_data.plot(ax=ax, column=plot_col, **kwargs)
    ax.set_axis_off()
    plt.show()
    return fig


def create_save_name(
        prefecture: str,
        year: int,
        random_data: bool = False,
) -> str:
    create_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M%S')
    if random_data:
        return f'{create_time}_{prefecture}_{year}_random.png'
    else:
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


def add_random_values(
        data: gpd.GeoDataFrame,
        add_col: str = 'Random_Values',
) -> gpd.GeoDataFrame:
    data[add_col] = np.random.rand(len(data))
    return data
