import re
from datetime import datetime


class SmartEventParser:
    """Parser for natural language (German)"""

    MONTHS_DE = {
        'januar': 1, 'jan': 1,
        'februar': 2,'feb': 2,
        'märz': 3, 'maerz': 3, 'mär': 3,
        'april': 4, 'apr': 4,
        'mai': 5,
        'juni': 6, 'jun': 6,
        'juli': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'oktober': 10, 'okt': 10,
        'november': 11, 'nov': 11,
        'dezember': 12, 'dez': 12,
    }

    def __init__(self) -> None:
        self.events= []
        self.current_year = datetime.now().year

    def parse_smart_text(self, text):
        """Main method for parsing a natural language"""

        self.events = []
        lines = text.split('\n')
        full_text = ' '.join(lines)

        # 1. Search by date range (multi-day)
        self._extract_date_range(full_text)

        # 2. Search by single date 
        #self._extract_single_date(full_text)

        # 3. Extract common information
        #common_info = self._extract_common_info(full_text)

        # 4. Apply common information to all events

        return self.events

    def _extract_date_range(self, full_text):
        text_lower = full_text.lower()
        months = '|'.join(self.MONTHS_DE.keys())

        # --- „vom DD. bis DD. Monat [Jahr]" ---
        pattern1 = (
            r'vom\s+(\d{1,2})\.\s*bis\s+'
            r'(\d{1,2})\.\s+'
            r'(' + months + r')'
            r'(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern1, text_lower):
            start_date, end_date, month_str, year_str=match.groups()
            month= self._month_to_number(month_str)
            year = int(year_str) if year_str else self.current_year
            self.events.append({
                'start_date': datetime(year, month, int(start_date)),
                'end_date': datetime(year, month, int(end_date)),
                'raw': match.group(0),
            })

        # --- „beginnt am DD. Monat [Jahr] und endet am DD. Monat [Jahr]" ---
        pattern2 = (
            r'.*?beginnt am\s+(\d{1,2})\.?\s*(' + months + r')(?:\s+(\d{4}))?\s*'
            r'und endet am\s+(\d{1,2})\.?\s*(' + months + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern2, text_lower, re.DOTALL):
            start_day, start_month_str, start_year, end_day, end_month_str, end_year = match.groups()
            
            start_date = datetime(
                int(start_year) if start_year else self.current_year,
                self._month_to_number(start_month_str),
                int(start_day))
            end_date = datetime(
                int(end_year) if end_year else self.current_year, 
                self._month_to_number(end_month_str), 
                int(end_day))
            
            self.events.append({
                'start_date': start_date,
                'end_date': end_date,
                'raw': match.group(0),
            })


    def _extract_single_date(self, full_text):
        text_lower = full_text.lower()
        months = '|'.join(self.MONTHS_DE.keys())
        pass

    def _create_date_range_event(self):
        
        pass

    def _create_single_event(self):
        
        pass

    def _extract_time_range(self):
        
        pass

    def _extract_tilte(self):
        pass

    def _extract_common_info(self, text):
        info= {
            'location': '',
            'trainer': '',
            'description': ''
        }
        pass

    def _month_to_number(self, month_name):
        month_name = month_name.lower().strip('.').strip()

        if month_name.isdigit():
            return int(month_name)
        
        if month_name in self.MONTHS_DE:
            return self.MONTHS_DE[month_name]
        
        return datetime.now().month
    

def parse_smart_text_to_event(text):
    pass

