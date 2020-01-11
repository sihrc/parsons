import requests
import os
import petl
from parsons.etl.table import Table


class TargetSmartConnector(object):

    def __init__(self, api_key=None, uri='https://api.targetsmart.com/'):

        if api_key is None:

            try:
                api_key = os.environ['TS_API_KEY']
            except KeyError:
                raise KeyError('No TargetSmart API key found. Please store'
                               ' in environment variable or pass as an'
                               'argument.')

        self.uri = uri
        self.api_key = api_key
        self.headers = {'x-api-key': self.api_key}

    def request(self, url, args=None, raw=False):

        r = requests.get(url, headers=self.headers, params=args)

        # This allows me to deal with data that needs to be munged.
        if raw:

            return r.json()

        return Table(r.json()['output'])


class Person(object):

    def __init__(self):

        return None

    def data_enhance(self, search_id, search_id_type='voterbase', state=None):
        """
        Searches for a record based on an id or phone or email address

        `Args:`
            search_id: str
                The primary key or email address or phone number
            search_id_type: str
                One of ``voterbase``, ``exacttrack``, ``abilitec_consumer_link``, ``phone``,
                ``email``, ``smartvan``, ``votebuilder``, ``voter``, ``household``.
            state: str
                Two character state code. Required if ``search_id_type`` of ``smartvan``,
                ``votebuilder`` or ``voter``.
        `Returns`
            Parsons Table
                See :ref:`parsons-table` for output options.
        """

        if search_id_type in ['smartvan', 'votebuilder', 'voter'] and state is None:

            raise KeyError("Search ID type '{}' requires state kwarg".format(search_id_type))

        if search_id_type not in ('voterbase', 'exacttrack', 'abilitec_consumer_link', 'phone',
                                  'email', 'smartvan', 'votebuilder', 'voter', 'household'):

            raise ValueError('Search_id_type is not valid')

        url = self.connection.uri + 'person/data-enhance'

        args = {'search_id': search_id,
                'search_id_type': search_id_type,
                'state': state
                }

        return self.connection.request(url, args=args)

    def radius_search(self, first_name, last_name, middle_name=None, name_suffix=None,
                      latitude=None, longitude=None, address=None, address_type='reg',
                      radius_size=10, radius_unit='miles', max_results=10, gender='a',
                      age_min=None, age_max=None, composite_score_min=1, composite_score_max=100,
                      last_name_exact=True, last_name_is_prefix=False, last_name_prefix_length=10):
        """
        Search for a person based on a specified radius

        `Args`:
            first_name: str
                One or more alpha characters
            last_name: str
                One or more alpha characters
            middle_name: str
                One or more alpha characters
            name_suffix: str
                One or more alpha characters
            latitude: float
                Floating point number (e.g. 33.738987255507)
            longitude: float
                Floating point number (e.g. -116.40833849559)
            address: str
                Any geocode-able address
            address_type: str
                ``reg`` for registration (default) or ``tsmart`` for TargetSmart
            radius_unit: str
                One of ``meters``, ``feet``, ``miles`` (default), or ``kilometers``.
            max_results: int
                Default of ``10``. An integer in range [0 - 100]
            gender: str
                Default of ``a``. One of ``m``, ``f``, ``u``, ``a``.
            age_min: int
                A positive integer
            age_max: int
                A positive integer
            composite_score_min: int
                An integer in range [1 - 100]. Filter out results with composite score
                less than this value.
            composite_score_max: int
                An integer in range [1 - 100]. Filter out results with composite score
                greater than this value.
            last_name_exact: boolean
                By default, the full last name is used for finding matches if the length of the
                last name is not longer than 10 characters. As an example, “anders” is less likely
                to match to “anderson” with this enabled. Disable this option if you are using
                either ``last_name_is_prefix`` or ``last_name_prefix_length``.
            last_name_is_prefix: boolean
                By default, the full last name is used for finding matches. Enable this parameter
                if your search last name is truncated. This can be common for some client
                applications that for various reasons do not have full last names. Use this
                parameter along with ``last_name_prefix_length`` to configure the length of the last
                name prefix. This parameter is ignored if ``last_name_exact`` is enabled.
            last_name_prefix_length: int
                By default, up to the first 10 characters of the search last name are used for
                finding relative matches. This value must be between 3 and 10. This parameter is
                ignored if last_name_exact is enabled.
        `Returns`
            Parsons Table
                See :ref:`parsons-table` for output options.
        """

        if (latitude is None or longitude is None) and address is None:
            raise ValueError('Lat/Long or Address required')

        # Convert booleans
        for a in [last_name_exact, last_name_is_prefix]:
            a = str(a)

        url = self.connection.uri + 'person/radius-search'

        args = {'first_name': first_name,
                'last_name': last_name,
                'middle_name': middle_name,
                'name_suffix': name_suffix,
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'radius_size': radius_size,
                'radius_unit': radius_unit,
                'max_results': max_results,
                'gender': gender,
                'age_min': age_min,
                'age_max': age_max,
                'composite_score_min': composite_score_min,
                'composite_score_max': composite_score_max,
                'last_name_exact': last_name_exact,
                'last_name_is_prefix': last_name_is_prefix,
                'last_name_prefix_length': last_name_prefix_length
                }

        r = self.connection.request(url, args=args, raw=True)
        return Table([itm for itm in r['output']]).unpack_dict('data_fields', prepend=False)

    def phone(self, table):
        """
        Match based on a list of 500 phones numbers. Table
        can contain up to 500 phone numbers to match

        `Args:`
            table: parsons table
                See :ref:`parsons-table`. One row per phone number,
                up to 500 phone numbers.
        `Returns:`
            See :ref:`parsons-table` for output options.
        """

        url = self.connection.uri + 'person/phone-search'

        args = {'phones': list(petl.values(table.table, 0))}

        return Table(self.connection.request(url, args=args, raw=True)['result'])

    def email(self, table, match_type=None, append_level=None, include_blank=None):
        """
        Match based a list up to 200 emails. Table
        can contain up to 200 emails to match

        `Args:`
            table: parsons table
                See :ref:`parsons-table`. One row per email,
                up to 200 emails.
            emails: str
                A comma separated list of up to 200 valid emails
            match_type: str
                `H` or `I`  indicating if the email is matched at
                the individual person level or at the household level
            append_level: str
                `Household` or `Individual` indicating the level of
                the opt-in email address
            include_blank: str
                Include persons without specified `match_type` and
                `append_level` included as optional parameter in the request
        `Returns:`
            See :ref:`parsons-table` for output options.
        """

        url = self.connection.uri + 'person/email-search'
        args = {
            'emails': list(petl.values(table.table, 0)),
            "match_type": match_type,
            "append_level": append_level,
            "include_blank": include_blank,
        }

        args = {
            key: value for key, value in args.items() if value is not None
        }

        return Table(self.connection.request(url, args=args, raw=True)['result'])

    def listbuilder(self, where, mode, percentage=None, limit=25):
        """
        Low-latency record counting and list selection from the
        TargetSmart platform database

        `Args:`
            where: str
                SQL Where Clause e.g. "vb.vf_source_state = 'NY'"
            mode: str
                Choice of ["count", "list", "sample"]
            percentage: int
                Between 0 and 100 for mode = "sample"
            limit: int
                Integer in range [1, 500000] inclusive.
        """
        url = self.connection.uri + 'person/listbuilder'
        args = {
            "where": where,
            "mode": mode,
            "limit": limit
        }

        if mode == "sample":
            args["percentage"] = percentage

        args = {
            key: value for key, value in args.items() if value is not None
        }
        response = self.connection.request(url, args=args, raw=True)
        if mode == "count":
            return response["count"]
        return Table(response["list"])

    def listjoiner(self, table, fields=None):
        """
        Match based a list up to 500 voter VoterBase IDs. Table
        can contain up to 500 IDS to match

        `Args:`
            table: parsons table
                See :ref:`parsons-table`. One row per VoterBase ID,
                up to 500 IDs.
            fields: List[str]
                Configured data-enhance fields
        """
        fields = fields or []
        url = self.connection.uri + 'person/listbuilder'

        args = {
            "ids": list(petl.values(table.table, 0))
        }
        if fields:
            args["fields"] = ",".join(fields)

        return Table(self.connection.request(url, args=args, raw=True)["result"])


class Service(object):

    def __init__(self):

        return None

    def district(self, search_type='zip', address=None, zip5=None, zip4=None, state=None,
                 latitude=None, longitude=None):
        """
        Return district information based on a geographic point. The method allows you to
        search based on the following:

        .. list-table::
            :widths: 30 30 30
            :header-rows: 1

            * - Search Type
              - Search Type Name
              - Required kwarg(s)
            * - Zip Code
              - ``zip``
              - ``zip5``, ``zip4``
            * - Address
              - ``address``
              - ``address``
            * - Point
              - point
              - ``latitude``, ``longitude``

        `Args`:
            search_type: str
                The type of district search to perform. One of ``zip``, ``address``
                or ``point``.
            address: str
                An uparsed full address
            zip5: str
                The USPS Zip5 code
            zip4: str
                The USPS Zip4 code
            state: str
                The two character state code
            latitude: float or str
                Valid latitude floating point
            lontitude: float or str
                Valid longitude floating point
        `Returns`:
            Parsons Table
                See :ref:`parsons-table` for output options.
        """

        if search_type == 'zip' and None in [zip5, zip4]:
            raise ValueError("Search type 'zip' requires 'zip5' and 'zip4' arguments")

        elif search_type == 'point' and None in [latitude, longitude]:
            raise ValueError("Search type 'point' requires 'latitude' and 'longitude' arguments")

        elif search_type == 'address' and None in [address]:
            raise ValueError("Search type 'address' requires 'address' argument")

        elif search_type not in ['zip', 'point', 'address']:
            raise KeyError("Invalid 'search_type' provided. ")

        else:
            pass

        url = self.connection.uri + 'service/district'

        args = {'search_type': search_type,
                'address': address,
                'zip5': zip5,
                'zip4': zip4,
                'state': state,
                'latitude': latitude,
                'longitude': longitude
                }

        return Table([self.connection.request(url, args=args, raw=True)['match_data']])

    def dictionary(self, field: str = None, prefix: str = None):
        """
        Returns information about the different data fields available.
        Explore human readable descriptions for component fields,
        statistical information about values for those fields, and discover
        new or updated fields given the following arguments:

        .. list-table::
            :widths: 20 20 50
            :header-rows: 1

            * - Fields
              - Optional
              - Permitted Values
            * - field
              - ``or prefix``
              - ``string with max 64 characters``
            * - prefix
              - ``or field``
              - ``string, possible values can be found in a request without prefix``

        `Args`:
            field: str
                string with max 64 characters. target field for more information
            prefix: str
                string, prefix of fields. possible values can be found in a request without prefix
        `Returns`:
            Parsons Table
                See :ref:`parsons-table` for output options.
        """

        if field is None and prefix is None:
            raise ValueError("At least one of 'field' or 'prefix' must be provided")

        url = self.connection.uri + 'service/dictionary'

        args = {'field': field,
                'prefix': prefix,
                }

        return Table([self.connection.request(url, args=args, raw=True)['result']])

    def onboarding(self, platform: str, audience: str, status_email: str, ids: str,
                   facebook_adid: str = None):
        """
        Create custom audience segments for digital ad targeting.
        Upon Facebook onboarding workflow completion, the custom audience is
        ready to be used in your Facebook platform ads.

        .. list-table::
            :widths: 20 20 50
            :header-rows: 1

            * - Fields
              - Optional
              - Permitted Values
            * - platform
              - ``X``
              - ``facebook or liveramp``
            * - audience
              - ``X``
              - ``string max 50 characters``
            * - status_email
              - ``X``
              - ``string max 50 characters``
            * - facebook_adid
              - ````
              - ``string``
            * - ids
              - ``X``
              - ``comma separated list without spaces of valid Voterbase IDs``

        `Args`:
            platform: str
                facebook or liveramp
            audience: str
                This paramater is your desired audience name. Accepts a string of up
                to 50 characters, including spaces. This is the "Audience Name" that
                will be used to create a custom audience.
            status_email: str
                An email address to receive status updates on your request
            ids: str
                A sorted comma separated list (without spaces) of valid Voterbase IDs
            facebook_adid: str
                Your Ad Account ID (required if ``platform``=``facebook``)
        `Returns`:
            boolean success
        """

        url = self.connection.uri + 'service/onboarding'

        args = {
            "platform": platform,
            "audience": audience,

        }

        post_url = self.connection.request(url, args=args, raw=True)['url']

        response = requests.post(post_url, json={
            "status_email": status_email,
            "ids": ids,
            "facebook_adid": facebook_adid,
        })

        return response.status_code == 200


class Voter(object):

    def __init__(self, connection):

        self.connection = connection

    def voter_registration_check(self, first_name=None, last_name=None,
                                 state=None, street_number=None,
                                 street_name=None, city=None, zip_code=None,
                                 age=None, dob=None, phone=None, email=None,
                                 unparsed_full_address=None,
                                 obj_type="dict"):
        """
        Searches for a registered individual, returns matches.

        A search must include the at minimum first name, last name and state.

        `Args:`
            first_name: str
                Required; One or more alpha characters. Trailing wildcard allowed
            last_name: str
                Required; One or more alpha characters. Trailing wildcard allowed
            state: str
                Required; Two character state code (e.g. ``NY``)
            street_number: str
                Optional; One or more alpha characters. Trailing wildcard allowed
            street_name: str
                Optional; One or more alpha characters. Trailing wildcard allowed
            city: str
                Optional; The person's home city
            zip_code: str
                Optional; Numeric characters. Trailing wildcard allowed
            age; int
                Optional; One or more integers. Trailing wildcard allowed
            dob; str
                Numeric characters in YYYYMMDD format. Trailing wildcard allowed
            phone; str
                Integer followed by 0 or more * or integers
            email: str
                Alphanumeric character followed by 0 or more * or legal characters
                (alphanumeric, @, -, .)
            unparsed_full_address: str
                One or more alphanumeric characters. No wildcards.
        `Returns`
            Parsons Table
                See :ref:`parsons-table` for output options.
        """

        url = self.connection.uri + 'voter/voter-registration-check'

        if None in [first_name, last_name, state]:
            raise ValueError("""Function must include at least first_name,
                             last_name, and state.""")

        args = {'first_name': first_name,
                'last_name': last_name,
                'state': state,
                'street_number': street_number,
                'street_name': street_name,
                'city': city,
                'zip_code': zip_code,
                'age': age,
                'dob': dob,
                'phone': phone,
                'email': email,
                'unparsed_full_address': unparsed_full_address
                }

        return self.connection.request(url, args=args, raw=True)

    def voter_suggest(self, first_name=None, middle_name=None, last_name=None,
                      state=None, street_number=None, street_name=None, city=None,
                      zip_code=None, county=None, age=None, dob=None, phone=None,
                      email=None, max_results=25):
        """
        Support for low-latency interactive search user interfaces allowing a user
        to find a voter record with minimal keystrokes

        Each request uses required and allowed keys. The ``state`` or ``zip_code`` are
        required. If ``zip_code`` is provided and not ``state``, the leading 3 digits in
        the ``zip_code`` will be used to look up the correct ``state``. Additionally,
        each query must provide at least one valid character for any of the following:
        ``first_name``, ``last_name``, ``middle_name``, ``street_name``, ``phone``, or ``email``. All other allowed keys shown in the following table are optional.

        `Args:`
        first_name
            Alpha character followed by 0 or more * or alpha characters
        middle_name
            Alpha character followed by 0 or more * or alpha characters
        last_name
            Alpha character followed by 0 or more * or alpha characters
        street_number
            Alphanumeric character followed by 0 or more * or alphanumeric characters
        street_name
            Alphanumeric character followed by 0 or more * or alphanumeric characters
        city
            Alpha character followed by 0 or more * or alpha characters
        state
            wo character U.S. state code (e.g. ``NY``)
        zip_code
            3 Integers followed by 2 or more * or integers
        county
            Alphanumeric character followed by 0 or more * or alphanumeric characters
        phone
            Integer followed by 0 or more * or integers
        email
            Alphanumeric character followed by 0 or more * or legal characters (alphanumeric, @, -, .)
        age
            Integer followed by 0 or more * or integers
        dob
            Integers in YYYYMMDD format
        max_results
            An integer in range [1 - 50]
        """
        url = self.connection.uri + 'voter/voter-suggest'

        if None in [first_name, last_name, state]:
            raise ValueError("""Function must include at least first_name,
                             last_name, and state.""")

        args = {'first_name': first_name,
                'last_name': last_name,
                'state': state,
                'street_number': street_number,
                'street_name': street_name,
                'city': city,
                'zip_code': zip_code,
                'age': age,
                'dob': dob,
                'phone': phone,
                'email': email,
                'max_results': max_results
                }

        return Table(
            self.connection.request(url, args=args, raw=True)["potential_voter_matches"]
        )


class TargetSmartAPI(Voter, Person, Service):

    def __init__(self, api_key=None):
        self.connection = TargetSmartConnector(api_key=api_key)
