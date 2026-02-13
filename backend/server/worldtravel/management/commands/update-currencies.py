"""
Management command to update country currencies and exchange rates.
Uses RestCountries API for currency data and exchangerate.host for rates.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from worldtravel.models import Country, ExchangeRate
import requests
from decimal import Decimal


# Fallback currency data for countries (ISO 3166-1 alpha-2 -> currency info)
# This is used if the API is unavailable
COUNTRY_CURRENCIES = {
    'AD': ('EUR', 'Euro', '€'),
    'AE': ('AED', 'UAE Dirham', 'د.إ'),
    'AF': ('AFN', 'Afghan Afghani', '؋'),
    'AG': ('XCD', 'East Caribbean Dollar', '$'),
    'AI': ('XCD', 'East Caribbean Dollar', '$'),
    'AL': ('ALL', 'Albanian Lek', 'L'),
    'AM': ('AMD', 'Armenian Dram', '֏'),
    'AO': ('AOA', 'Angolan Kwanza', 'Kz'),
    'AR': ('ARS', 'Argentine Peso', '$'),
    'AS': ('USD', 'US Dollar', '$'),
    'AT': ('EUR', 'Euro', '€'),
    'AU': ('AUD', 'Australian Dollar', '$'),
    'AW': ('AWG', 'Aruban Florin', 'ƒ'),
    'AZ': ('AZN', 'Azerbaijani Manat', '₼'),
    'BA': ('BAM', 'Bosnia Mark', 'KM'),
    'BB': ('BBD', 'Barbadian Dollar', '$'),
    'BD': ('BDT', 'Bangladeshi Taka', '৳'),
    'BE': ('EUR', 'Euro', '€'),
    'BF': ('XOF', 'CFA Franc', 'Fr'),
    'BG': ('BGN', 'Bulgarian Lev', 'лв'),
    'BH': ('BHD', 'Bahraini Dinar', '.د.ب'),
    'BI': ('BIF', 'Burundian Franc', 'Fr'),
    'BJ': ('XOF', 'CFA Franc', 'Fr'),
    'BM': ('BMD', 'Bermudian Dollar', '$'),
    'BN': ('BND', 'Brunei Dollar', '$'),
    'BO': ('BOB', 'Bolivian Boliviano', 'Bs.'),
    'BR': ('BRL', 'Brazilian Real', 'R$'),
    'BS': ('BSD', 'Bahamian Dollar', '$'),
    'BT': ('BTN', 'Bhutanese Ngultrum', 'Nu.'),
    'BW': ('BWP', 'Botswana Pula', 'P'),
    'BY': ('BYN', 'Belarusian Ruble', 'Br'),
    'BZ': ('BZD', 'Belize Dollar', '$'),
    'CA': ('CAD', 'Canadian Dollar', '$'),
    'CD': ('CDF', 'Congolese Franc', 'Fr'),
    'CF': ('XAF', 'Central African CFA Franc', 'Fr'),
    'CG': ('XAF', 'Central African CFA Franc', 'Fr'),
    'CH': ('CHF', 'Swiss Franc', 'Fr'),
    'CI': ('XOF', 'CFA Franc', 'Fr'),
    'CL': ('CLP', 'Chilean Peso', '$'),
    'CM': ('XAF', 'Central African CFA Franc', 'Fr'),
    'CN': ('CNY', 'Chinese Yuan', '¥'),
    'CO': ('COP', 'Colombian Peso', '$'),
    'CR': ('CRC', 'Costa Rican Colón', '₡'),
    'CU': ('CUP', 'Cuban Peso', '$'),
    'CV': ('CVE', 'Cape Verdean Escudo', '$'),
    'CY': ('EUR', 'Euro', '€'),
    'CZ': ('CZK', 'Czech Koruna', 'Kč'),
    'DE': ('EUR', 'Euro', '€'),
    'DJ': ('DJF', 'Djiboutian Franc', 'Fr'),
    'DK': ('DKK', 'Danish Krone', 'kr'),
    'DM': ('XCD', 'East Caribbean Dollar', '$'),
    'DO': ('DOP', 'Dominican Peso', '$'),
    'DZ': ('DZD', 'Algerian Dinar', 'د.ج'),
    'EC': ('USD', 'US Dollar', '$'),
    'EE': ('EUR', 'Euro', '€'),
    'EG': ('EGP', 'Egyptian Pound', '£'),
    'ER': ('ERN', 'Eritrean Nakfa', 'Nfk'),
    'ES': ('EUR', 'Euro', '€'),
    'ET': ('ETB', 'Ethiopian Birr', 'Br'),
    'FI': ('EUR', 'Euro', '€'),
    'FJ': ('FJD', 'Fijian Dollar', '$'),
    'FK': ('FKP', 'Falkland Islands Pound', '£'),
    'FM': ('USD', 'US Dollar', '$'),
    'FO': ('DKK', 'Danish Krone', 'kr'),
    'FR': ('EUR', 'Euro', '€'),
    'GA': ('XAF', 'Central African CFA Franc', 'Fr'),
    'GB': ('GBP', 'British Pound', '£'),
    'GD': ('XCD', 'East Caribbean Dollar', '$'),
    'GE': ('GEL', 'Georgian Lari', '₾'),
    'GH': ('GHS', 'Ghanaian Cedi', '₵'),
    'GI': ('GIP', 'Gibraltar Pound', '£'),
    'GL': ('DKK', 'Danish Krone', 'kr'),
    'GM': ('GMD', 'Gambian Dalasi', 'D'),
    'GN': ('GNF', 'Guinean Franc', 'Fr'),
    'GQ': ('XAF', 'Central African CFA Franc', 'Fr'),
    'GR': ('EUR', 'Euro', '€'),
    'GT': ('GTQ', 'Guatemalan Quetzal', 'Q'),
    'GU': ('USD', 'US Dollar', '$'),
    'GW': ('XOF', 'CFA Franc', 'Fr'),
    'GY': ('GYD', 'Guyanese Dollar', '$'),
    'HK': ('HKD', 'Hong Kong Dollar', '$'),
    'HN': ('HNL', 'Honduran Lempira', 'L'),
    'HR': ('EUR', 'Euro', '€'),
    'HT': ('HTG', 'Haitian Gourde', 'G'),
    'HU': ('HUF', 'Hungarian Forint', 'Ft'),
    'ID': ('IDR', 'Indonesian Rupiah', 'Rp'),
    'IE': ('EUR', 'Euro', '€'),
    'IL': ('ILS', 'Israeli New Shekel', '₪'),
    'IN': ('INR', 'Indian Rupee', '₹'),
    'IQ': ('IQD', 'Iraqi Dinar', 'ع.د'),
    'IR': ('IRR', 'Iranian Rial', '﷼'),
    'IS': ('ISK', 'Icelandic Króna', 'kr'),
    'IT': ('EUR', 'Euro', '€'),
    'JM': ('JMD', 'Jamaican Dollar', '$'),
    'JO': ('JOD', 'Jordanian Dinar', 'د.ا'),
    'JP': ('JPY', 'Japanese Yen', '¥'),
    'KE': ('KES', 'Kenyan Shilling', 'Sh'),
    'KG': ('KGS', 'Kyrgyz Som', 'с'),
    'KH': ('KHR', 'Cambodian Riel', '៛'),
    'KI': ('AUD', 'Australian Dollar', '$'),
    'KM': ('KMF', 'Comorian Franc', 'Fr'),
    'KN': ('XCD', 'East Caribbean Dollar', '$'),
    'KP': ('KPW', 'North Korean Won', '₩'),
    'KR': ('KRW', 'South Korean Won', '₩'),
    'KW': ('KWD', 'Kuwaiti Dinar', 'د.ك'),
    'KY': ('KYD', 'Cayman Islands Dollar', '$'),
    'KZ': ('KZT', 'Kazakhstani Tenge', '₸'),
    'LA': ('LAK', 'Lao Kip', '₭'),
    'LB': ('LBP', 'Lebanese Pound', 'ل.ل'),
    'LC': ('XCD', 'East Caribbean Dollar', '$'),
    'LI': ('CHF', 'Swiss Franc', 'Fr'),
    'LK': ('LKR', 'Sri Lankan Rupee', 'Rs'),
    'LR': ('LRD', 'Liberian Dollar', '$'),
    'LS': ('LSL', 'Lesotho Loti', 'L'),
    'LT': ('EUR', 'Euro', '€'),
    'LU': ('EUR', 'Euro', '€'),
    'LV': ('EUR', 'Euro', '€'),
    'LY': ('LYD', 'Libyan Dinar', 'ل.د'),
    'MA': ('MAD', 'Moroccan Dirham', 'د.م.'),
    'MC': ('EUR', 'Euro', '€'),
    'MD': ('MDL', 'Moldovan Leu', 'L'),
    'ME': ('EUR', 'Euro', '€'),
    'MG': ('MGA', 'Malagasy Ariary', 'Ar'),
    'MH': ('USD', 'US Dollar', '$'),
    'MK': ('MKD', 'Macedonian Denar', 'ден'),
    'ML': ('XOF', 'CFA Franc', 'Fr'),
    'MM': ('MMK', 'Burmese Kyat', 'Ks'),
    'MN': ('MNT', 'Mongolian Tögrög', '₮'),
    'MO': ('MOP', 'Macanese Pataca', 'P'),
    'MP': ('USD', 'US Dollar', '$'),
    'MR': ('MRU', 'Mauritanian Ouguiya', 'UM'),
    'MS': ('XCD', 'East Caribbean Dollar', '$'),
    'MT': ('EUR', 'Euro', '€'),
    'MU': ('MUR', 'Mauritian Rupee', '₨'),
    'MV': ('MVR', 'Maldivian Rufiyaa', 'ރ'),
    'MW': ('MWK', 'Malawian Kwacha', 'MK'),
    'MX': ('MXN', 'Mexican Peso', '$'),
    'MY': ('MYR', 'Malaysian Ringgit', 'RM'),
    'MZ': ('MZN', 'Mozambican Metical', 'MT'),
    'NA': ('NAD', 'Namibian Dollar', '$'),
    'NC': ('XPF', 'CFP Franc', '₣'),
    'NE': ('XOF', 'CFA Franc', 'Fr'),
    'NG': ('NGN', 'Nigerian Naira', '₦'),
    'NI': ('NIO', 'Nicaraguan Córdoba', 'C$'),
    'NL': ('EUR', 'Euro', '€'),
    'NO': ('NOK', 'Norwegian Krone', 'kr'),
    'NP': ('NPR', 'Nepalese Rupee', '₨'),
    'NR': ('AUD', 'Australian Dollar', '$'),
    'NZ': ('NZD', 'New Zealand Dollar', '$'),
    'OM': ('OMR', 'Omani Rial', 'ر.ع.'),
    'PA': ('PAB', 'Panamanian Balboa', 'B/.'),
    'PE': ('PEN', 'Peruvian Sol', 'S/'),
    'PF': ('XPF', 'CFP Franc', '₣'),
    'PG': ('PGK', 'Papua New Guinean Kina', 'K'),
    'PH': ('PHP', 'Philippine Peso', '₱'),
    'PK': ('PKR', 'Pakistani Rupee', '₨'),
    'PL': ('PLN', 'Polish Złoty', 'zł'),
    'PM': ('EUR', 'Euro', '€'),
    'PR': ('USD', 'US Dollar', '$'),
    'PS': ('ILS', 'Israeli New Shekel', '₪'),
    'PT': ('EUR', 'Euro', '€'),
    'PW': ('USD', 'US Dollar', '$'),
    'PY': ('PYG', 'Paraguayan Guaraní', '₲'),
    'QA': ('QAR', 'Qatari Riyal', 'ر.ق'),
    'RO': ('RON', 'Romanian Leu', 'lei'),
    'RS': ('RSD', 'Serbian Dinar', 'дин.'),
    'RU': ('RUB', 'Russian Ruble', '₽'),
    'RW': ('RWF', 'Rwandan Franc', 'Fr'),
    'SA': ('SAR', 'Saudi Riyal', 'ر.س'),
    'SB': ('SBD', 'Solomon Islands Dollar', '$'),
    'SC': ('SCR', 'Seychellois Rupee', '₨'),
    'SD': ('SDG', 'Sudanese Pound', 'ج.س.'),
    'SE': ('SEK', 'Swedish Krona', 'kr'),
    'SG': ('SGD', 'Singapore Dollar', '$'),
    'SH': ('SHP', 'Saint Helena Pound', '£'),
    'SI': ('EUR', 'Euro', '€'),
    'SK': ('EUR', 'Euro', '€'),
    'SL': ('SLE', 'Sierra Leonean Leone', 'Le'),
    'SM': ('EUR', 'Euro', '€'),
    'SN': ('XOF', 'CFA Franc', 'Fr'),
    'SO': ('SOS', 'Somali Shilling', 'Sh'),
    'SR': ('SRD', 'Surinamese Dollar', '$'),
    'SS': ('SSP', 'South Sudanese Pound', '£'),
    'ST': ('STN', 'São Tomé and Príncipe Dobra', 'Db'),
    'SV': ('USD', 'US Dollar', '$'),
    'SY': ('SYP', 'Syrian Pound', '£'),
    'SZ': ('SZL', 'Swazi Lilangeni', 'L'),
    'TC': ('USD', 'US Dollar', '$'),
    'TD': ('XAF', 'Central African CFA Franc', 'Fr'),
    'TG': ('XOF', 'CFA Franc', 'Fr'),
    'TH': ('THB', 'Thai Baht', '฿'),
    'TJ': ('TJS', 'Tajikistani Somoni', 'ЅМ'),
    'TL': ('USD', 'US Dollar', '$'),
    'TM': ('TMT', 'Turkmenistan Manat', 'm'),
    'TN': ('TND', 'Tunisian Dinar', 'د.ت'),
    'TO': ('TOP', 'Tongan Paʻanga', 'T$'),
    'TR': ('TRY', 'Turkish Lira', '₺'),
    'TT': ('TTD', 'Trinidad and Tobago Dollar', '$'),
    'TV': ('AUD', 'Australian Dollar', '$'),
    'TW': ('TWD', 'New Taiwan Dollar', 'NT$'),
    'TZ': ('TZS', 'Tanzanian Shilling', 'Sh'),
    'UA': ('UAH', 'Ukrainian Hryvnia', '₴'),
    'UG': ('UGX', 'Ugandan Shilling', 'Sh'),
    'US': ('USD', 'US Dollar', '$'),
    'UY': ('UYU', 'Uruguayan Peso', '$'),
    'UZ': ('UZS', 'Uzbekistani Som', 'сўм'),
    'VA': ('EUR', 'Euro', '€'),
    'VC': ('XCD', 'East Caribbean Dollar', '$'),
    'VE': ('VES', 'Venezuelan Bolívar', 'Bs.'),
    'VG': ('USD', 'US Dollar', '$'),
    'VI': ('USD', 'US Dollar', '$'),
    'VN': ('VND', 'Vietnamese Đồng', '₫'),
    'VU': ('VUV', 'Vanuatu Vatu', 'Vt'),
    'WF': ('XPF', 'CFP Franc', '₣'),
    'WS': ('WST', 'Samoan Tālā', 'T'),
    'XK': ('EUR', 'Euro', '€'),
    'YE': ('YER', 'Yemeni Rial', '﷼'),
    'ZA': ('ZAR', 'South African Rand', 'R'),
    'ZM': ('ZMW', 'Zambian Kwacha', 'ZK'),
    'ZW': ('ZWL', 'Zimbabwean Dollar', '$'),
}


class Command(BaseCommand):
    help = 'Updates country currencies and exchange rates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rates-only',
            action='store_true',
            help='Only update exchange rates, not country currencies'
        )
        parser.add_argument(
            '--currencies-only',
            action='store_true',
            help='Only update country currencies, not exchange rates'
        )

    def handle(self, **options):
        rates_only = options.get('rates_only', False)
        currencies_only = options.get('currencies_only', False)

        if not rates_only:
            self.update_country_currencies()

        if not currencies_only:
            self.update_exchange_rates()

        self.stdout.write(self.style.SUCCESS('Currency update complete!'))

    def update_country_currencies(self):
        """Update country currency fields using fallback data"""
        self.stdout.write('Updating country currencies...')

        updated = 0
        with transaction.atomic():
            for country in Country.objects.all():
                currency_info = COUNTRY_CURRENCIES.get(country.country_code.upper())
                if currency_info:
                    currency_code, currency_name, currency_symbol = currency_info
                    if (country.currency_code != currency_code or
                        country.currency_name != currency_name or
                        country.currency_symbol != currency_symbol):
                        country.currency_code = currency_code
                        country.currency_name = currency_name
                        country.currency_symbol = currency_symbol
                        country.save(update_fields=['currency_code', 'currency_name', 'currency_symbol'])
                        updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} countries with currency data'))

    def update_exchange_rates(self):
        """Update exchange rates from free API"""
        self.stdout.write('Fetching exchange rates...')

        # Try multiple free API sources
        rates = self._fetch_rates_from_api()

        if not rates:
            self.stdout.write(self.style.WARNING('Could not fetch rates from API, using fallback rates'))
            rates = self._get_fallback_rates()

        # Update database
        updated = 0
        created = 0
        with transaction.atomic():
            for currency_code, rate in rates.items():
                obj, was_created = ExchangeRate.objects.update_or_create(
                    currency_code=currency_code,
                    defaults={'rate': Decimal(str(rate))}
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Exchange rates: {created} created, {updated} updated'
        ))

    def _fetch_rates_from_api(self):
        """Try to fetch rates from free API sources"""
        # Try exchangerate.host (free, no API key)
        try:
            response = requests.get(
                'https://api.exchangerate.host/latest',
                params={'base': 'USD'},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('rates'):
                    self.stdout.write('Got rates from exchangerate.host')
                    return data['rates']
        except Exception as e:
            self.stdout.write(f'exchangerate.host failed: {e}')

        # Try frankfurter.app (free, no API key)
        try:
            response = requests.get(
                'https://api.frankfurter.app/latest',
                params={'from': 'USD'},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('rates'):
                    self.stdout.write('Got rates from frankfurter.app')
                    rates = data['rates']
                    rates['USD'] = 1.0  # Add USD as base
                    return rates
        except Exception as e:
            self.stdout.write(f'frankfurter.app failed: {e}')

        return None

    def _get_fallback_rates(self):
        """Return fallback rates if API is unavailable"""
        # These are approximate rates as of early 2024
        return {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'JPY': 149.50,
            'AUD': 1.53,
            'CAD': 1.35,
            'CHF': 0.88,
            'CNY': 7.24,
            'HKD': 7.82,
            'SGD': 1.34,
            'SEK': 10.42,
            'NOK': 10.65,
            'DKK': 6.88,
            'NZD': 1.64,
            'INR': 83.12,
            'MXN': 17.15,
            'BRL': 4.97,
            'ZAR': 18.63,
            'AED': 3.67,
            'TRY': 30.25,
            'KRW': 1328.50,
            'THB': 35.50,
            'PLN': 4.02,
            'PHP': 56.20,
            'IDR': 15650.00,
            'MYR': 4.72,
            'VND': 24500.00,
            'CZK': 23.15,
            'HUF': 356.00,
            'ILS': 3.65,
            'CLP': 935.00,
            'COP': 3950.00,
            'PEN': 3.72,
            'ARS': 825.00,
            'EGP': 30.90,
            'PKR': 278.50,
            'NGN': 900.00,
            'BDT': 110.00,
            'UAH': 37.50,
            'RON': 4.58,
            'RUB': 90.00,
            'SAR': 3.75,
            'QAR': 3.64,
            'KWD': 0.31,
            'BHD': 0.377,
            'OMR': 0.385,
        }
