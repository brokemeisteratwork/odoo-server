
import os, shutil, subprocess


#Put this file in the directory, where you wish to copy all the module to.
#you can overwrite module => order in filelist is important
#------ example file
## your comment
#addons:path/to/addons/ -> register module from this addons-path (will not copy addons)
#module:your_module_name -> copy module, if it's registered,
#folder containing modules ../my-external-folder/repository/*
#folder as one single module  ../my-module-external-module/
#----

###################### CONFIGURATION ######################

# file fore loading modules
filelist = "_externals"
# location where all repositories are location (recommaned sibiling folder to your odoo project)
base_path = '../../odoo-externals/'
# locations with modules which should be ignored bei default, e.g. ignore default addons from odoo
ignore_addons_path = ['../addons_odoo/', '../odoo/openerp/addons/']
# arguments for the rsync
arguments = ["-rtudv"]

############### DON'T CHANGE ANYTHING BELOW ###############
MANIFEST = '__openerp__.py'

### DON'T CHANGE ANYTHING BELOW

#externel folder
print "###########################################################"
print "###########################################################"
print "###########################################################"
print ""
print "###########################################################"
print "###################### CONFIGURATION ######################"
print "###########################################################"
print ""
print "FILELIST: %s" % filelist
print "BASE PATH: %s" % os.path.abspath(base_path)
print "IGNORE MODULES FROM THIS ADDON-PATHES: %s" % ignore_addons_path
print "RSYNC Parameters: %s" % os.path.abspath(base_path)
print ""
print "###########################################################"
print "######################### RUNNING #########################"
print "###########################################################"
print ""

# list of existing folders
modules_found = {}
modules_available = {}
modules_depends = {}
modules_loaded = {}
modules_ignore = {}
errors = []

def shall_ignore_module(module):
    if module in modules_ignore:
        return True
    for path in ignore_addons_path:
        if os.path.isdir(os.path.join(path, module)):
            return True

    return False


def rsync_folder(module, source_path):
    target_path = module+'/'
    if not os.path.isfile(os.path.join(source_path, '__init__.py')):
        print "    no module in folder "+source_path
        return
    if shall_ignore_module(module):
        print "    IGNORE module '"+module+"' in folder "+source_path
        return

    modules_found[module] = True
    modules_loaded[module] = True

    folder_arguments = list(arguments)
    folder_arguments.append(source_path)
    folder_arguments.append(target_path)
    print "    rsync "+str(folder_arguments)
    return_code = subprocess.call(["rsync"] + folder_arguments)
    if return_code == 0:
        print "    SUCCESFUL "+module
    else:
        errors.append('RSYNC FAILED: Module %s' % module)
        print "    FAILED "+module

    if module in modules_depends and len(modules_depends[module]) > 0:
        print "  LOADING DEPENDENCIES for  " + module
        for submodule in modules_depends[module]:
            load_module(submodule)

def rsync_addons(addons_folder):
    for folder in os.listdir(os.path.join(base_path, addons_folder)):
        source_path = addons_folder+folder+'/'
        if not os.path.isdir(os.path.join(base_path, source_path)):
            # no module so we continue
            continue

        rsync_folder(folder, os.path.join(base_path, source_path))

# modified copy of Odoo.
def load_information_from_description_file(module, mod_path):
    """
    :param module: The name of the module (sale, purchase, ...)
    :param mod_path: Physical path of module, if not providedThe name of the module (sale, purchase, ...)
    """

    terp_file = mod_path and os.path.join(mod_path, MANIFEST) or False
    if terp_file:
        info = {}
        if os.path.isfile(terp_file):
            # default values for descriptor
            info = {
                'depends': [],
                'installable': True,
            }

            f = open(terp_file)
            try:
                info.update(eval(f.read()))
            finally:
                f.close()

            return info

    return {}


def register_modules(path):
    ignore = False
    if path.startswith('!'):
        path.replace('!','')
        ignore = True

    path_absolute = os.path.join(base_path, path)
    print ""
    print "  MODULE REGISTRATION: %s" % path_absolute
    if not os.path.isdir(path_absolute):
        print "    addons:%s not found." % path_absolute
        return

    for folder in os.listdir(path_absolute):
        module_path = os.path.join(path_absolute, folder)

        if not os.path.isdir(module_path):
            continue

        if not os.path.isfile(os.path.join(module_path, '__init__.py')) or not os.path.isfile(os.path.join(module_path, MANIFEST)):
            print "    WARNING:            %s not Odoo module found" % folder
            continue

        module_info = load_information_from_description_file(folder, module_path)

        if not module_info['installable']:
            print "    WARNING:            %s not installable" % folder
            continue

        if ignore:
            modules_ignore[folder] = True
        else:
            modules_available[folder] = module_path
            modules_depends[folder] = module_info['depends']


        print "    MODULE AVAILABLE:   %s" % folder

def load_module(module):
    #this is a module to ignore => do not sync or delete
    if module.startswith('!'):
        module = module.replace('!', '')
        modules_ignore[module] = True

    if module in modules_loaded:
        print "    INFO:   Module '%s' already loaded." % module
        return
    elif shall_ignore_module(module):
        print "    INFO:   Ignoring module '%s' while loading module." % module
        return
    elif not module in modules_available:
        errors.append('LOADING FAILED: Module %s' % module)
        print "    ERROR:   Module '%s' not found registered modules." % module
        return

    module_path = modules_available[module]+'/'
    rsync_folder(module, module_path)

################# action #################

for folder in os.listdir('.'):
    if os.path.isdir(folder):
        modules_found[folder] = False

for folder in os.listdir('.'):
    if os.path.isdir(folder):
        modules_found[folder] = False

with open(filelist, 'r') as fread:
    i = 0
    for line in fread:
        i += 1
        line = line.strip()
        if not line:
            print ''
            continue

        #this comment line
        if line.startswith('#'):
            print line
            continue

        print "\n"+str(i)+': '+line

        if line.startswith('addons:'):
            path = line.replace('addons:', '')
            register_modules(path)

        elif line.startswith('module:'):
            path = line.replace('module:', '')
            load_module(path)

        elif '*' in line:
            # this is folder with modules
            line = line.replace('*', '')
            line = line.rstrip('/')+'/'

            rsync_addons(line)
        else:
            module = os.path.basename(line.rstrip('/'))
            rsync_folder(module, os.path.join(base_path, line))

        print "\n-----------------------------------------------"

print "\n###############################################\n###############################################\n"
print "Checking folders to delete:"
deletion_found = False
for folder in modules_found:
    if not modules_found[folder] and not folder in modules_ignore:
        deletion_found = True
        print '- DELETING '+folder
        shutil.rmtree(folder)
if not deletion_found:
    print 'No Modules deleted.'
print "\n###############################################\n###############################################\n"
if len(errors):
    print "Following Errors occured:"
    for error in errors:
        print "- "+error
else:
    print "No Errors occured."
print "\n###############################################\n###############################################\n"
