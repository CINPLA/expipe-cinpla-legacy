#!/usr/bin/env python
from __future__ import print_function
import argparse
import sys
import exdir
import yaml
import os
import os.path
import click
try:
    from termcolor import colored, cprint
    has_colors = True
except ImportError:
    has_colors = False
    def colored(value, *args, **kwargs):
        return value
        
    def cprint(value, *args, **kwargs):
        print(value)
try:
    import colorama
    colorama.init()
except ImportError:
    pass
    

class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        
        aliases = {
            "ls": "list",
            "mkgrp": "create-group"
        }
        
        if cmd_name in aliases:
            return click.Group.get_command(self, ctx, aliases[cmd_name])
            
        return None
        

@click.group(cls=AliasedGroup)
def cli():
    pass


def verify_inside(name):
    try:
        exdir.core.assert_inside_exdir(name)
    except FileNotFoundError:
        print("ERROR:", os.path.abspath(name), "is not inside a exdir repository.")
        sys.exit(1)


@cli.command(name="list")
@click.argument("name", default=".", nargs=1, required=False)
@click.option("--color", "-c", default="auto")
def list_(name, color, **args):
    """
    List contents of an object.
    
    Lists contents of NAME.
    
    Note that coloring requires checking each object type, which is slow.
    Disabling colors by passing -c never makes this command run faster.
    """
    if color == "always":
        use_colors = True
    elif color == "auto":
        use_colors = has_colors
    else:
        use_colors = False
    
    verify_inside(name)
    try:
        obj = exdir.core.open_object(name)
    except KeyError:
        return 0
            
    if isinstance(obj, exdir.core.Group):
        if not use_colors:
            print("\n".join(obj.keys()))
            return 0
            
        for sub in obj.values():
            if isinstance(sub, exdir.core.Group):
                cprint(sub.object_name, "blue", attrs=["bold"])
            elif isinstance(sub, exdir.core.Raw):
                cprint(sub.object_name, "yellow", attrs=["bold"])
            else:
                print(sub.object_name)
                
        return 0
    elif isinstance(obj, exdir.core.Dataset):
        print(obj.object_name)
        return 0
    else:
        print("Cannot list object of this type:", obj)
        return 1


# NOTE the uppercase T is just to avoid conflicts with Python's builtin object
@cli.command()
@click.argument("name", required=False, default=".", nargs=1)
def info(name):
    """
    Give information about an object.
    
    This command gives different output depending on the type of object.
    Groups are shown with the name and number of items,
    datasets with the name and shape,
    and raw directories show only the name.
    
    """    
    verify_inside(name)
    obj = exdir.core.open_object(name)
    if isinstance(obj, exdir.core.Group):
        if isinstance(obj, exdir.core.File):
            print("__root__")
            print("Type: File")
        else:
            print(obj.object_name)
            print("Type: Group")
        print("Name:", obj.name)
        item_count = len(list(obj.keys()))
        print("Item count:", item_count)
        return 0
    if isinstance(obj, exdir.core.Dataset):
        print(obj.object_name)
        print("Type: Dataset")
        print("Name:", obj.name)
        print("Shape:", obj.shape)
        return 0
    if isinstance(obj, exdir.core.Raw):
        print(obj.object_name)
        print("Type: Raw")
        print("Name:", obj.name)
        return 0


@cli.command()
@click.argument("name", default=".", nargs=1)
@click.option("--all", "-a", help="show all data in datasets")
def show(name, **args):
    """
    Show contents of an object.
    
    The contents of NAME is shown depending on the type.
    Files and groups show the number of items and lists these.
    Datasets show partial contents of the dataset unless --all is used,
    which shows entire dataset (this can be slow).
    """
    verify_inside(name)
    obj = exdir.core.open_object(name)
    
    if args.get("all"):
        import numpy as np
        np.set_printoptions(threshold=np.inf)        
    
    if isinstance(obj, exdir.core.Group):
        if isinstance(obj, exdir.core.File):
            print("__root__")
            print("Type: File")
        else:
            print(obj.object_name)
            print("Type: Group")
        print("Name:", obj.name)
        item_count = len(list(obj.keys()))
        print("Item count:", item_count)
        if item_count > 0:
            print("Items:")
            print(", ".join(obj.keys()))
        return 0
    if isinstance(obj, exdir.core.Dataset):
        print(obj.object_name)
        print("Type: Dataset")
        print("Name:", obj.name)
        print("Shape:", obj.shape)
        print("Data:")
        print(obj.data)
        return 0
    if isinstance(obj, exdir.core.Raw):
        print(obj.object_name)
        print("Type: Raw")
        print("Name:", obj.name)
        return 0


@cli.command(name="create-group")
@click.argument("name")
def create_group(name):
    """
    Create a new group.
    
    An empty group NAME is created.
    """
    verify_inside(name)
    obj = exdir.core.open_object(".")
    if not isinstance(obj, exdir.core.Group):
        print("ERROR: '{}' is not a group".format(name))
    try:
        obj.create_group(name)
    except OSError as e:
        print("ERROR: Cannot create group '{group}': {error}".format(group=name, error=e))
    

@cli.command()
@click.argument("name", default=".")
def name(name):
    """
    Print the full name of an object.
    
    The name of object with NAME is returned.
    """
    print(exdir.core.open_object(name).name)


@cli.command()
@click.argument("name")
def create(name):
    """
    Create new exdir directory.
    
    If NAME does not end with '.exdir', it will be appended.
    """
    if not name.endswith(".exdir"):
        name += ".exdir"
        
    if os.path.exists(name):
        print("Cannot create new Exdir directory. '{}' already exists.".format(name))
        return
    
    if exdir.core.is_inside_exdir(name):
        print("Cannot create new Exdir directory inside existing Exdir directory.")
        return
    
    exdir.File(name)
    print("Exdir directory '{}' successfully created.".format(name))
            

def main():
    cli()
    
if __name__ == "__main__":
    sys.exit(main())
