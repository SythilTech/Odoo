Menus
=====
Migrate
-------
Child of "Settings" menu, parent menu of all other image import menus

Import Partner Images
---------------------
Child of "Migrate" menu, place to mass import partner images

Import History
--------------
Child of "Migrate" menu, stores a history of all imports including which images failed to import

Models / Fields
===============
crm.migrate.image.wizard (Wizard to mass import partner images)
---------------------------------------------------------------
Fields
^^^^^^
**Zip File Path (zip_path)**: The location of the zip file which contains all the images files

**Mapping Field (map_field)**: The field that matches the filename

crm.migrate.image (An instance of a import)
-------------------------------------------
Fields
^^^^^^
**Mapping Field (map_field)**: The field that matched the file name during the import

**Filename (filename)**: The file path of the zip file with all the images

**Imported Images (import_history)**: List of the images imported

import.image.history (History of the images imported)
-----------------------------------------------------
Fields
^^^^^^
**Migrate ID (migrate_image_id)**: The ID of the migrate attempt

**Filename (filename)**: The file name of the image file

**State (state)**: Success or failure if the image imported

**Note (note)**: Information on why the import failed