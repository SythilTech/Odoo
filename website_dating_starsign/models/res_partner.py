# -*- coding: utf-8 -*-
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import math
import logging
_logger = logging.getLogger(__name__)
from random import randint

from openerp import api, fields, models

class ResPartnerWebsiteDatingStarSign(models.Model):

    _inherit = "res.partner"


    starsign = fields.Char(string="Star Sign", compute='_compute_starsign', store=True)

    @api.one
    @api.depends('birth_date')
    def _compute_starsign(self):
        if (self.birth_date):
            zodiac_sign = ""
            my_date = datetime.strptime(self.birth_date, "%Y-%m-%d").date()
            Month = my_date.month
            Day = my_date.day
            if ((int(Month)==12 and int(Day) >= 22)or(int(Month)==1 and int(Day)<= 19)):
	        zodiac_sign = "Capricorn"
            elif ((int(Month)==1 and int(Day) >= 20)or(int(Month)==2 and int(Day)<= 17)):
	        zodiac_sign = "Aquarium"
	    elif ((int(Month)==2 and int(Day) >= 18)or(int(Month)==3 and int(Day)<= 19)):
	        zodiac_sign = "Pices"
	    elif ((int(Month)==3 and int(Day) >= 20)or(int(Month)==4 and int(Day)<= 19)):
	        zodiac_sign = "Aries"
	    elif ((int(Month)==4 and int(Day) >= 20)or(int(Month)==5 and int(Day)<= 20)):
	        zodiac_sign = "Taurus"
	    elif ((int(Month)==5 and int(Day) >= 21)or(int(Month)==6 and int(Day)<= 20)):
	        zodiac_sign = "Gemini"
	    elif ((int(Month)==6 and int(Day) >= 21)or(int(Month)==7 and int(Day)<= 22)):
	        zodiac_sign = "Cancer"
	    elif ((int(Month)==7 and int(Day) >= 23)or(int(Month)==8 and int(Day)<= 22)): 
	        zodiac_sign = "Leo"
	    elif ((int(Month)==8 and int(Day) >= 23)or(int(Month)==9 and int(Day)<= 22)): 
	        zodiac_sign = "Virgo"
	    elif ((int(Month)==9 and int(Day) >= 23)or(int(Month)==10 and int(Day)<= 22)):
	        zodiac_sign = "Libra"
	    elif ((int(Month)==10 and int(Day) >= 23)or(int(Month)==11 and int(Day)<= 21)): 
	        zodiac_sign = "Scorpio"
	    elif ((int(Month)==11 and int(Day) >= 22)or(int(Month)==12 and int(Day)<= 21)):
	        zodiac_sign = "Sagittarius"
	        _logger.error(zodiac_sign)
            self.starsign = zodiac_sign
    
    def _dating_fake_action_starsigns(self, partner_dict):
        #partner_dict['starsign'] = "Leo"
        return partner_dict
        
    def _dating_match_action_starsigns(self, search_list):
        #Just an example, can't be bothered inputing a chart
        search_list.append(('starsign','!=', self.starsign))
        return search_list