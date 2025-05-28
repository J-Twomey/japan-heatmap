import pytest

from japan_heatmap import(
    download_url,
    get_resolution,
)


@pytest.mark.parametrize(
    ('resolution', 'expected'),
    (
        pytest.param('value', 'v', id='in_keys'),
        pytest.param('v', 'v', id='in_values'),
    ),
)
def test_get_resolution(
        resolution: str,
        expected: str,
) -> None:
    ''''''
    mapping = {
        'value': 'v',
        'v': 'bad_value',
    }
    return_resolution = get_resolution(resolution, resolution_map=mapping)
    assert return_resolution == expected


def test_get_resolution_error_case() -> None:
    ''''''
    mapping = {'value': 'v'}
    resolution = 'invalid'
    with pytest.raises(ValueError, match='Invalid resolution: invalid'):
        get_resolution(resolution, resolution_map=mapping)


def test_download_url() -> None:
    ''''''
    year = 2005
    pref = 5
    res = 'h'
    expected = 'https://geoshape.ex.nii.ac.jp/city/topojson/20050101/05/05_city.h.topojson'
    actual = download_url(year, pref, res)
    assert actual == expected
