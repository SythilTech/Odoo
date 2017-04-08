Menus
=====
Migration
---------
Child of "Settings" menu, parent menu of all other ERD Maker menus

Create ERD
----------
Child of "Migration" menu, place to create Entity Relationship Diagrams

Create ERD (Module)
-------------------
Child of "Migration" menu, create Entity Relationship Diagrams of a module

Models / Fields
===============
erd.maker (Wizard to create an ERD)
-----------------------------------
Fields
^^^^^^
**Select Model (my_model)**: The model which the ERD is based on

**Transverse Depth (transverse_depth)**: Database relation depth to tranverse

**Omit Builtin Fields (omit_builtin_fields)**: Do not include Odoo built in database fields

**Output HTML (output_text)**: A HTML version of the ERD

**Output Image (output_image)**: Not used, was designed to output image

**Current Transverse (current_transverse)**: Internal use only, should have been a python variable...

erd.maker.module (Wizard to create an ERD of a module)
------------------------------------------------------
Fields
^^^^^^
**Select Module (my_module)**: The module which the ERD is based on

**Omit Builtin Fields (omit_builtin_fields)**: Do not include Odoo built in database fields

**Output HTML (output_text)**: A HTML version of the ERD