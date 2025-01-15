import japan_heatmap as jpnh


def test_download_url() -> None:
    ''''''
    year = 2005
    pref = '5'
    res = 'h'
    expected = 'https://geoshape.ex.nii.ac.jp/city/topojson/20050101/01/05_city.h.topojson'
    actual = jpnh.download_url(year, pref, res)
    