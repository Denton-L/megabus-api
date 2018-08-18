import datetime
import json
import urllib.parse
import urllib.request

class MegabusError(Exception):
    def __init__(self, megabus_errors=None, http_error=None):
        if megabus_errors:
            message = ', '.join(
                    map(lambda e: '%s (%s)' % (e['message'], e['id']),
                        megabus_errors))
        elif http_error:
            message = http_error
        else:
            message = ''

        super().__init__(message)


class MegabusApi:
    BASE_API_URL = 'https://%s.megabus.com/%s/api/%s?%s'

    def __init__(self, country_code):
        self.country_code = country_code.value

    @staticmethod
    def get_date_from_iso(date_string):
        year, month, date = map(int, date_string.split('-'))
        return datetime.date(year, month, date)

    def send_get_request(self, endpoint_group, endpoint, params):
        url = MegabusApi.BASE_API_URL % (
                self.country_code,
                endpoint_group,
                endpoint,
                urllib.parse.urlencode(params))

        try:
            with urllib.request.urlopen(url) as response:
                parsed_response = json.load(response)
        except urllib.error.HTTPError as e:
            raise MegabusError(http_error='Invalid request.') from e

        if 'errors' in parsed_response and parsed_response['errors']:
            raise MegabusError(megabus_errors=parsed_response['errors'])

        return parsed_response

    def get_travel_dates(self, origin_id, destination_id):
        response = self.send_get_request('journey-planner', 'journeys/travel-dates', {
            'originCityId': origin_id,
            'destinationCityId': destination_id})

        return map(MegabusApi.get_date_from_iso, response['availableDates'])

    def get_prices(self, origin_id, destination_id, departure_date, days, total_passengers=1):
        # TODO: handle other parameters, like special needs
        response = self.send_get_request('journey-planner', 'journeys/prices', {
            'originId': origin_id,
            'destinationId': destination_id,
            'departureDate': departure_date.isoformat(),
            'days': days,
            'totalPassengers': total_passengers})

        return map(lambda date_info: (
            date_info['price'], self.get_date_from_iso(date_info['date']), date_info['available']),
            response['dates'])

    def get_destination_cities(self, origin_id):
        response = self.send_get_request('journey-planner', 'destination-cities', {
            'originCityId': origin_id})

        return map(lambda city_info: (
            city_info['id'], city_info['name'], city_info['latitude'], city_info['longitude']),
            response['cities'])
