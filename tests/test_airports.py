import io
from models.airport import Airport
from services.airport_service import (
    get_all_airports,
    get_airport_by_id,
    get_airport_by_code,
    haversine_distance,
    import_airports_from_csv
)
from utils.validators import validate_coordinates

def test_airport_listing_and_filter(app):
    with app.app_context():
        airports = get_all_airports()
        assert len(airports) >= 2

        del_apt = get_airport_by_code('DEL')
        assert del_apt is not None
        assert del_apt.city == 'New Delhi'

        bom_apt = get_airport_by_code('BOM')
        assert bom_apt is not None
        assert bom_apt.city == 'Mumbai'

def test_airport_search_query(client):
    response = client.get('/airports?search=Mumbai')
    assert response.status_code == 200
    assert b"Chhatrapati Shivaji Maharaj" in response.data

def test_haversine_distance():
    # Distance between DEL (28.556, 77.100) and BOM (19.089, 72.865) is approx 1140-1160 km
    dist = haversine_distance(28.5562, 77.1000, 19.0896, 72.8656)
    assert 1100 <= dist <= 1200

def test_coordinate_validation():
    valid, msg = validate_coordinates(28.55, 77.10)
    assert valid is True

    invalid_lat, msg = validate_coordinates(120.0, 77.10)
    assert invalid_lat is False
    assert "Latitude" in msg

    invalid_str, msg = validate_coordinates("invalid", "number")
    assert invalid_str is False

def test_airport_csv_import(app):
    with app.app_context():
        csv_content = """name,city,state,iata_code,icao_code,latitude,longitude,category,operational_status,terminals,description
Kempegowda International Airport,Bengaluru,Karnataka,BLR,VOBL,13.1986,77.7066,International,Operational,"T1, T2",Bangalore Airport
Invalid Airport,TestCity,TestState,INV,TEST,999.0,77.0,Domestic,Operational,T1,Bad Lat
"""
        file_stream = io.BytesIO(csv_content.encode('utf-8'))
        res = import_airports_from_csv(file_stream)
        assert res['imported'] == 1
        assert res['skipped'] == 1  # 1 invalid latitude
        
        blr = Airport.query.filter_by(iata_code='BLR').first()
        assert blr is not None
        assert blr.city == 'Bengaluru'
