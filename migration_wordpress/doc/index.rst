Configuration
1. Go Settings->Users & Companies->Users
2. Select a user you want to give permission to import Wordpress websites
3. Tick the "Wordpress Migration Manager" tickbox
4. Save the record and the new "Migration" top level menu should appear

Import Entire Media Library
1. Go to Migration top level menu
2. Create a new record and enter the URL of your Wordpress website (no credentials needed)
3. Hit "Import Media", this will download all images into the Odoo media library
*NOTE* Only the orginal image size is transferred

Import Website pages
1. Go to Migration top level menu
2. Create a new record and enter the URL of your Wordpress website (no credentials needed)
3. Hit "Import Pages", this will copy the raw content of the page, transforming any image / link URLs in the process.
*NOTE* Due to theme styles and javascript not being transferred over, most pages will NOT retain thier original appearance.
In most cases a redesign will be neccassary however this module still saves time having to manually transfer resources.