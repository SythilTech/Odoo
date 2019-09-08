def migrate(cr, version):
    cr.execute('SELECT can, not, upgrade FROM version')