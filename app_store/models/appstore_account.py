# -*- coding: utf-8 -*
import logging
_logger = logging.getLogger(__name__)
import io
import zipfile
import tempfile
import urllib
import os

from openerp import api, fields, models

class AppstoreAccount(models.Model):

    _name = "appstore.account"
    _description = "App Store Account"
    
    name = fields.Char(string="Name")
    repositories_ids = fields.One2many('appstore.account.repository', 'asa_id', string="Repositories")

class AppstoreAccountRepository(models.Model):

    _name = "appstore.account.repository"
    _description = "App Store Account Repository"
    
    asa_id = fields.Many2one('appstore.account', string="App Store Account")
    url = fields.Char(string="Repository URL")
    
    @api.model
    def check_all_repositories(self):
        """Checks to see if there are any new modules"""
        #https://github.com/SythilTech/Odoo9#9.0
        #https://github.com/SythilTech/Odoo9/archive/9.0.zip        
        
        filename = tempfile.mktemp('.zip')
        destDir = tempfile.mktemp()
        home_directory = os.path.expanduser('~')
        app_directory = home_directory + "/apps"
        
        for account_repository in self.env['appstore.account.repository'].search([]):
            rep_directory = app_directory + "/" +  account_repository.url.split("/")[3]

            repository_url = account_repository.url.split("#")[0] + "/archive/" + account_repository.url.split("#")[1] + ".zip"
            name, hdrs = urllib.urlretrieve(repository_url, filename)
            thefile = zipfile.ZipFile(filename)

            if not os.path.exists(rep_directory):
                os.makedirs(rep_directory)

            thefile.extractall(rep_directory)
                        
            thefile.close()
            
            rep_name = account_repository.url.split("/")[4].replace("#","-")
            
            full_rep_path = rep_directory + "/" + rep_name
            _logger.error(full_rep_path)
        
            #Go through all module folders under the repository directory and analyse the module
            for dir in os.listdir(full_rep_path):
                if os.path.isdir(os.path.join(full_rep_path, dir)):
                    self.env['module.overview.wizard'].create({'name':'temp wizard'}).analyse_module(dir, full_rep_path)